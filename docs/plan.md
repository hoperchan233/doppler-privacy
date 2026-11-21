# TVT paper plan (draft)

Working title: *Keyed Exposure-Aware Transmission for Location Privacy of Satellite IoT Terminals against Passive LEO Eavesdroppers*

1. Introduction. Covers the satellite-IoT location leak that payload encryption (ARROW) does not cover, and why the leak matters for wildlife and assets.
2. System and threat model. Attackers E1 (single satellite), E2 (formation such as HawkEye 360), E3 (several satellites in different orbits, possibly colluding), plus coarse leaks (footprint, pass timing).
3. Leakage analysis.
   - CRB for a single satellite using Doppler or TOA.
   - GPS-scheduled transmission as a leak.
   - Common-mode cancellation in TDOA/FDOA, which makes any transmit-side perturbation useless against a pair.
4. Design.
   - L1a keyed offsets and jitter.
   - L1b decoy precompensation (indistinguishability proposition).
   - L2 TLE scheduling.
   - L3 keyed DSSS plus power control (quadratic-penalty theorem).
   - Key management with ARROW's time-anchored tree.
5. Simulation with real Kineis TLEs: scripts s1-s5.
6. Prototype.
   - STM32WL55 tag: per-message frequency agility, PLL settling time, jitter and energy.
   - Two GPS-disciplined SDRs on the ground or on a UAV, acting as a scaled-down TDOA/FDOA pair, to measure the CAF penalty.
7. Discussion. Argos compatibility (legacy Argos cannot despread, so this is a new-system design), the loss of the operator's own Doppler fix, regulation, and the relation to doppler-verify.

## Hardware: on hand and to buy
- On hand: STM32WL55 board and antenna.
- To buy:
  1. Two SDR receivers (RTL-SDR v4 for a minimum setup; HackRF One or USRP B200mini for better timing).
  2. A GPSDO or GPS 1PPS/10 MHz reference for each receiver, needed for TDOA/FDOA.
  3. A transmitter for the L3 DSSS test. The WL55 radio has no chip-rate DSSS, so use a HackRF in TX.
  4. Attenuators, coax cables, and a shielded box for conducted tests.
  5. A Nordic PPK2 if one is not available in the lab.
  6. Antennas for the test band.
- Band: in Japan, test in a specified low-power band (426/429 or 920 MHz) or conducted only. Do not radiate at 401 MHz.

## Open items
- Real HawkEye TLEs.
- Whether Kineis or Argos-4 supports active offsets of several kHz and a spread waveform.
- Simulating decoy precompensation against a pair.
- The exact constant in Stein 1981.
