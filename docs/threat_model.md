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

## T2: evidence-based stress tests (s7, s8; no arbitrary attackers)
Every T2 assumption below is tied to a public source or to measured data. The earlier "12 extra colluding satellites" case was dropped because nothing supports it.

| Stress | Evidence | Setting |
| --- | --- | --- |
| Stale onboard ephemeris | Chen's real HawkEye snapshot TLE compared with the OMM truth. Quiescent satellites aged 5-16 days show 0-15 s timing error. Elements aged 21-83 days show 37-65 s. Newly launched HAWK-15A/B, still orbit raising, show 160-600 s. A Starlink SGP4 study (arXiv 2605.19850) reports a 38.5 km median at 7 days. | No refresh, or refresh every 7/14/30 days with 1 day latency. Guard margin M, widened for satellites under 3 months old. |
| Stationary animal | An incubating or denning animal stays put for weeks (shorebird incubation is about 3 weeks). | The attacker accumulates 1, 7 or 21 days. |
| Larger aperture | Kineis satellite antenna gain is -4 to +4.2 dBi (isoflux, FCC filing SAT-PDR-20191011-00113). A 15 dB advantage needs about 19 dBi, i.e. a reflector of about 3 m at 400 MHz. | dG = 15 dB (T1 uses 10 dB). |
| Constellation growth | Launch record in the OMM object ids: 4 HawkEye clusters in 2024, 1 cluster plus KESTREL-0A in 2025, 4 clusters in 2026. | +8 clusters, about 2 years of growth, assumed public. |

Not used: Unseenlabs works in S/X band, so it is not a UHF attacker, but it shows commercial single-satellite geolocation exists, which supports the T1 single-satellite class. Kleos: company trading suspended since 2023, constellation status unclear.

Results:
- **No refresh** (s7): 1.8-4.4% of transmissions leak to a pair. With 21-day accumulation at dG 15 dB, pair localization reaches 50-100%.
- **Weekly refresh**, M = 60 s, 900 s for new satellites (s8): leak 0%, and pair localization 0% for every window up to 21 days and every dG up to 15 dB.
    - Cost: 225-233 min/day allowed, max gap 6.5 h or less.
    - Single-satellite detection over 7-21 days rises to 83-100%. L1b (decoy) still bounds the error at |delta|.
- **Growth +8 clusters** (s7): 224-257 min/day allowed, max gap 3.2 h or less.

## Out of scope (one sentence in the paper, not studied)
- National SIGINT with large apertures (dG >= 20 dB) or covert orbits combined with a large dG.
- Active attacks: jamming, GNSS spoofing of the tag, relays. These belong to doppler-verify.
- Compromise of the tag or of its keys. ARROW's forward security limits the damage, but it is not evaluated here.
- Terrestrial attackers near the animal (VHF beacons, UAV homing). These belong to vhf-guard.
- The legitimate operator is trusted. Privacy against the operator is a possible extension.
