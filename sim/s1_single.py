"""Scenario 1: a single eavesdropping LEO satellite localises a static tag over 24 h
from (a) Doppler and (b) time of arrival of GPS-scheduled messages.  The tag adds keyed
per-message frequency offsets U[-B,B] and/or keyed timing jitter U[0,J]; the keyholder subtracts them."""
import json, sys
import numpy as np
from scipy.optimize import least_squares
from orbit import site_ecef, ecef_states, elevation_deg, range_rate, haversine_km, offset, start_jd, C_KM_S, F0_HZ
from constellations import legit, independent

rng = np.random.default_rng(7)
SIG_F = 2.2        # Hz, calibrated per-message noise (doppler-verify)
SIG_T = 10e-6      # s, TOA noise for a ~kHz-wide narrowband message (assumption)
REP = 60.0         # s between messages
MIN_EL = 5.0
TRIALS = 40
BS = [0, 3, 10, 30, 100, 300, 1000, 3000]
JS = [0, 1e-4, 1e-3, 1e-2, 1e-1]
SITES = [("Kenya", 0.0, 37.0), ("Fuji", 35.2, 138.8), ("North Slope", 70.2, -148.3)]

names, kin = legit("argos.tle")
jd0 = start_jd(kin)
eav = independent(1, jd0, np.random.default_rng(3))
t = np.arange(0, 86400, REP)
re, ve = ecef_states(eav, jd0, t)
re, ve = re[0], ve[0]


def geom(lat, lon):
    x = site_ecef(lat, lon)
    return x


def fit(model, meas, p0, scale):
    best = None
    for k in range(6):
        start = p0 + rng.normal(0, 1, len(p0)) * scale
        r = least_squares(lambda p: model(p) - meas, start, x_scale=scale, method="lm", max_nfev=400)
        if best is None or r.cost < best.cost:
            best = r
    return best.x


out = {"assumptions": dict(sig_f_hz=SIG_F, sig_t_s=SIG_T, rep_s=REP, min_el=MIN_EL, trials=TRIALS,
                           eavesdropper="1 synthetic sat, 550 km, 53 deg", window="24 h"), "sites": {}}
for name, la, lo in SITES:
    x = geom(la, lo)
    el = elevation_deg(re, x)
    vis = el > MIN_EL
    R, V = re[vis], ve[vis]
    n = int(vis.sum())
    res = {"n_msgs": n, "doppler": {}, "toa": {}}
    print(name, "messages seen by eavesdropper in 24 h:", n, flush=True)

    def fmodel(p):
        xx = site_ecef(p[0], p[1])
        return (F0_HZ + p[2]) * (1 - range_rate(R, V, xx) / C_KM_S)

    def tmodel(p):
        xx = site_ecef(p[0], p[1])
        return np.linalg.norm(R - xx, axis=-1) / C_KM_S + p[2]

    truth_f = fmodel([la, lo, 0.0])
    truth_t = tmodel([la, lo, 0.0])
    for B in BS:
        errs = []
        for _ in range(TRIALS):
            meas = truth_f + rng.normal(0, SIG_F, n) + rng.uniform(-B, B, n)
            p = fit(fmodel, meas, np.array([la, lo, 0.0]), np.array([0.5, 0.5, 50.0]))
            errs.append(haversine_km(la, lo, p[0], p[1]))
        res["doppler"][str(B)] = float(np.median(errs))
        print(f"  Doppler B={B:>5} Hz  median err {np.median(errs):9.2f} km", flush=True)
    for J in JS:
        errs = []
        for _ in range(TRIALS):
            meas = truth_t + rng.normal(0, SIG_T, n) + rng.uniform(0, J, n)
            p = fit(tmodel, meas, np.array([la, lo, J / 2]), np.array([0.5, 0.5, max(J, 1e-5)]))
            errs.append(haversine_km(la, lo, p[0], p[1]))
        res["toa"][str(J)] = float(np.median(errs))
        print(f"  TOA     J={J:>7} s   median err {np.median(errs):9.2f} km", flush=True)
    out["sites"][name] = res
json.dump(out, open("../results/s1_result.json", "w"), indent=1)
