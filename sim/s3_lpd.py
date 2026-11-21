"""Scenario 3: LPD (keyed DSSS) + elevation-aware power control against eavesdroppers.
Legit receiver despreads: output SNR = BT * S_L.  Tag sets power so BT*S_L = GAMMA_L (adaptive), or for the
worst-case legit range at 10 deg elevation (fixed).  An eavesdropper with antenna/G-T advantage dG receives
S_E = S_L (R_L/R_E)^2 dG.  Single eavesdropper (energy detector): deflection sqrt(BT)*S_E >= D_TH.
Pair (cross-ambiguity, TDOA/FDOA): output SNR BT*S1*S2/(1+S1+S2) >= CAF_TH."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd
from constellations import legit, formation_clusters, independent

STEP, DAYS, LEG_EL = 20.0, 3, 10.0
GAMMA_L = 10 ** 1.2      # 12 dB legit post-despreading SNR
D_TH = 6.0               # energy-detector deflection for Pfa 1e-6 / Pd 0.9
CAF_TH = 10 ** 1.3       # 13 dB CAF peak SNR needed to detect + measure TDOA/FDOA
BTS = {"BT=6e4 (60 kHz x 1 s)": 6e4, "BT=6e3 (6 kHz x 1 s)": 6e3}
DGS = np.arange(0, 41, 5)
SITES = [("Kenya", 0.0, 37.0), ("Fuji", 35.2, 138.8), ("North Slope", 70.2, -148.3)]

names, kin = legit("argos.tle"); jd0 = start_jd(kin)
t = np.arange(0, DAYS * 86400, STEP)
rek, _ = ecef_states(kin, jd0, t)
rng = np.random.default_rng(100)
s1, c1 = formation_clusters(10, jd0, rng); s2 = independent(12, jd0, rng)
ree, _ = ecef_states(s1 + s2, jd0, t)
cid = np.concatenate([c1, np.full(len(s2), -1)])

out = {"assumptions": dict(gamma_l_db=12, d_th=D_TH, caf_th_db=13, eav="10 formation clusters + 12 independent",
                           days=DAYS, step_s=STEP), "sites": {}}
for name, la, lo in SITES:
    x = site_ecef(la, lo)
    elk = elevation_deg(rek, x); rk = np.linalg.norm(rek - x, axis=-1)
    ele = elevation_deg(ree, x); r_e = np.linalg.norm(ree - x, axis=-1)
    lv = (elk >= LEG_EL).any(0)
    rk_m = np.where(elk >= LEG_EL, rk, np.inf)
    RL = rk_m.min(0)                                   # best (closest) legit satellite
    RL_worst = rk[elk >= LEG_EL].max()                 # legit range at ~10 deg
    ev = ele >= 0.0
    # scheduled = no eavesdropper pair in view (scenario 2 rule)
    danger = ev.sum(0) >= 2   # any two eavesdroppers in view can pair
    site = {"range_ratio_note": f"legit range best median {np.median(RL[lv]):.0f} km, worst {RL_worst:.0f} km"}
    for btn, BT in BTS.items():
        for mode in ("adaptive", "fixed"):
            SL = GAMMA_L / BT * (np.ones_like(RL) if mode == "adaptive" else (RL / RL_worst) ** -2)
            rows = {}
            for dG in DGS:
                g = 10 ** (dG / 10)
                SE = np.where(ev, SL[None] * (RL[None] / r_e) ** 2 * g, 0.0)   # (n_eav, n_t)
                det_any = (np.sqrt(BT) * SE >= D_TH).any(0)
                # best pair (two largest S among eavesdroppers that may pair: conservative, any two)
                srt = np.sort(SE, axis=0)
                a, b = srt[-1], srt[-2]
                caf = BT * a * b / (1 + a + b)
                loc = caf >= CAF_TH
                m_all, m_sch = lv, lv & ~danger
                rows[int(dG)] = dict(
                    detect_unsched=float(det_any[m_all].mean()), locate_unsched=float(loc[m_all].mean()),
                    detect_sched=float(det_any[m_sch].mean()), locate_sched=float(loc[m_sch].mean()))
            site[f"{btn}|{mode}"] = rows
            print(name, btn, mode, " ".join(f"dG{d}:det{r['detect_sched']*100:.0f}%/loc{r['locate_unsched']*100:.0f}%" for d, r in rows.items()), flush=True)
    out["sites"][name] = site
json.dump(out, open("../results/s3_result.json", "w"), indent=1)
