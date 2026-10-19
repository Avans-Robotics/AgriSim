# Measurement protocol for Plant physics

Written 2026-10-19 for M4 ([ADR 0006](../adr/0006-pull-out-via-anchored-root-and-force-law.md)), to be run later in the field. Until it has run, every Plant physics value in the Crop YAML is a literature value or a guess, and the simulated Plants are uncalibrated.

## What it calibrates

| Quantity | Used for | Current value (carrot) |
|---|---|---|
| Pull-out Force range | `physics.pull_out_force` | 15 to 26 N, loosened soil, literature |
| Travel to the peak `d_peak` | Pull-out Curve | 5 mm, guess |
| `residual_fraction` | Pull-out Curve | 0.3, guess |
| Pull-out damping `c` (speed effect) | `pull_out_curve.pull_out_damping` | 0 (off), unmeasured |
| Whether the peak correlates with root size | Sampling of the Pull-out Force | assumed independent |
| Petiole bending stiffness | `petiole_modulus` | about 500 MPa, taro petiole, guess for carrot |
| Root and top mass | Physics export densities | guess |

The goal is distributions per Crop and soil condition, not values for individual Plants: Pull-out Force varies a lot from Plant to Plant even in one bed.

## Equipment

- A load cell (about 0 to 500 N, so a torn-off top in compact soil stays in range) with a logger at 100 Hz or more, on a handle or a slow linear actuator.
- A displacement measurement: a draw-wire sensor on the handle logged with the force, or, as a cheaper option, a logging force gauge plus a 60 fps phone video against a ruler, synchronised by a clap or a tap on the gauge.
- A clamp that grips the leaf bunch about 3 cm above the crown, as the robot will.
- Calipers, a kitchen scale (0.1 g), a tape measure.
- A soil moisture probe and a penetrometer (cone index).
- For petiole bending: a small clamp, a few known weights (for example 2, 5 and 10 g), a grid card behind the leaf and a phone camera.

## Per bed (soil condition)

1. Note the soil treatment (loosened, undisturbed), date, time and weather.
2. Measure soil moisture at 5 and 15 cm depth at three spots in the bed.
3. Measure the penetrometer cone index down to root depth at the same three spots.
4. Pull about 30 Plants per soil condition, spread over the bed, skipping edge rows.
5. Pull about 10 more Plants at a second, faster speed (for example about 20 cm/s), spread over the same bed, for the speed effect.

## Per pull

1. Clamp the leaf bunch about 3 cm above the crown.
2. Pull straight up at a constant, slow speed (aim for about 5 cm/s, note the actual speed from the log or video), until the root is fully out.
3. Log force and displacement for the whole pull, from before the clamp takes up the slack until the root is free.
4. Record whether the tops tore off before the root came out, and at which force.
5. Measure the Plant: root length, shoulder diameter, root mass and top mass (tops cut at the crown).
6. Give each pull an id that links the log, the video and the measurements.

## Petiole bending (about 10 Plants per Crop)

1. Clamp one petiole at the crown, horizontal, in front of the grid card.
2. Photograph it unloaded, then with each weight hung at a marked point near the blade.
3. Measure the petiole diameter at the base, middle and tip, and the length to the load point.
4. The deflection per load gives the bending stiffness `E * I` through the cantilever formula, so `E` follows from the measured diameter.

## Analysis

- Per pull: the peak force `F_peak`, the travel to the peak `d_peak`, the force just after the drop as a fraction of the peak, and the shape of the decay to zero.
- Per soil condition: the distribution of each value, and whether `F_peak` correlates with root length, shoulder diameter or root mass. If it does, the Pull-out Force can be sampled from the Variant's root size instead of independently.
- Speed effect: compare the force over the decay phase between the two pull speeds; the difference divided by the speed difference gives the damping `c`. If the peak force also differs between speeds, note it: a linear damping term cannot model that and the Pull-out Curve needs a speed-dependent peak.
- Per Crop: the petiole modulus range and the root and top densities, written to the Crop YAML with this protocol as the source.
- Compare the measured curves with the simulated Pull-out Curve of a matching Variant and Plant scale.
