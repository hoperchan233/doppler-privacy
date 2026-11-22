"""Scenario 8: operational ephemeris policy for layer 2 under T2 stress.
Policy: the tag receives eavesdropper elements every R days with 1 day latency (element age 1..R+1 days).
Along-track timing error tau_i(age) = k_i * age^2 (drag-dominated growth), with k_i drawn from the
quiescent satellites of Chen's real snapshot (fit k = tau(age_end) / age_end^2).  Satellites launched within
~3 months (REV_AT_EPOCH < 1500: HAWK-15*, HAWK-16*) may still manoeuvre (HAWK-15A/B: 160-600 s errors measured),
so they get a wide guard margin M_new; all others get M.  Truth = OMM.  Same metrics as s7."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd, load_tle
from constellations import legit_omm, hawkeye_omm

STEP, DAYS, LEG_EL, BUDGET, DRAWS = 20.0, 21, 10.0, 96, 10
GAMMA_L, D_TH, CAF_TH, BT = 10 ** 1.2, 6.0, 10 ** 1.3, 6e4
POLICIES = [(7, 60, 900), (7, 120, 1800), (14, 120, 1800), (30, 120, 1800)]   # (R days, M s, M_new s)
WINDOWS, DGS = (1, 7, 21), (10, 15)
SITES = [("Kenya", 0.0, 37.0), ("Fuji", 35.2, 138.8), ("North Slope", 70.2, -148.3)]
rng = np.random.default_rng(31)
_, kin = legit_omm("../data/kineis/kineis_latest_omm.json")
recs = json.load(open("../data/hawkeye/hawkeye360_latest_omm.json"))
hn, hs, _ = hawkeye_omm("../data/hawkeye/hawkeye360_latest_omm.json")
new = np.array([r["REV_AT_EPOCH"] < 1500 for r in recs])
tn, ts = load_tle("../data/hawkeye/hawkeye360_snapshot_2026-11.tle")
jd0 = start_jd(hs)
t = np.arange(0, DAYS * 86400, STEP); day = (t // 86400).astype(int)
rek, _ = ecef_states(kin, jd0, t)
reh, veh = ecef_states(hs, jd0, t)
# quiescent k_i from the real snapshot
ks = []
for nm, s in zip(tn, ts):
    if nm not in hn: continue
    i = hn.index(nm)
    if new[i] or (s.jdsatepoch + s.jdsatepochF) > (hs[i].jdsatepoch + hs[i].jdsatepochF) - 1: continue
    age_end = jd0 + 7 - (s.jdsatepoch + s.jdsatepochF)
    r2, _ = ecef_states([s], jd0, np.array([7 * 86400.0]))
    vn = veh[i, int(7 * 86400 / STEP)]; vn = vn / np.linalg.norm(vn)
    tau = (r2[0, 0] - reh[i, int(7 * 86400 / STEP)]) @ vn / 7.6
    ks.append(tau / age_end ** 2)
ks = np.array(ks)


def dilate1(v, m):
    k = int(round(m / STEP)); out = v.copy()
    for s in range(1, k + 1):
        out[s:] |= v[:-s]; out[:-s] |= v[s:]
    return out


out = {"assumptions": dict(k_s_per_day2=ks.round(3).tolist(), policies=POLICIES, new_sats=[n for n, f in zip(hn, new) if f]), "sites": {}}
for R, M, Mn in POLICIES:
    age = 1 + (t / 86400) % R                       # element age in days
    pred = np.empty_like(reh)
    for i in range(len(hs)):
        k = ks[rng.integers(len(ks))] * (3 if new[i] else 1)
        r2, _ = ecef_states([hs[i]], jd0, t + k * age ** 2)
        pred[i] = r2[0]
    for name, la, lo in SITES:
        x = site_ecef(la, lo)
        elk = elevation_deg(rek, x)
        rk = np.where(elk >= LEG_EL, np.linalg.norm(rek - x, axis=-1), np.inf)
        RL = rk.min(0); lv = np.isfinite(RL)
        ev_true = elevation_deg(reh, x) >= 0
        evp = elevation_deg(pred, x) >= 0
        evp = np.stack([dilate1(evp[i], Mn if new[i] else M) for i in range(len(hs))])
        allowed = lv & (evp.sum(0) < 2)
        leak = allowed & (ev_true.sum(0) >= 2)
        r_e = np.linalg.norm(reh - x, axis=-1)
        res = dict(allowed_min_per_day=float(allowed.sum() * STEP / 60 / DAYS),
                   leak_frac_of_allowed=float(leak.sum() / allowed.sum()),
                   max_gap_h=float(np.diff(np.flatnonzero(allowed)).max() * STEP / 3600), acc={})
        for dG in DGS:
            g = 10 ** (dG / 10)
            with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
                SE = np.nan_to_num(np.where(ev_true, GAMMA_L / BT * (RL[None] / r_e) ** 2 * g, 0.0), posinf=0.0)
            srt = np.sort(SE, 0); a, b = srt[-1], srt[-2]; rho = BT * a * b / (1 + a + b)
            dsing = np.sqrt(BT) * SE
            for W in WINDOWS:
                loc, det = [], []
                for start in range(0, DAYS - W + 1, W):
                    for _ in range(DRAWS):
                        kk = np.concatenate([rng.choice(np.flatnonzero(allowed & (day == dd)), BUDGET, replace=False)
                                             for dd in range(start, start + W)])
                        loc.append(np.sqrt((rho[kk] ** 2).sum()) >= CAF_TH)
                        det.append(np.sqrt((dsing[:, kk] ** 2).sum(1)).max() >= D_TH)
                res["acc"][f"dG{dG}_W{W}d"] = dict(pair_locate=float(np.mean(loc)), single_detect=float(np.mean(det)))
        out["sites"].setdefault(name, {})[f"R{R}_M{M}_Mnew{Mn}"] = res
        print(f"{name:11s} R={R:2d}d M={M:3d}s Mnew={Mn:4d}s allowed {res['allowed_min_per_day']:4.0f} min/d gap {res['max_gap_h']:.1f} h leak {res['leak_frac_of_allowed']*100:5.2f}% | "
              + " ".join(f"{k}:loc{v['pair_locate']*100:.0f}%/det{v['single_detect']*100:.0f}%" for k, v in res["acc"].items()), flush=True)
json.dump(out, open("../results/s8_result.json", "w"), indent=1)
