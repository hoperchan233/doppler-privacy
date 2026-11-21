"""Scenario 4: keyed decoy-location precompensation against a KNOWN single eavesdropper (public TLE).
For each message the tag (GPS position x, onboard TLE) sets f_t = F0 * g_e(d)/g_e(x), d = x + delta (secret),
so the targeted eavesdropper e sees exactly the Doppler curve of a stationary transmitter at d.
Compared with i.i.d. keyed offsets U[-B,B] at the same RMS frequency excursion, over 1/7/30 days.
Also reports what an UNTARGETED satellite e2 (different orbit) sees from the same transmissions,
and the keyholder's error after removing the known precompensation."""
import json
import numpy as np
from scipy.optimize import least_squares
from orbit import site_ecef, ecef_states, elevation_deg, range_rate, haversine_km, offset, start_jd, C_KM_S, F0_HZ
from constellations import legit, independent

rng = np.random.default_rng(21)
SIG_F, REP, MIN_EL, TRIALS = 2.2, 60.0, 5.0, 20
la, lo = 35.2, 138.8
DELTAS_KM = (10, 50, 200)
names, kin = legit("argos.tle"); jd0 = start_jd(kin)
sats = independent(3, jd0, np.random.default_rng(3))
e, e2 = sats[2], sats[0]           # targeted SSO eavesdropper, untargeted 53-deg satellite
x = site_ecef(la, lo)


def g(R, V, xx):
    return 1 - range_rate(R, V, xx) / C_KM_S


def fit(R, V, m):
    f = lambda p: (F0_HZ + p[2]) * g(R, V, site_ecef(p[0], p[1]))
    best = None
    for _ in range(4):
        r = least_squares(lambda p: f(p) - m, [la + rng.normal(0, 1), lo + rng.normal(0, 1), 0], x_scale=[.5, .5, 50], method="lm")
        best = r if best is None or r.cost < best.cost else best
    return best.x


out = {"assumptions": dict(site="Fuji", sig_f=SIG_F, rep_s=REP, trials=TRIALS), "rows": []}
for days in (1, 7, 30):
    t = np.arange(0, days * 86400, REP)
    re, ve = ecef_states([e, e2], jd0, t)
    vis = elevation_deg(re[0], x) > MIN_EL
    R, V = re[0][vis], ve[0][vis]
    R2, V2 = re[1][vis], ve[1][vis]
    vis2 = elevation_deg(R2, x) > MIN_EL          # e2 hears the messages sent while targeting e
    n = int(vis.sum())
    for dk in DELTAS_KM:
        ed, ei, eu, ek = [], [], [], []
        for _ in range(TRIALS):
            d = site_ecef(*offset(la, lo, dk, rng.uniform(0, 2 * np.pi)))
            ft = F0_HZ * g(R, V, d) / g(R, V, x)          # precompensated transmit frequency
            dev = ft - F0_HZ
            m = ft * g(R, V, x) + rng.normal(0, SIG_F, n)
            p = fit(R, V, m); ed.append(haversine_km(la, lo, p[0], p[1]))
            # i.i.d. offsets with the same RMS excursion
            B = np.sqrt(3) * dev.std()
            m_iid = F0_HZ * g(R, V, x) + rng.uniform(-B, B, n) + rng.normal(0, SIG_F, n)
            p = fit(R, V, m_iid); ei.append(haversine_km(la, lo, p[0], p[1]))
            # keyholder: removes the known precompensation
            p = fit(R, V, m - dev); ek.append(haversine_km(la, lo, p[0], p[1]))
            # untargeted satellite e2
            if vis2.sum() >= 6:
                m2 = ft[vis2] * g(R2[vis2], V2[vis2], x) + rng.normal(0, SIG_F, int(vis2.sum()))
                p = fit(R2[vis2], V2[vis2], m2); eu.append(haversine_km(la, lo, p[0], p[1]))
        row = dict(days=days, n_msgs=n, delta_km=dk, rms_dev_hz=float(dev.std()),
                   decoy_err_km=float(np.median(ed)), iid_err_km=float(np.median(ei)),
                   keyholder_err_km=float(np.median(ek)), n_untargeted=int(vis2.sum()),
                   untargeted_err_km=float(np.median(eu)) if eu else None)
        out["rows"].append(row); print(row, flush=True)
json.dump(out, open("../results/s4_result.json", "w"), indent=1)
