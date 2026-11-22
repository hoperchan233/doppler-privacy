"""Scenario 7: evidence-based T2 stress tests against the real HawkEye 360 constellation.

Truth: HawkEye OMM (epoch 2026-11-21).  Legit: fresh Kineis OMM (same epoch).
(a) Stale onboard ephemeris.  The tag schedules with older elements:
    - for the 20 satellites that appear in Chen's TLE snapshot (epochs 2026-08-30 ... 2026-11-16) it uses that snapshot;
    - for the others, a timing error tau(t) drawn from the errors measured on those 20 satellites
      (linear from tau(start) to tau(start+7 d)), the two orbit-raising HAWK-15A/B excluded from the draw.
    A guard margin M widens each predicted pass by +-M seconds.
(b) Stationary animal (e.g. incubation, ~3 weeks): the attacker accumulates 1, 7 or 21 days of leaked messages.
(c) Larger eavesdropper aperture: dG = 15 dB (about a 2 m reflector at 400 MHz vs Kineis' isoflux -4..+4 dBi) vs 10 dB.
(d) Constellation growth: +8 clusters, i.e. two years at the observed launch rate (4 clusters in 2024, 4 in 2026),
    assumed known to the tag (public catalogue), to measure the cost in allowed time."""
import json
import numpy as np
from orbit import site_ecef, ecef_states, elevation_deg, start_jd, load_tle
from constellations import legit_omm, hawkeye_omm, formation_clusters

STEP, DAYS, LEG_EL, BUDGET, DRAWS = 20.0, 21, 10.0, 96, 10
GAMMA_L, D_TH, CAF_TH, BT = 10 ** 1.2, 6.0, 10 ** 1.3, 6e4
MARGINS = (0, 30, 60, 120, 300)
WINDOWS = (1, 7, 21)
DGS = (10, 15)
SITES = [("Kenya", 0.0, 37.0), ("Fuji", 35.2, 138.8), ("North Slope", 70.2, -148.3)]
rng = np.random.default_rng(13)

_, kin = legit_omm("../data/kineis/kineis_latest_omm.json")
hn, hs, _ = hawkeye_omm("../data/hawkeye/hawkeye360_latest_omm.json")
tn, ts = load_tle("../data/hawkeye/hawkeye360_snapshot_2026-11.tle")
jd0 = start_jd(hs)
t = np.arange(0, DAYS * 86400, STEP); day = (t // 86400).astype(int)
rek, _ = ecef_states(kin, jd0, t)
reh, veh = ecef_states(hs, jd0, t)

# --- measured staleness of the snapshot satellites (timing error, s) ---
meas = []
pred = np.empty_like(reh)
have = np.zeros(len(hs), bool)
for nm, s in zip(tn, ts):
    if nm not in hn:
        continue
    i = hn.index(nm)
    if (s.jdsatepoch + s.jdsatepochF) > (hs[i].jdsatepoch + hs[i].jdsatepochF) - 1:
        continue                                    # same element set: not stale
    r2, _ = ecef_states([s], jd0, t)
    pred[i] = r2[0]; have[i] = True
    vn = veh[i] / np.linalg.norm(veh[i], axis=-1, keepdims=True)
    at = np.einsum("ij,ij->i", r2[0] - reh[i], vn) / 7.6
    k7 = int(7 * 86400 / STEP)
    if nm not in ("HAWK-15A", "HAWK-15B"):
        meas.append((at[0], at[k7]))
meas = np.array(meas)
for i in np.flatnonzero(~have):                      # emulate staleness for the others
    a0, a7 = meas[rng.integers(len(meas))]
    tau = a0 + (a7 - a0) * t / (7 * 86400)
    r2, _ = ecef_states([hs[i]], jd0, t + tau)
    pred[i] = r2[0]
growth, _ = formation_clusters(8, jd0, np.random.default_rng(77), alt_km=530.0)
reg, _ = ecef_states(growth, jd0, t)


def dilate(v, m):
    k = int(round(m / STEP))
    if k == 0:
        return v
    out = v.copy()
    for s in range(1, k + 1):
        out[:, s:] |= v[:, :-s]; out[:, :-s] |= v[:, s:]
    return out


out = {"assumptions": dict(days=DAYS, step_s=STEP, budget=BUDGET, bt=BT, gamma_l_db=12,
                           n_stale_snapshot=int(have.sum()), measured_timing_err_s=meas.round(1).tolist(),
                           growth_clusters=8), "sites": {}}
for name, la, lo in SITES:
    x = site_ecef(la, lo)
    elk = elevation_deg(rek, x)
    rk = np.where(elk >= LEG_EL, np.linalg.norm(rek - x, axis=-1), np.inf)
    RL = rk.min(0); lv = np.isfinite(RL)
    ev_true = elevation_deg(reh, x) >= 0
    ev_pred = elevation_deg(pred, x) >= 0
    r_e = np.linalg.norm(reh - x, axis=-1)
    site = {"legit_min_per_day": float(lv.sum() * STEP / 60 / DAYS)}
    # (d) growth: capacity only (fresh, known elements)
    ev_g = np.concatenate([ev_true, elevation_deg(reg, x) >= 0])
    allowed_g = lv & (ev_g.sum(0) < 2)
    site["growth_+8_clusters"] = dict(allowed_min_per_day=float(allowed_g.sum() * STEP / 60 / DAYS),
                                      max_gap_h=float(np.diff(np.flatnonzero(allowed_g)).max() * STEP / 3600))
    rho_by_dg = {}
    for dG in DGS:
        g = 10 ** (dG / 10)
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
            SE = np.nan_to_num(np.where(ev_true, GAMMA_L / BT * (RL[None] / r_e) ** 2 * g, 0.0), posinf=0.0)
        srt = np.sort(SE, 0); a, b = srt[-1], srt[-2]
        rho_by_dg[dG] = (BT * a * b / (1 + a + b), np.sqrt(BT) * SE)
    for label, evp in (("fresh", ev_true), ("stale", ev_pred)):
        for M in (MARGINS if label == "stale" else (0,)):
            allowed = lv & (dilate(evp, M).sum(0) < 2)
            leak = allowed & (ev_true.sum(0) >= 2)
            res = dict(allowed_min_per_day=float(allowed.sum() * STEP / 60 / DAYS),
                       leak_frac_of_allowed=float(leak.sum() / max(allowed.sum(), 1)), acc={})
            for dG in DGS:
                rho, dsing = rho_by_dg[dG]
                for W in WINDOWS:
                    loc, det = [], []
                    for start in range(0, DAYS - W + 1, max(1, W)):
                        for _ in range(DRAWS):
                            ks = []
                            for dd in range(start, start + W):
                                ii = np.flatnonzero(allowed & (day == dd))
                                ks.append(rng.choice(ii, min(BUDGET, ii.size), replace=False))
                            k = np.concatenate(ks)
                            loc.append(np.sqrt((rho[k] ** 2).sum()) >= CAF_TH)
                            det.append(np.sqrt((dsing[:, k] ** 2).sum(1)).max() >= D_TH)
                    res["acc"][f"dG{dG}_W{W}d"] = dict(pair_locate=float(np.mean(loc)), single_detect=float(np.mean(det)))
            site[f"{label}_M{M}"] = res
            print(f"{name:11s} {label:5s} M={M:3d}s allowed {res['allowed_min_per_day']:5.0f} min/d leak {res['leak_frac_of_allowed']*100:5.2f}% | "
                  + " ".join(f"{k}:loc{v['pair_locate']*100:.0f}%" for k, v in res["acc"].items()), flush=True)
    print(f"{name:11s} growth +8 clusters: allowed {site['growth_+8_clusters']['allowed_min_per_day']:.0f} min/d, max gap {site['growth_+8_clusters']['max_gap_h']:.1f} h")
    out["sites"][name] = site
json.dump(out, open("../results/s7_result.json", "w"), indent=1)
