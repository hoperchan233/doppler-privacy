"""Scenario 1b: how fast does a single eavesdropper's Doppler error shrink with observation days (static tag)."""
import json
import numpy as np
from scipy.optimize import least_squares
from orbit import site_ecef, ecef_states, elevation_deg, range_rate, haversine_km, start_jd, C_KM_S, F0_HZ
from constellations import legit, independent
rng = np.random.default_rng(11)
SIG_F, REP, MIN_EL, TRIALS = 2.2, 60.0, 5.0, 30
names, kin = legit("argos.tle"); jd0 = start_jd(kin)
eav = independent(3, jd0, np.random.default_rng(3))[2:]   # the SSO one
la, lo = 35.2, 138.8; x = site_ecef(la, lo)
out = {}
for days in (1, 7, 30):
    t = np.arange(0, days * 86400, REP)
    re, ve = ecef_states(eav, jd0, t); re, ve = re[0], ve[0]
    vis = elevation_deg(re, x) > MIN_EL; R, V = re[vis], ve[vis]; n = int(vis.sum())
    f = lambda p: (F0_HZ + p[2]) * (1 - range_rate(R, V, site_ecef(p[0], p[1])) / C_KM_S)
    truth = f([la, lo, 0.0]); out[days] = {"n": n}
    for B in (100, 1000, 3000, 10000):
        e = []
        for _ in range(TRIALS):
            m = truth + rng.normal(0, SIG_F, n) + rng.uniform(-B, B, n)
            best = None
            for k in range(4):
                r = least_squares(lambda p: f(p) - m, [la + rng.normal(0, .5), lo + rng.normal(0, .5), 0], x_scale=[.5, .5, 50], method="lm")
                best = r if best is None or r.cost < best.cost else best
            e.append(haversine_km(la, lo, best.x[0], best.x[1]))
        out[days][B] = float(np.median(e)); print(days, n, B, round(np.median(e), 1), flush=True)
json.dump(out, open("../results/s1b_result.json", "w"), indent=1)
