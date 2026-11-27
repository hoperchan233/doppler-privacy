# Novelty check (2026-11-22, titles/abstracts via web search; IEEE Xplore not queried directly)

| Work | What it does | Overlap with us |
| --- | --- | --- |
| Finger & Francillon, WiSec 2020 poster, Argos cyberpoaching | Argos uplink is in the clear; proposes stream ciphers. Location stays exposed through payload and DSE data | Motivation only; no physical-layer defense |
| Koisser et al., USENIX Sec 2024 SoK, "Orbital Trust and Privacy" | Uplink signals can be triangulated by other satellites; lists countermeasures (power modulation, artificial noise, fake traffic, delay) | **Closest framing.** L3 power control is conceptually listed there; we must cite it and position our work as a concrete, quantified design for IoT uplinks |
| Koisser et al., arXiv 2307.14879, "Don't Shoot the Messenger" | Starlink users triangulated via uplink; defense by mesh routing to random gateways | Same threat class; defense entirely different (network layer) |
| Jedermann et al., USENIX Sec 2024, RECORD | Region of LEO users from downlink reception only | Different channel (downlink) |
| Shi et al., USENIX Sec 2026, LPG | D2C operator links identity and location; protocol-level fix. Mentions TA and Doppler as observables | Different layer; useful citation that Doppler and TA leak |
| Coppola et al., 3S 2025, privacy of LEO two-way ranging | Location leak in LEO-PNT ranging | Different setting |
| Kong et al., IEEE TVT 2023, LEO vehicular location management | Pseudonym/protocol location privacy | Shows TVT publishes LEO location privacy; no RF |
| Argyriou (& Kosmanos), arXiv 2212.14241 / 2303.06600 | Doppler and range spoofing in WiFi OFDM to defeat passive emitter tracking | **Conceptual precedent for the L1b decoy.** Terrestrial, OFDM, no orbit or keyholder recovery |
| US 5,537,117 (Rose, Litton; filed 1995-08-08, granted 1996-07-16, expired) | Pulse radar defeats an airborne passive Doppler ESM observer. The radar tracks the observer (velocity v_p, direction u_p) and varies its reference oscillator by df = f0 (v_p/c)(u_f - u_p), so RF carrier and PRF (TOA) are perturbed consistently and the observer solves for a chosen false location u_f. Perturbing both prevents detection by comparing frequency- and time-based Doppler | **Direct prior art for the L1b principle** (closed-loop false location from observer kinematics, frequency and time together). Differences: we take kinematics from public ephemerides, not active tracking; the false position is key-dependent and recoverable by the legitimate receiver; spoofing is consistent for one receiver only, so it needs scheduling against receiver pairs; multi-day accumulation and real constellations. Must cite; do not claim the spoofing principle as new |
| US 5,534,867 (Rose, Litton; 1996), open-loop sibling | Random (random-telegraph) RF and PRF perturbation, no observer knowledge needed | Prior art for L1a random offsets; we add that random offsets average out as B/sqrt(N) |
| US 8,447,295 (Palmer et al., Boeing; 2013) | CDMA VSAT network randomly redistributes unused power spectral density among terminals and pads with filler bits, so an eavesdropper cannot infer activity from received power. Background cites DSSS (US 7,136,621), random TDMA slots and FDMA as prior TRANSEC | Traffic-activity obfuscation, not geolocation. No conflict. Confirms DSSS for low detectability of satellite terminals is known, so L3 stays a design rule |
| LEO covert communication with UAV warden (arXiv 2504.10347) | Transmit only when the satellite is overhead, to avoid detection | Related to L2/L3 timing; detection, not geolocation |
| Ristic et al., arXiv 2607.28585 | Passive Doppler geolocation of IoT emitters from 3 LEO satellites, about 4.5 km | Attack side; supports the threat model |
| Stein 1981 (CAF) / covert-communication literature | SNR-squared behaviour of cross-correlation; LPD | The L3 "quadratic penalty" is classical. Present it as a design rule, not a new theorem |

**Assessment.** No paper found that defends low-rate satellite-IoT uplinks against Doppler/TOA/TDOA/FDOA geolocation by third-party LEO receivers.

Contributions likely to read as new:
1. Leakage quantification with real constellations, including the TOA leak caused by GPS-scheduled transmission.
2. The keyed decoy precompensation with an indistinguishability argument and keyholder recovery.
3. Orbit-aware scheduling against pair-capable constellations, with a measured ephemeris-ageing policy.
4. Integration with time-anchored keys.

Contributions to present modestly:
- L3, which is classical CAF/LPD.
- Power control, which is listed in Koisser's SoK.

Required citations: Koisser SoK, Argyriou, Finger & Francillon, Ristic, LPG, US 5,537,117 and US 5,534,867.

**Update 2026-11-28 (patents read in full).** US 5,537,117 already describes closed-loop Doppler/TOA spoofing toward a chosen false location using the observer's kinematics. The keyed pre-compensation is therefore an adaptation, not a new principle. Forward citations of US 5,537,117 (Google Patents, 17 entries, titles only) are all radar or EW; none concerns satellites, IoT terminals or location privacy. Suggested reframing: the paper's research question becomes "transmitter-side spoofing is inherently single-observer; under which conditions does it protect a satellite IoT terminal against a constellation of passive receivers?", with ephemeris-based scheduling as the condition-enforcing mechanism and the key as what makes the false position unpredictable yet recoverable.
