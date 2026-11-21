"""Scenario 2: orbit-aware scheduling.  The tag transmits only when a Kineis satellite is in view
(el >= LEG_EL) and no eavesdropper group can form a simultaneous pair (>= 2 of its satellites at el >= 0).
Eavesdroppers: HawkEye-like 3-sat formation clusters, or independent satellites in different planes."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd
from constellations import legit, formation_clusters, independent

STEP, DAYS, LEG_EL = 10.0, 7, 10.0
SITES = [("Kenya", 0.0, 37.0), ("Texas coast", 28.0, -97.0), ("Fuji", 35.2, 138.8), ("Pampas", -35.0, -59.0), ("North Slope", 70.2, -148.3)]
SEEDS = 5
names, kin = legit("argos.tle"); jd0 = start_jd(kin)
t = np.arange(0, DAYS * 86400, STEP)
rek, _ = ecef_states(kin, jd0, t)


def stats(ok, legit_vis):
    allowed = ok & legit_vis
    frac = allowed.sum() / max(legit_vis.sum(), 1)
    idx = np.flatnonzero(allowed)
    gaps = np.diff(idx) * STEP / 3600 if idx.size > 1 else np.array([DAYS * 24.0])
    return dict(allowed_frac_of_legit=float(frac), allowed_min_per_day=float(allowed.sum() * STEP / 60 / DAYS),
                max_gap_h=float(gaps.max()), p95_gap_h=float(np.percentile(gaps, 95)))


out = {"assumptions": dict(step_s=STEP, days=DAYS, legit_min_el=LEG_EL, eav_min_el=0.0, seeds=SEEDS), "sites": {}}
configs = [("cluster", 1), ("cluster", 4), ("cluster", 10), ("indep", 2), ("indep", 6), ("indep", 12), ("both", (10, 12))]
eav_cache = {}
for seed in range(SEEDS):
    rng = np.random.default_rng(100 + seed)
    for kind, n in configs:
        if kind == "cluster":
            s, cid = formation_clusters(n, jd0, rng)
        elif kind == "indep":
            s = independent(n, jd0, rng); cid = np.arange(n) * 0  # one group: any two can pair
        else:
            s1, c1 = formation_clusters(n[0], jd0, rng); s2 = independent(n[1], jd0, rng)
            s, cid = s1 + s2, np.concatenate([c1, np.full(len(s2), -1)])
        re, _ = ecef_states(s, jd0, t)
        eav_cache[(seed, kind, str(n))] = (re, cid)

for name, la, lo in SITES:
    x = site_ecef(la, lo)
    legit_vis = (elevation_deg(rek, x) >= LEG_EL).any(0)
    site = {"legit_vis_min_per_day": float(legit_vis.sum() * STEP / 60 / DAYS)}
    for kind, n in configs:
        rows = []
        for seed in range(SEEDS):
            re, cid = eav_cache[(seed, kind, str(n))]
            vis = elevation_deg(re, x) >= 0.0
            # conservative: any two eavesdropper satellites in view can pair (one operator or colluding)
            danger = vis.sum(0) >= 2
            rows.append(stats(~danger, legit_vis))
        agg = {k: float(np.median([r[k] for r in rows])) for k in rows[0]}
        site[f"{kind}:{n}"] = agg
        print(f"{name:12s} {kind}:{n}  allowed {agg['allowed_frac_of_legit']*100:5.1f}% of legit time, "
              f"{agg['allowed_min_per_day']:6.1f} min/day, max gap {agg['max_gap_h']:5.1f} h", flush=True)
    print(name, "legit visible min/day", round(site["legit_vis_min_per_day"], 1))
    out["sites"][name] = site
json.dump(out, open("../results/s2_result.json", "w"), indent=1)
