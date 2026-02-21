---
layout: ../../../layouts/PostLayout.astro
title: "Shell Emitter"
date: "2026-03-16"
tags: ["Nuke","Physics", "Expressions","Python"]
summary: "A procedural shell ejection system using projectile motion physics in Nuke."
category: ""
image: /assets/ShellEjector/ShellEjectorThumbnail.jpg
---


## Overview


A Nuke Group Node that simulates shell casings ejecting from a chamber. Each shell
follows a arc driven by simple physics. No particle system needed,
just transformation math evaluated frame by frame.


> Built this for a muzzle flash comp where I needed shells to fly out.
> I remembered my first physics class where we had to calculate a ball's trajectory.
> Turns out it came handy for this assignment making the work less repetitive.


---
## Result Preview
<video autoplay muted loop playsinline style="width:100%; margin:2rem 0; border:1px solid #1f1f1f;">
  <source src="/assets/ShellEjector/ShellEjector.mp4" type="video/mp4"/>
</video>

## Shell Trajectroy Preview
<div style="position:relative; aspect-ratio:16/9; margin:2rem 0;">
  <iframe
    src="/assets/ShellEjector/ShellejectExpressions.mp4"
    title="Shell Ejector"
    frameborder="0"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen
    style="position:absolute; inset:0; width:100%; height:100%; border:1px solid #1f1f1f;">
  </iframe>
</div>



---
## The Physics


### Projectile motion


Each shell is an independent projectile. The Transform node moves it every frame
based on how much time has passed since it spawned. If a shell spawns at frame 50
and we are at frame 65, then `t = 15` frames have elapsed.


$$
x(t) = x_0 + v_x \cdot t
$$


$$
y(t) = y_0 + v_y \cdot t - \frac{1}{2} g t^2
$$


Where $x_0, y_0$ is the muzzle spawn position, $v_x$ is horizontal speed,
$v_y$ is the initial upward velocity, $g$ is gravity, and $t$ is frames since spawn.


### Breaking down the expression


The Y-position expression in the node looks like this:


```tcl
[expression parent.Chamber_pos.y(43)] - center.y
+ (parent.arc_height * (1 + (random(44) * parent.rand_arc)) * (frame - 43))
- (0.5 * parent.gravity * pow(frame - 43, 2))
```


Breaking it down:


1. `Chamber_pos.y(43)` reads the muzzle Y at the spawn frame
2. `- center.y` converts from absolute position to a relative offset
3. `arc_height * (frame - 43)` is the initial upward velocity over time
4. `(1 + random * rand_arc)` adds per-shell variation to the arc
5. `- 0.5 * gravity * pow(frame - 43, 2)` is the gravity term pulling it down


The X formula is simpler, just constant velocity with a random speed offset:


```tcl
[expression parent.Chamber_pos.x(43)] - center.x
+ ((frame - 43) * parent.side_speed * (1 + (random(43) * parent.rand_speed)))
```


---


## Implementation


### Multiple shells


Six shells spawn at different frames: `43, 50, 58, 63, 70, 75`. Each has its own
Transform node with identical expressions but a different hardcoded spawn frame.
They all get merged together at the end.


### Visibility


Each Merge node has a mix expression that keeps the shell invisible outside its
lifetime window:


```tcl
frame >= 43 && frame <= 43 + parent.life_span ? 1 : 0
```


### Randomness


`random()` in Nuke is seeded by its argument, so passing different values per
shell gives each one unique but stable variation. Same seed always returns the
same value, so the motion is repeatable across renders.


---


## Parameters


| Parameter        | Description                                             |
|------------------|---------------------------------------------------------|
| Chamber Position | Animated XY tracking where shells spawn                 |
| Base Height      | Initial upward velocity, higher arcs more               |
| Gravity          | Downward pull over time                                 |
| Forward Speed    | Horizontal ejection speed, negative ejects left         |
| Arc Randomness   | Per-shell variation in vertical velocity                |
| Speed Randomness | Per-shell variation in horizontal velocity              |
| Base Spin Speed  | Rotation speed in degrees per frame                     |
| Scale            | Shell size multiplier                                   |
| Life Span        | How many frames each shell stays visible                |


---


## Python Code


```python

def shell_emitter():
    spawn_frames =[43, 50, 58, 63, 70, 75]

    group = nuke.nodes.Group(name="Shell_Emitter")
    group.setXYpos(100, 50)

    with group:
        group.addKnob(nuke.Tab_Knob("ShellPhysics", "Shell Physics"))
        group.addKnob(nuke.XY_Knob("Chamber_pos", "Chamber Position"))
        group.addKnob(nuke.Text_Knob("arc_settings", "", "<b>Arc Settings</b>"))

        arc_height = nuke.Double_Knob("arc_height", "Base Height")
        arc_height.setRange(0, 100)
        arc_height.setValue(25.5)
        group.addKnob(arc_height)

        gravity = nuke.Double_Knob("gravity", "Gravity")
        gravity.setRange(0, 10)
        gravity.setValue(9.2)
        group.addKnob(gravity)

        side_speed = nuke.Double_Knob("side_speed", "Forward Speed")
        side_speed.setRange(-100, 100)
        side_speed.setValue(-55)
        group.addKnob(side_speed)

        group.addKnob(nuke.Text_Knob("randomness", "", "<b>Randomness</b>"))

        rand_arc = nuke.Double_Knob("rand_arc", "Arc Randomness")
        rand_arc.setValue(0.175)
        group.addKnob(rand_arc)

        rand_speed = nuke.Double_Knob("rand_speed", "Speed Randomness")
        rand_speed.setValue(2)
        group.addKnob(rand_speed)

        group.addKnob(nuke.Text_Knob("visuals", "", "<b>Visuals</b>"))

        global_spin = nuke.Double_Knob("global_spin", "Base Spin Speed")
        global_spin.setRange(-100, 100)
        global_spin.setValue(84)
        group.addKnob(global_spin)

        global_scale = nuke.Double_Knob("global_scale", "Scale")
        global_scale.setRange(0, 2)
        global_scale.setValue(1)
        group.addKnob(global_scale)

        life_span = nuke.Int_Knob("life_span", "Life Span")
        life_span.setValue(40)
        group.addKnob(life_span)

        img = nuke.nodes.Input(name="img")
        img.setXYpos(0, -1000)

        transforms = {}
        for f in spawn_frames:
            t = nuke.nodes.Transform(name="T{}".format(f))
            t.setInput(0, img)
            t.setXYpos(0, -1000 + (spawn_frames.index(f) + 1) * 100)

            tx_expr = "[expression parent.Chamber_pos.x({f})]-center.x+((frame-{f})*parent.side_speed*(1+(random({f})*parent.rand_speed)))".format(f=f)
            ty_expr = "[expression parent.Chamber_pos.y({f})]-center.y+(parent.arc_height*(1+(random({r})*parent.rand_arc))*(frame-{f}))-(0.5*parent.gravity*pow(frame-{f},2))".format(f=f, r=f+1)

            t['translate'].setExpression(tx_expr, 0)
            t['translate'].setExpression(ty_expr, 1)
            t['rotate'].setExpression("(frame-{f})*parent.global_spin".format(f=f))
            t['scale'].setExpression("parent.global_scale")
            t['center'].setExpression("input.width/2", 0)
            t['center'].setExpression("input.height/2", 1)

            transforms[f] = t

        prev = None
        for f in spawn_frames:
            m = nuke.nodes.Merge2(name="M{}".format(f))
            m.setXYpos(400, -1000 + (spawn_frames.index(f) + 1) * 100)
            m.setInput(1, transforms[f])
            m.setInput(0, prev)
            m['mix'].setExpression("frame>={f}&&frame<={f}+parent.life_span?1:0".format(f=f))
            prev = m

        out = nuke.nodes.Output(name="Output1")
        out.setInput(0, prev)
        out.setXYpos(400, -100)
shell_emitter()