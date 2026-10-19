---
status: accepted
---

# Gazebo Plants grouped per Pixel

The Gazebo Exporter writes one static model per Pixel, named after the Pixel (`r<row>c<col>`), placed at the Pixel's south-west corner. Its Plants are visuals of that model's single link, each named after its Plant id from the Manifest. Pixels without Plants get no model.

## Why

A 10 x 10 carrot Field (3,058 Plants) with one static model per Plant ran at a real-time factor of 0.3 after a 20 s stall. The cost is the Physics system iterating over thousands of models, even static ones without collision; rendering and VRAM were not the bottleneck. Grouping per Pixel (100 models) runs at 1.0 with Physics, Sensors and VCT GI kept, and renders pixel-identical images.

## Considered Options

- **One model per Plant.** Needed for per-Plant pick-up and per-Plant labels, but misses the M2 performance budget with no known fix.
- **One model for the whole Field, or per row of Pixels.** Fewer models still, but a Pixel is the domain unit and the natural unit to swap in M4.
- **Switch between both layouts.** No current user for the per-Plant layout; git keeps the old code.

## Consequences

- **Labels.** Gazebo segmentation instance ids and bounding boxes are grouped per top-level model, so with this layout they are per Pixel, not per Plant. Gazebo provides semantic segmentation only (one label per Pixel model, since a Pixel holds one Crop). Per-Plant ground truth lives in the Manifest; per-Plant 2D boxes can be projected from it when a consumer needs them, and photorealistic labelled datasets come from a later Blender Exporter (ADR 0005).
- **Pull-out (M4).** `DetachableJoint` needs the picked Plant to be its own model with a link, and Gazebo services cannot hide or remove a single visual. M4d spawns a model for a picked Plant and removes its grouped visual from the gz-sim system that ADR 0006 requires (`RequestRemoveEntity`, which the GUI follows).
- **Mixed labels per model** (for example weeds inside a crop Pixel) can collide instance ids in Gazebo; revisit when weeds are added.
