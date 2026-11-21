"""Scenario 5: layer 3 against an eavesdropper that accumulates a whole day of messages non-coherently.
The tag sends BUDGET messages/day in random allowed slots (Kineis in view; optionally TLE-scheduled).
Per message: energy-detector deflection d_k = sqrt(BT) S_k, best-pair CAF SNR rho_k (as s3_lpd.py).
Day statistics (attacker-optimistic, ideal alignment): sqrt(sum d_k^2) >= D_TH, sqrt(sum rho_k^2) >= CAF_TH."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd
from constellations import legit, formation_clusters, independent

STEP, DAYS, LEG_EL, BUDGET, DRAWS = 20.0, 7, 10.0, 96, 20
GAMMA_L, D_TH, CAF_TH, BT = 10 ** 1.2, 6.0, 10 ** 1.3, 6e4
DGS = np.arange(0, 31, 5)
SITES = [("Kenya", 0.0, 37.0), ("Fuji", 35.2, 138.8), ("North Slope", 70.2, -148.3)]
rng = np.random.default_rng(5)
names, kin = legit("argos.tle"); jd0 = start_jd(kin)
t = np.arange(0, DAYS * 86400, STEP)
rek, _ = ecef_states(kin, jd0, t)
r0 = np.random.default_rng(100)
s1, c1 = formation_clusters(10, jd0, r0); s2 = independent(12, jd0, r0)
ree, _ = ecef_states(s1 + s2, jd0, t)
cid = np.concatenate([c1, np.full(len(s2), -1)])
day = (t // 86400).astype(int)
out = {"assumptions": dict(budget=BUDGET, bt=BT, gamma_l_db=12, d_th=D_TH, caf_th_db=13, power="adaptive",
                           note="attacker-optimistic ideal non-coherent accumulation over one day"), "sites": {}}
for name, la, lo in SITES:
    x = site_ecef(la, lo)
    elk = elevation_deg(rek, x); rk = np.where(elk >= LEG_EL, np.linalg.norm(rek - x, axis=-1), np.inf)
    RL = rk.min(0); lv = np.isfinite(RL)
    ele = elevation_deg(ree, x); r_e = np.linalg.norm(ree - x, axis=-1); ev = ele >= 0
    danger = ev.sum(0) >= 2   # any two eavesdroppers in view can pair
    SL = GAMMA_L / BT
    site = {}
    for sched in ("unscheduled", "scheduled"):
        allowed = lv & (~danger if sched == "scheduled" else True)
        rows = {}
        for dG in DGS:
            gg = 10 ** (dG / 10)
            with np.errstate(invalid="ignore", divide="ignore"):
                SE = np.where(ev, SL * (RL[None] / r_e) ** 2 * gg, 0.0)
            SE = np.nan_to_num(SE)
            d = np.sqrt(BT) * SE                                   # per eavesdropper
            srt = np.sort(SE, 0); a, b = srt[-1], srt[-2]
            rho = BT * a * b / (1 + a + b)
            det, loc, det1, loc1 = [], [], [], []
            for dd in range(DAYS):
                idx = np.flatnonzero(allowed & (day == dd))
                for _ in range(DRAWS):
                    k = rng.choice(idx, min(BUDGET, idx.size), replace=False)
                    det.append(np.sqrt((d[:, k] ** 2).sum(1)).max() >= D_TH)
                    loc.append(np.sqrt((rho[k] ** 2).sum()) >= CAF_TH)
                    det1.append((d[:, k] >= D_TH).any())
                    loc1.append((rho[k] >= CAF_TH).any())
            rows[int(dG)] = dict(day_detect=float(np.mean(det)), day_locate=float(np.mean(loc)),
                                 any_single_msg_detect=float(np.mean(det1)), any_single_msg_locate=float(np.mean(loc1)))
        site[sched] = rows
        print(name, sched, " ".join(f"dG{g}: det{r['day_detect']*100:.0f}% loc{r['day_locate']*100:.0f}%" for g, r in rows.items()), flush=True)
    out["sites"][name] = site
json.dump(out, open("../results/s5_result.json", "w"), indent=1)
