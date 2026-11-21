# doppler-privacy

This repository studies location privacy for satellite-IoT tags (wildlife tags and similar) against passive LEO eavesdroppers that locate a transmitter from Doppler, TOA, TDOA or FDOA. The target venue is IEEE TVT.

It is a separate line from `doppler-verify`, which uses Doppler to verify a tag's location, and from `satnetsec` (ARROW), which protects the payload. The keys come from ARROW's time-anchored key tree.

## Layered defense
| Layer | Mechanism | Attacker it stops |
| --- | --- | --- |
| L1a | Keyed per-message frequency offsets and timing jitter | A single receiver doing Doppler or TOA |
| L1b | Keyed decoy-location precompensation | A known single receiver, for as long as it observes |
| L2 | TLE-aware scheduling: never transmit while two eavesdroppers are in view | Formations and colluding pairs (TDOA/FDOA) |
| L3 | Keyed DSSS with adaptive power control (LPD) | Pairs with unknown orbits, and energy detectors |

## Running it
Needs Python 3, numpy, scipy and sgp4. Run every script from `sim/`; each one writes `results/sN_result.json`.

- `s1_single.py`: a single eavesdropper uses Doppler or TOA for 24 h against keyed offsets U[-B,B] and jitter U[0,J].
- `s1_days.py`: the same attack observed for 1, 7 and 30 days, showing the 1/sqrt(N) decay of i.i.d. offsets.
- `s2_schedule.py`: the scheduling cost when no two eavesdropper satellites may be in view (7 days, 5 sites, 5 seeds).
- `s3_lpd.py`: per-message detection and pair localization under L3.
- `s4_decoy.py`: decoy precompensation compared with i.i.d. offsets, plus the keyholder's result and an untargeted satellite.
- `s5_accum.py`: L3 against an attacker that accumulates a whole day of messages (96 msg/day budget).
- `s6_real_hawkeye.py`: L2 and L3 against the real HawkEye 360 constellation (46 satellites, OMM JSON), alone and with 12 extra independent satellites.

Theory notes are in `docs/theory.md`; the paper plan and hardware list are in `docs/plan.md`.

## Data
- Legitimate system: 25 real Kineis TLEs in `sim/argos.tle`, epoch 2026-10, copied from doppler-verify.
- Real HawkEye 360: `data/hawkeye/`, CelesTrak OMM JSON downloaded by Chen on 2026-11-21. It covers 46 satellites, including KESTREL-0A and the 6-digit NORAD ids that legacy TLE cannot hold. Refresh it with `refresh_hawkeye360.py`.
- Synthetic eavesdroppers for s2-s5: HawkEye-like 3-satellite clusters (575 km SSO, 125 km along-track spacing) and independent satellites at 550 km.
- Caveat for s6: the Kineis TLEs are about 50 days older than the HawkEye epoch, so Kineis phasing is representative only statistically. Refresh the Kineis elements before final numbers.
