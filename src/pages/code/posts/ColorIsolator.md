---
layout: ../../../layouts/PostLayout.astro
title: "Color Isolator"
date: "2026-02-21"
tags: ["Blinkscript", "Nuke"]
summary: "A per-pixel color isolation kernel built in Blinkscript for NukeX."
category: ""
image: /assets/ColorIsolator/ColorIsolatorThumbnail.jpg
---


## Overview


Pick a color, get a matte. Everything close to the targeted colored stays, everything else
gets removed. Output is either a matte or the original image masked by the matte.


> A simple kernel but a good one to understand, once you see how color difference
> is just subtraction across three channels, a lot of other techniques start making sense.


---


## The Algorithm


### Color distance


We treat RGB like a 3D space. Each pixel is a point, and the target color is another
point in the same space. The distance between them is the Euclidean length of the
per-channel difference:

$$
d = \sqrt{(R - R_t)^2 + (G - G_t)^2 + (B - B_t)^2}
$$

In code that is, subtract target from pixel per channel, square each difference,
add them together, and square root the sum. That single number `d` represents how
different the pixel is from the target color.


### Threshold and softness


Once we have `d`, we convert it into a mask:

- If `d` is within the `threshold`, the pixel is inside the selection, mask = 1
- If `d` exceeds `threshold + softness`, the pixel is outside, mask = 0
- Between them, the mask falls off linearly from 1 down to 0

The linear falloff is:

$$
m = 1 - \frac{d - \text{threshold}}{\text{softness}}
$$

Then clamped to stay in range:

$$
m = \mathrm{clamp}(m,\; 0,\; 1)
$$

An epsilon is added to `softness` in the kernel to avoid dividing by zero when
`softness = 0`, which effectively gives you a hard edge at the threshold.


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
    <img src="/assets/ColorIsolator/ColorIsolatorBefore.jpg" alt="Before, full color input" />
    <figcaption>Input, full color</figcaption>
  </figure>
  <figure style="margin:0;">
    <img src="/assets/ColorIsolator/ColorIsolatorAfter.jpg" alt="After, isolated color" />
    <figcaption>Output, isolated color</figcaption>
  </figure>
</div>


---


## Blinkscript Code


```cpp
// ColorIsolator — isolates a target color using RGB distance
kernel ColorIsolator : ImageComputationKernel<ePixelWise> {
  Image<eRead, eAccessPoint, eEdgeClamped> src;
  Image<eWrite> dst;

  param:
    float4 target;
    float  threshold;
    float  softness;
    bool   coloredOutput;

  void process() {
    float4 pixel = src();

    // subtract target channels from pixel channels
    float dR = pixel.x - target.x;
    float dG = pixel.y - target.y;
    float dB = pixel.z - target.z;

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
