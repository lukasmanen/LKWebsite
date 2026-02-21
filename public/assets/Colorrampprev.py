import nuke
from PySide6.QtWidgets import QPushButton, QVBoxLayout, QHBoxLayout, QWidget,QLabel, QComboBox
from PySide6.QtGui import (QPainter, QLinearGradient, QColor, QBrush, QPen,)
from PySide6.QtCore import QPointF, QRectF, Qt

class GradientWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 150)
        self.node = nuke.thisNode()
        self.knob_name = "gradient_pos"  # Target knob to update
        self._stops = [[0.0, QColor(0,0,0)], [1.0, QColor(255,255,255)]]
        self._selected = -1
        self._dragging = False
        self.setMouseTracking(True)
        
        # 1. Main Horizontal Layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 5, 5)
        
        
        
        top_layout = QVBoxLayout()
        top_layout.setSpacing(2)

        top_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        top_layout.addWidget(QLabel("Interpolation:"))
        self.interp_box = QComboBox()
        self.interp_box.addItems(["Linear", "Ease In/Out", "Hold"])
        self.interp_box.setFixedWidth(120)
        self.interp_box.currentIndexChanged.connect(self.update)
        top_layout.addWidget(self.interp_box)
        
        main_layout.addLayout(top_layout)

        # 2. Add an empty stretch to push the button column to the right edge
        main_layout.addStretch()

        # 3. Vertical layout specifically for the +/- buttons
        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_col.setAlignment(Qt.AlignVCenter)
        
        self.add_btn = QPushButton("+", self)
        self.add_btn.setFixedSize(20, 20)
        self.add_btn.clicked.connect(self.add_stop)
        
        self.remove_btn = QPushButton("-", self)
        self.remove_btn.setFixedSize(20, 20)
        self.remove_btn.clicked.connect(self.remove_stop)
        
        btn_col.addWidget(self.add_btn)
        btn_col.addWidget(self.remove_btn)
        
        main_layout.addLayout(btn_col)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # active_w reduces the paintable area by 40px to leave room for the buttons
        active_w = self.width() - 40
        bar = QRectF(10, 60, active_w - 10, 24)
        
        # GRADIENT BAR
        grad = QLinearGradient(bar.left(), 0, bar.right(), 0)
        for pos, color in self._stops:
            grad.setColorAt(pos, color)
        p.fillRect(bar, QBrush(grad))
        p.setPen(QColor(60,60,60))
        p.drawRect(bar)
        
        # STOPS WITH WHITE OUTLINE
        STOP_W, STOP_H = 12.0, 12.0
        
        for i, (pos, color) in enumerate(self._stops):
            x = 10 + pos * (active_w - 10)
            points = [
                QPointF(x, bar.top()),
                QPointF(x - STOP_W/2, bar.top() - STOP_H),
                QPointF(x + STOP_W/2, bar.top() - STOP_H)
            ]
            
            # WHITE OUTLINE
            p.setPen(QPen(QColor(255,255,255), 1.8))
            p.setBrush(Qt.transparent)
            p.drawPolygon(points)
            
            # FILL (ORANGE IF SELECTED)
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#ff9900") if i == self._selected else color)
            p.drawPolygon(points)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            hit, idx = self._check_hit(event.position().x())
            if hit:
                self._selected = idx
                self._dragging = True
                self.update()

    def mouseMoveEvent(self, event):
        if self._dragging and self._selected >= 0:
            active_w = self.width() - 40
            # Convert x position to 0.0-1.0 range based on active area
            new_pos = max(0.0, min(1.0, (event.position().x() - 10) / (active_w - 10)))
            self._stops[self._selected][0] = new_pos
            self.update()  # REPAINT DURING DRAG

    def mouseReleaseEvent(self, event):
        self._dragging = False
        self._update_knobs()  # FINAL UPDATE

    def _check_hit(self, x):
        self._selected = -1
        active_w = self.width() - 40
        for i, (pos, _) in enumerate(self._stops):
            cx = 10 + pos * (active_w - 10)
            if abs(x - cx) < 6:
                self._selected = i
                return True, i
        return False, -1

    def add_stop(self):
        if len(self._stops) < 32:
            self._stops.append([0.5, QColor(128,128,128)])  # Add at middle with gray color
            self.update()
            self._update_knobs()
            
    def remove_stop(self):
        if self._selected >= 0 and len(self._stops) > 2:
            del self._stops[self._selected]
            self._selected = -1
            self.update()
            self._update_knobs()

    def _update_knobs(self):
        """UPDATE NODE KNOBS IN REAL TIME"""
        try:
            # Create/update position array knob (32 slots)
            if self.knob_name not in self.node.knobs():
                pos_knob = nuke.Double_Knob(self.knob_name, "Gradient Pos")
                pos_knob.setArray(True)
                self.node.addKnob(pos_knob)
            
            # Pack stops into 32-slot array
            positions = [0.0] * 32
            for i, (pos, _) in enumerate(self._stops):
                if i < 32:
                    positions[i] = pos
            
            self.node[self.knob_name].setValue(positions)
            nuke.updateUI()  # Force UI refresh
            
        except:
            pass 


# WRAPPER + INSTALL
class GradientKnobWrapper(object):
    def makeUI(self):
        return GradientWidget()

nuke.GradientKnobWrapper = GradientKnobWrapper

try:
    node = nuke.selectedNode()
    if not node:
        nuke.message("Select node first!")
    else:
        if "ramp" in node.knobs():
            node.removeKnob(node["ramp"])
        
        knob = nuke.PyCustom_Knob("ramp", "", "nuke.GradientKnobWrapper()")
        node.addKnob(knob)
        
        # Auto-create target knob
        if "gradient_pos" not in node.knobs():
            pos_knob = nuke.Double_Knob("gradient_pos", "Gradient Pos")
            pos_knob.setArray(True)
            node.addKnob(pos_knob)
    
        print(f" REAL TIME ramp on {node.name()}")
        node.showControlPanel()
        
except:
    nuke.message("Error!")
