# Pixel Farming Field Generation

Tools to generate pixel farming fields for robot simulation. A field is described once, independent of any simulator, and then exported to a simulator (Gazebo first).

## Language

### Field

**Field**:
A rectangular grid of Pixels, the full area that gets generated.
_Avoid_: plot, map, world

**Pixel**:
A square cell of the Field, `pixel_size` by `pixel_size` meters, that holds exactly one Crop or is empty.
_Avoid_: cell, tile, patch, strip

**Empty Pixel**:
A Pixel with no Crop: bare soil.
_Avoid_: blank, gap

**Path Gap**:
An optional strip of bare soil between groups of Pixel columns, left free for robot wheels.
_Avoid_: track, lane, aisle

**Border**:
The strip of textured soil around the Field, room for a robot to drive in and turn.
_Avoid_: headland, margin (reserved for the Planting Pattern)

### Crops and plants

**Crop**:
A kind of plant (carrot, lettuce, ...) together with its Planting Pattern, variation ranges and physical properties.
_Avoid_: species, plant type

**Plant**:
One placed instance of a Crop in the Field, with its own pose, size and properties.
_Avoid_: crop instance, specimen

**Planting Pattern**:
How Plants of one Crop are arranged inside a Pixel: rows, spacing, margin and random deviations.
_Avoid_: layout (reserved for Field Layout), grid

**Pull-out Force**:
The force in newtons needed to pull one Plant out of the soil.
_Avoid_: extraction force, uprooting force

**Picked Plant**:
A Plant spawned as its own articulated model in a running world, held by its Pull-out Curve until it is pulled out, or until it turns back into its static visual when left alone (unpick).
_Avoid_: dynamic plant, spawned plant

**Active Region**:
The space around any robot link in which root crop Plants become Picked Plants, so the robot touches them.
_Avoid_: active zone, interaction area

**Pull-out Curve**:
The resisting force on a Plant's root as a function of how far the root has moved up, ending in detach; its peak is the Pull-out Force.
_Avoid_: pull-out profile, force profile

### Descriptions

**Field Spec**:
The input that describes a Field: either a hand-drawn Pixel grid or a request for a random one.
_Avoid_: config, field file

**Field Layout**:
The fully resolved, simulator-independent list of Pixels and Plants produced from a Field Spec and a seed.
_Avoid_: scene, world

**Manifest**:
The Field Layout written to disk next to an exported world, used as ground truth.
_Avoid_: labels, metadata

### Assets and export

**Asset Library**:
The committed set of 3D models per Crop, each Crop having several visual variants.
_Avoid_: model zoo, asset cache

**Variant**:
One 3D model of a Crop in the Asset Library; Plants reuse Variants with their own rotation and scale.
_Avoid_: model, mesh

**Asset Generator**:
Anything that produces Variants for the Asset Library, such as a procedural script or an import from another library.
_Avoid_: modeler, builder

**Exporter**:
The part that turns a Field Layout into files for one specific simulator or renderer.
_Avoid_: backend, adapter, converter
