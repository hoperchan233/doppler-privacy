"""Shared orbit helpers: TLE loading, Earth-fixed satellite state, site geometry."""
import math
import numpy as np
from sgp4.api import Satrec, SatrecArray

C_KM_S = 299792.458
F0_HZ = 401.65e6
RE_KM = 6378.137
WE = 7.2921150e-5  # Earth rotation, rad/s


def load_tle(path, names=None):
    """Return (names, satrecs).  `names` keeps only satellites whose name starts with one of them."""
    L = [l.rstrip() for l in open(path) if l.strip()]
    out_n, out_s = [], []
    for i in range(0, len(L) - 2, 3):
        if not L[i + 1].startswith("1 "):
            continue
        nm = L[i].strip()
        if names and not any(nm.startswith(n) for n in names):
            continue
        out_n.append(nm)
        out_s.append(Satrec.twoline2rv(L[i + 1], L[i + 2]))
    return out_n, out_s


def start_jd(sats):
    """First UTC midnight after the newest TLE epoch."""
    newest = max(s.jdsatepoch + s.jdsatepochF for s in sats)
    return math.floor(newest - 0.5) + 1.5


def gmst(jd):
    t = (jd - 2451545.0) / 36525.0
    sec = 67310.54841 + (876600 * 3600 + 8640184.812866) * t + 0.093104 * t**2 - 6.2e-6 * t**3
    return np.radians((sec % 86400) / 240.0)


def site_ecef(lat, lon):
    f = 1 / 298.257223563
    e2 = f * (2 - f)
    la, lo = np.radians(lat), np.radians(lon)
    n = RE_KM / np.sqrt(1 - e2 * np.sin(la) ** 2)
    return np.stack([n * np.cos(la) * np.cos(lo), n * np.cos(la) * np.sin(lo), n * (1 - e2) * np.sin(la)], -1)


def ecef_states(sats, jd0, t_s):
    """Earth-fixed position (km) and velocity (km/s) of every satellite at times t_s (s after jd0).
    Shapes: (n_sat, n_t, 3).  The velocity is relative to the rotating Earth."""
    t_s = np.atleast_1d(np.asarray(t_s, dtype=float))
    jd = np.full(t_s.size, jd0)
    fr = t_s / 86400.0
    err, r, v = SatrecArray(sats).sgp4(jd, fr)
    g = gmst(jd + fr)
    c, s = np.cos(g), np.sin(g)
    rot = lambda a: np.stack([c * a[..., 0] + s * a[..., 1], -s * a[..., 0] + c * a[..., 1], a[..., 2]], -1)
    re, ve = rot(r), rot(v)
    ve = ve - np.cross(np.array([0.0, 0.0, WE]), re)
    re[err != 0] = np.nan
    return re, ve


def elevation_deg(re, x):
    d = re - x
    up = x / np.linalg.norm(x)
    return np.degrees(np.arcsin((d @ up) / np.linalg.norm(d, axis=-1)))


def range_rate(re, ve, x):
    d = re - x
    return np.einsum("...k,...k->...", d, ve) / np.linalg.norm(d, axis=-1)


def received_freq(f_t, re, ve, x):
    return f_t * (1 - range_rate(re, ve, x) / C_KM_S)


def haversine_km(a1, o1, a2, o2):
    a1, o1, a2, o2 = map(np.radians, (a1, o1, a2, o2))
    h = np.sin((a2 - a1) / 2) ** 2 + np.cos(a1) * np.cos(a2) * np.sin((o2 - o1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(h))


def offset(lat, lon, dist_km, bearing):
    d = dist_km / 6371.0
    la, lo = math.radians(lat), math.radians(lon)
    la2 = math.asin(math.sin(la) * math.cos(d) + math.cos(la) * math.sin(d) * math.cos(bearing))
    lo2 = lo + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(la), math.cos(d) - math.sin(la) * math.sin(la2))
    return math.degrees(la2), math.degrees(lo2)


def passes(el, step_s, min_el=0.0, min_len_s=60.0):
    """Contiguous visibility segments per satellite: list of (sat_index, t_start_s, t_end_s)."""
    out = []
    for i in range(el.shape[0]):
        vis = el[i] > min_el
        if not vis.any():
            continue
        idx = np.flatnonzero(vis)
        for seg in np.split(idx, np.flatnonzero(np.diff(idx) > 1) + 1):
            t0, t1 = seg[0] * step_s, seg[-1] * step_s
            if t1 - t0 >= min_len_s:
                out.append((i, t0, t1))
    return out
