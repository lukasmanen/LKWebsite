---
layout: ../../../layouts/PostLayout.astro
title: "Color Isolator"
date: "2026-02-21"
tags: ["Blinkscript", "Nuke"]
summary: "A per-pixel color isolation kernel built in Blinkscript for NukeX."
image: /assets/ColorIsolator/ColorIsolatorThumbnail.jpg
---

## Overview

Pick a color, get a matte. Everything close to the target stays, everything else
falls off. Output is either a matte or the original image masked by the matte.

> A simple kernel but a good one to understand, once you see how color difference
> is just subtraction across three channels, a lot of other techniques start making sense.

---

## The Algorithm

The kernel subtracts the target color's channels from the pixel's channels, squares
each difference, adds them together, and square roots the result. That single number
represents how different the pixel is from the target. Pixels within the threshold
get a mask of 1, pixels beyond it fall off over the softness range.

### Parameters

| Parameter      | Description                                                 |
|----------------|-------------------------------------------------------------|
| Target         | The color to isolate                                        |
| Threshold      | How close a pixel needs to be to the target to pass         |
| Softness       | How gradually the mask falls off beyond the threshold       |
| Colored Output | Off = greyscale matte · On = original color masked by matte |

---

## Before and After

<div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin:2rem 0;">
  <figure style="margin:0;">
    <img src="/assets/ColorIsolator/ColorIsolatorBefore.jpg" alt="Before — full color input" />
    <figcaption>Input — full color</figcaption>
  </figure>
  <figure style="margin:0;">
    <img src="/assets/ColorIsolator/ColorIsolatorAfter.jpg" alt="After — isolated color" />
    <figcaption>Output — isolated color</figcaption>
  </figure>
</div>

---


## Blinkscript Code

```cpp
// ColorIsolator — isolates a target color using RGB distance
//
// Threshold — hard cutoff radius around the target color
// Softness  — falloff range beyond the threshold. 0 = hard edge

kernel ColorIsolator : ImageComputationKernel<ePixelWise> {
  Image<eRead, eAccessPoint, eEdgeClamped> src;
  Image<eWrite>dst;

  param:
    float4 target;
    float  threshold;
    float  softness;
    bool   coloredOutput;

  void process() {
    float4 pixel = src();

    // subtract target channels from pixel channels
    float dR   = pixel.x - target.x;
    float dG   = pixel.y - target.y;
    float dB   = pixel.z - target.z;

    // square each difference, sum them, take the square root
    // gives a single value representing how different the pixel is from the target
    float dist = sqrt(dR*dR + dG*dG + dB*dB);

    // pixels inside threshold clamp to 1, beyond threshold+softness clamp to 0
    // epsilon prevents division by zero when softness = 0
    float mask = 1.0f - (dist - threshold) / (softness + 0.000001f);
    mask = clamp(mask, 0.0f, 1.0f);

    if (coloredOutput) {
      dst() = float4(pixel.x * mask, pixel.y * mask, pixel.z * mask, pixel.w);
    } else {
      dst() = float4(mask, mask, mask, mask);
    }
  }
};

