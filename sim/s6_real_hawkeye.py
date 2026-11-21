"""Scenario 6: layers 2 and 3 against the REAL HawkEye 360 constellation (46 satellites incl. KESTREL-0A,
CelesTrak OMM, epoch 2026-11-21), alone and together with 12 synthetic independent eavesdroppers.
Simulation starts at the first UTC midnight after the newest HawkEye epoch; Kineis TLEs (epoch ~2026-10-01)
are propagated ~50 days forward, so Kineis phasing is statistically, not exactly, representative."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd
from constellations import legit, independent, hawkeye_omm

STEP, DAYS, LEG_EL = 20.0, 7, 10.0
BUDGET, DRAWS = 96, 20
GAMMA_L, D_TH, CAF_TH, BT = 10 ** 1.2, 6.0, 10 ** 1.3, 6e4
DGS = (0, 5, 10, 15, 20)
SITES = [("Kenya", 0.0, 37.0), ("Texas coast", 28.0, -97.0), ("Fuji", 35.2, 138.8), ("Pampas", -35.0, -59.0), ("North Slope", 70.2, -148.3)]
rng = np.random.default_rng(9)
_, kin = legit("argos.tle")
hn, hs, hc = hawkeye_omm("../data/hawkeye/hawkeye360_latest_omm.json")
jd0 = start_jd(hs)
t = np.arange(0, DAYS * 86400, STEP); day = (t // 86400).astype(int)
rek, _ = ecef_states(kin, jd0, t)
reh, _ = ecef_states(hs, jd0, t)
rei, _ = ecef_states(independent(12, jd0, np.random.default_rng(100)), jd0, t)
CONFIGS = {"hawkeye_real": reh, "hawkeye_real+12indep": np.concatenate([reh, rei])}

out = {"assumptions": dict(n_hawkeye=len(hs), start_jd=jd0, days=DAYS, step_s=STEP, legit_min_el=LEG_EL,
                           eav_min_el=0.0, danger="any two eavesdropper satellites in view", budget=BUDGET,
                           bt=BT, gamma_l_db=12, power="adaptive"), "sites": {}}
for name, la, lo in SITES:
    x = site_ecef(la, lo)
    elk = elevation_deg(rek, x)
    rk = np.where(elk >= LEG_EL, np.linalg.norm(rek - x, axis=-1), np.inf)
    RL = rk.min(0); lv = np.isfinite(RL)
    site = {"legit_min_per_day": float(lv.sum() * STEP / 60 / DAYS)}
    for cname, ree in CONFIGS.items():
        ev = elevation_deg(ree, x) >= 0
        n_in_view = ev.sum(0)
        danger = n_in_view >= 2
        allowed = lv & ~danger
        idx = np.flatnonzero(allowed)
        gaps = np.diff(idx) * STEP / 3600
        res = dict(frac_legit_time_ge1_eav=float((n_in_view[lv] >= 1).mean()),
                   frac_legit_time_ge2_eav=float(danger[lv].mean()),
                   allowed_min_per_day=float(allowed.sum() * STEP / 60 / DAYS),
                   allowed_frac_of_legit=float(allowed.sum() / lv.sum()),
                   max_gap_h=float(gaps.max()), p95_gap_h=float(np.percentile(gaps, 95)), l3={})
        r_e = np.linalg.norm(ree - x, axis=-1)
        for dG in DGS:
            g = 10 ** (dG / 10)
            with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
                SE = np.nan_to_num(np.where(ev, GAMMA_L / BT * (RL[None] / r_e) ** 2 * g, 0.0), posinf=0.0)
            d = np.sqrt(BT) * SE
            srt = np.sort(SE, 0); a, b = srt[-1], srt[-2]
            rho = BT * a * b / (1 + a + b)
            row = {}
            for mode, mask in (("unscheduled", lv), ("scheduled", allowed)):
                det, loc = [], []
                for dd in range(DAYS):
                    ii = np.flatnonzero(mask & (day == dd))
                    for _ in range(DRAWS):
                        k = rng.choice(ii, min(BUDGET, ii.size), replace=False)
                        det.append(np.sqrt((d[:, k] ** 2).sum(1)).max() >= D_TH)
                        loc.append(np.sqrt((rho[k] ** 2).sum()) >= CAF_TH)
                row[mode] = dict(day_detect=float(np.mean(det)), day_locate=float(np.mean(loc)))
            res["l3"][dG] = row
        site[cname] = res
        print(f"{name:12s} {cname:22s} >=1 eav {res['frac_legit_time_ge1_eav']*100:4.0f}%  >=2 eav {res['frac_legit_time_ge2_eav']*100:4.0f}%  "
              f"allowed {res['allowed_min_per_day']:5.0f} min/day ({res['allowed_frac_of_legit']*100:4.0f}%) maxgap {res['max_gap_h']:.1f} h | "
              + " ".join(f"dG{g}: U-loc{r['unscheduled']['day_locate']*100:.0f}% S-loc{r['scheduled']['day_locate']*100:.0f}% S-det{r['scheduled']['day_detect']*100:.0f}%" for g, r in res["l3"].items()), flush=True)
    out["sites"][name] = site
json.dump(out, open("../results/s6_result.json", "w"), indent=1)
