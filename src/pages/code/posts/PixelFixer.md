---
layout: ../../../layouts/PostLayout.astro
title: "PixelFixer"
date: "2026-03-17"
tags: ["Blinkscript", "Nuke"]
summary: "A firefly and hot pixel removal node built in Blinkscript for NukeX."
category: ""
image: /assets/PixelFixer/PixelFixerThumbNail.jpg
---

## Overview

> I won't be sharing the code or the Gizmo for this one, but I wanted to document how it works anyway.

During a school project we were getting a ton of fireflies in our renders. Fireflies are most common with path tracing, it's just how the algorithm works, occasionally a ray gets unlucky with a light sample and one pixel ends up way hotter than it should be. The result is a little white or coloured speck flickering in and out over a few frames.

I was stacking multiple nodes and running everything through NeatVideo and you could still see warm pixels dancing around. Nothing was fully killing them. So I built something that could run as a pre-pass before NeatVideo and just handle all of it in one go.

> One node. Drop it in. Dancing Bright pixels & fireflies gone.

<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin:2rem 0;">
  <figure style="margin:0;">
    <img src="/assets/PixelFixer/PixelFixerBefore.jpg" alt="Before, fireflies visible" />
    <figcaption>Input, fireflies visible</figcaption>
  </figure>
  <figure style="margin:0;">
    <img src="/assets/PixelFixer/PixelFixerAfter.jpg" alt="After, cleaned" />
    <figcaption>Output, cleaned in a single pass</figcaption>
  </figure>
</div>

---

## The Algorithm

### Finding What Doesn't Belong

For each pixel, the tool collects all the surrounding pixels in a window, 3×3, 5×5, or 7×7 depending on how big the artifact is. Those get sorted by brightness and the **median** gets pulled out, the value sitting right in the middle of the sorted list.

The median is more reliable than averaging here. An average gets dragged toward any extreme value in the list. The median just ignores them. If the center pixel deviates too far from that median, it gets flagged.

The detection also checks **red, green and blue separately**. A weird pink or blue speck might not even look that bright in overall luminance but it's clearly wrong. Checking each channel independently catches those.

### Adapting to Local Content

A flat threshold doesn't work because what counts as "too different" depends entirely on where you are in the image. A deviation on a flat grey wall is suspicious. The same deviation on a rough stone texture with lots of natural contrast is completely fine.

To fix this the tool computes the **Median Absolute Deviation** how spread out the neighbourhood values are around the median. Flat areas get a tight threshold. Textured areas get a loose one. It adapts automatically without you having to think about it.

### Not Touching Real Detail

A pixel sitting on a hard edge genuinely looks different from some of its neighbours, the ones on the other side of the edge. That's not broken data, that's just the edge.

The tool checks whether a pixel is an outlier in every direction at once. A real firefly sticks out from above, below, left, right, and diagonally. An edge pixel only sticks out in one direction. That distinction is what keeps edges clean while still catching actual fireflies sitting on them.

---

## Using Time

### Temporal Checking

A firefly almost never survives more than a frame or two. Everything real around it stays consistent. So the tool reads two frames before and two frames after the current one and uses them to see if the bright pixel was there before/after if not it's a firefly.

If the surrounding frames agree on what the pixel should look like but the current frame disagrees, the current frame loses. Frames one step away count more than frames two steps away. 

> This is what really killed the dancing warm pixels. Spatially they were hard to remove since no more data was there to be compared against. But temporally they stick out immediately.

<figure style="margin:0;">
  <img src="/assets/PixelFixer/PixelFixerTemporal.jpg" alt="Temporal" />
  <figcaption>Frames ±1 and ±2 vote against the current pixel to confirm it's an outlier</figcaption>
</figure>

---

## Replacing the Pixel

When a pixel gets flagged it gets filled with a weighted blend of its neighbours closer pixels count more, and pixels that look like what the area should look like count more too. The brightest and darkest outliers in the neighbourhood get thrown out first so nearby fireflies don't contaminate the fill.

It also blends in pixels from the neighbouring frames, leaning toward those since they tend to hold more natural texture than a purely spatial patch.

<video controls playsinline style="width:100%; margin:2rem 0; border:1px solid #1f1f1f;">
  <source src="/assets/PixelFixer/PixelFixerComparison.mp4" type="video/mp4" />
</video>

---

## Parameters

| Parameter | Description |
|---|---|
| Filter Size | Size of the sampling window, 3×3 / 5×5 / 7×7 |
| Spatial Sensitivity | How far a pixel needs to deviate to be flagged |
| Highlight Protection | Gives brighter pixels more tolerance before flagging |
| MAD Multiplier | Controls how adaptive the threshold is to local texture |
| Fix Mode | Target brights only, darks only, or both |
| Temporal Detect | Uses surrounding frames as additional evidence |
| Replace Method | Spatial fill, temporal fill, or a blend of both |
| Output View | Switch between result, confidence map, or binary mask |

This is what I built for the project, settings might need tweaking depending on the render. This was just a quick render showing it's potential i know it can handle severe renders with fireflies after using it on a plate which i cant share at the moment.
