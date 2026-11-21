"""Legitimate (Kineis, real TLE) and synthetic eavesdropper constellations."""
import math
import numpy as np
from sgp4.api import Satrec, WGS72
from orbit import load_tle, RE_KM

MU = 398600.4418


def legit(path):
    return load_tle(path, ["KINEIS"])


def _sat(num, epoch_jd, alt_km, inc_deg, raan_deg, ma_deg):
    a = RE_KM + alt_km
    n_rad_min = math.sqrt(MU / a**3) * 60.0
    s = Satrec()
    s.sgp4init(WGS72, "i", num, epoch_jd - 2433281.5, 0.0, 0.0, 0.0, 1e-4, 0.0,
               math.radians(inc_deg), math.radians(ma_deg % 360), n_rad_min, math.radians(raan_deg % 360))
    return s


def sso_inc(alt_km):
    a = RE_KM + alt_km
    # nodal precession = 360 deg / tropical year
    J2 = 1.08263e-3
    n = math.sqrt(MU / a**3)
    rate = 2 * math.pi / (365.2422 * 86400)
    return math.degrees(math.acos(-rate / (1.5 * n * J2 * (RE_KM / a) ** 2)))


def formation_clusters(n_clusters, epoch_jd, rng, alt_km=575.0, spacing_km=125.0):
    """HawkEye-360-like: 3 satellites per cluster, same plane, spacing_km along track (eoPortal)."""
    inc = sso_inc(alt_km)
    dma = math.degrees(spacing_km / (RE_KM + alt_km))
    sats, cid = [], []
    for c in range(n_clusters):
        raan = rng.uniform(0, 360)
        ma = rng.uniform(0, 360)
        for k in range(3):
            sats.append(_sat(90000 + 3 * c + k, epoch_jd, alt_km, inc, raan, ma + k * dma))
            cid.append(c)
    return sats, np.array(cid)


def independent(n, epoch_jd, rng, alt_km=550.0):
    """Independent eavesdroppers in different planes (mixed 53/70/97.6 deg inclinations)."""
    incs = [53.0, 70.0, sso_inc(alt_km)]
    return [_sat(95000 + i, epoch_jd, alt_km, incs[i % 3], rng.uniform(0, 360), rng.uniform(0, 360))
            for i in range(n)]
