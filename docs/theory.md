# Theory notes (draft)

Notation:
- Tag at x. Satellite e has range-rate ṙ_k(x) at message k.
- Received frequency: f_k = f_t,k · g_k(x), where g_k = 1 − ṙ_k / c.
- Per-message noise σ = 2.2 Hz, the calibration from doppler-verify.

## L1a. Keyed i.i.d. offsets against a single receiver

The tag adds Δf_k = PRF(K_t, k) mapped to U[−B, B]. A receiver without the key sees the offset as extra noise with variance B²/3.
After the unknown f0 is projected out, the Fisher information for position is

J = Σ_k ∇h_k ∇h_kᵀ / (σ² + B²/3),

so RMSE ∝ sqrt(σ² + B²/3) / sqrt(N). The error therefore grows linearly in B and falls as 1/√N.

Simulation check (s1, s1b, Fuji, B = 3 kHz): 102 km after 1 day, 37 km after 7 days, 24 km after 30 days.
- 102/37 = 2.8, against √7 = 2.6.
- 30-day decay is somewhat slower than √30, because day-to-day pass geometry repeats.

**Leak caused by GPS-scheduled transmissions.** If transmit epochs are known, the time of arrival gives one-way pseudo-ranges. A single satellite then localizes the tag to about 0.8 km in 24 h.
Keyed jitter U[0, J] adds variance J²/12 to the timing:
- J = 1 ms raises the error to about 20 km.
- J = 10 ms raises it to 200–300 km.

## L1b. Targeted decoy precompensation (known eavesdropper e)

The tag sets f_t,k = F0 · g_k^e(d) / g_k^e(x), where d = x + δ and δ is secret and long-lived.
Receiver e then sees F0 · g_k^e(d) plus noise. This is the same distribution as an honest stationary tag at d.

**Proposition (indistinguishability).** For receiver e, the likelihoods of (x, precompensated toward d) and (d, honest) coincide. Hence every estimator built from e's data has an error of at least |δ| − ε_d, where ε_d is the estimator's error at d. No amount of observation time removes this.

Simulation (s4): the error equals |δ| to within 0.1% after 1, 7 and 30 days.
- i.i.d. offsets with the same RMS excursion decay to 0.4–8 km at 30 days.
- The keyholder subtracts the known precompensation and keeps a 0.02–0.18 km error.

Notes:
- Choosing δ = 10 km costs only about 30–50 Hz RMS of frequency excursion.
- δ must be long-lived. Redrawing δ per epoch around zero lets an attacker average the decoys back to x.
- A fixed δ preserves the shape of the trajectory, so only the absolute position is protected.
- δ should be smaller than what coarse leaks reveal (footprint, pass timing, roughly 100 km).
- The scheme is the frequency-precompensating relay of doppler-verify, used here as a defense. Its limit is the same: a second, untargeted receiver sees an inconsistent curve (s4: a biased fix of 6–124 km). This is why L2 and L3 are needed against more than one receiver.

## L2. Orbit-aware scheduling

The tag transmits only when the legitimate system is in view and at most one known eavesdropper satellite is in view.
Every transmit-side perturbation is common-mode, so it cancels in TDOA/FDOA. L2 therefore removes the paired-receiver configuration instead of trying to defeat it.
The cost is the loss of allowed time. s2 measures it with real Kinéis TLEs.

## L3. Keyed DSSS with power control: the quadratic penalty

Notation: γ is the input SNR in bandwidth B; T is the message duration.
- The keyholder despreads and gets Γ_L = BT · γ_L.
- An unkeyed pair must cross-correlate the two raw receptions. Stein (IEEE Trans. ASSP 29(3), 1981; check the constant) gives an output SNR of about BT · γ1 γ2 / (1 + γ1 + γ2).

Write γ_i = ρ_i · γ_L, where ρ_i = G_i/G_L · (R_L/R_i)². With the tag operating at a fixed Γ_L:

Γ_pair ≈ BT · ρ1 ρ2 · γ_L² = Γ_L² · ρ1 ρ2 / BT      (γ ≪ 1)

**Theorem sketch.** At a fixed legitimate operating point, the pair SNR falls as 1/BT while the keyholder's SNR stays constant.
Locating requires ρ1 ρ2 ≥ Γ_th · BT / Γ_L². Ideal non-coherent accumulation of N messages lowers that requirement by √N.
In dB, with symmetric ρ:

ρ_dB ≥ ½ (Γ_th + 10 log BT − 2 Γ_L − 5 log N)

Worked example: Γ_th = 13 dB, BT = 6·10⁴, Γ_L = 12 dB, N = 96 messages/day. This gives about 13.5 dB of eavesdropper gain advantage, before the range term.

A single energy detector needs a deflection √(N·BT) · γ_E ≥ D_th, i.e. ρ ≥ D_th · √BT / (√N · Γ_L). For one message that is about 20 dB; with N = 96 it is about 10 dB.

Simulations s3 (per message) and s5 (per day) agree with these thresholds within about 3 dB. Adaptive power control, which keeps the minimum Γ_L at the best visible legitimate satellite, adds about 5 dB.

## Composition

| Attacker | Layer that stops it | Residual |
| --- | --- | --- |
| Single known satellite | L1b decoy | Error ≥ \|δ\| |
| Single unknown satellite | L1a offsets + L3 | Error B/√N; detection above about 10–15 dB of gain advantage |
| Pair or formation, orbits known | L2 | Pair geometry removed; some allowed time lost |
| Pair, orbits unknown | L3 | Below about 10 dB of gain advantage (per day) |
