# Threat model: tiered (draft, 2026-11-21)

Principle: give hard guarantees against a realistic, clearly stated attacker. Report stronger attackers as stress tests, and leave the extreme ones explicitly out of scope.

## T1: primary model (all main results and guarantees)
- Passive receivers in space whose orbits are **public** (TLE/OMM). Two kinds:
  - a single LEO satellite, such as a rideshare cubesat or the receiver of another IoT operator;
  - a commercial formation-flying RF-geolocation constellation, represented by the real HawkEye 360 elements (46 satellites).
- We do not claim HawkEye targets this band; it serves only as a realistic benchmark of a known-orbit pair-capable attacker.
- Smallsat-class receive chain: antenna or G/T advantage dG <= 10 dB over the legitimate satellite.
- The attacker knows the protocol (Kerckhoffs) but not the key. It can accumulate up to one day of messages non-coherently and collude across all T1 satellites.
- Guarantees (s4, s6):
  - Pair (TDOA/FDOA) localization is 0% of days, because of L2.
  - A single satellite converges to the decoy (error >= |delta|), because of L1b.
  - Day-level detection is 0-36% at dG = 10 dB.
  - Cost: the tag can transmit 312-418 min/day with gaps of 2.4 h or less, enough for the 96 msg/day budget.

## T2: stress tests (reported, no guarantee claimed)
- 12 additional colluding satellites with orbits we do not model, inclined 53/70/97.6 deg. The allowed time falls to 268-314 min/day.
- dG = 15 dB. Pair localization stays at 0% under L2. A single satellite detects the tag on most days, but L1b still limits it to the decoy.

## Out of scope (stated in the paper)
- National SIGINT with large apertures (dG >= 20 dB) or covert orbits combined with a large dG.
- Active attacks: jamming, GNSS spoofing of the tag, relays. These belong to doppler-verify.
- Compromise of the tag or of its keys. ARROW's forward security limits the damage, but it is not evaluated here.
- Terrestrial attackers near the animal (VHF beacons, UAV homing). These belong to vhf-guard.
- The legitimate operator is trusted. Privacy against the operator is a possible extension.
