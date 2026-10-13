"""Tree cover loss: real data from Global Forest Watch (UMD/Hansen) with simulated fallback,
plus statistical analysis (trend, anomalies, projection)."""
import math
import time

import numpy as np
import requests

from .. import config

YEARS = list(range(2001, 2024))
_cache = {"ts": 0, "data": None}
CACHE_SEC = 3600


def circle_polygon(lat, lon, radius_km, n=48):
    """GeoJSON polygon approximating a circle."""
    pts = []
    for i in range(n + 1):
        a = 2 * math.pi * i / n
        dlat = (radius_km / 111.32) * math.cos(a)
        dlon = (radius_km / (111.32 * math.cos(math.radians(lat)))) * math.sin(a)
        pts.append([lon + dlon, lat + dlat])
    return {"type": "Polygon", "coordinates": [pts]}


def fetch_gfw_loss(lat, lon, radius_km):
    """Annual tree cover loss (ha) inside the circle from GFW Data API. Needs GFW_API_KEY."""
    if not config.GFW_API_KEY:
        raise RuntimeError("GFW_API_KEY not set")
    url = "https://data-api.globalforestwatch.org/dataset/umd_tree_cover_loss/latest/query/json"
    body = {
        "sql": "SELECT umd_tree_cover_loss__year, SUM(area__ha) FROM results "
               "GROUP BY umd_tree_cover_loss__year",
        "geometry": circle_polygon(lat, lon, radius_km),
    }
    r = requests.post(url, json=body, timeout=60,
                      headers={"x-api-key": config.GFW_API_KEY})
    r.raise_for_status()
    rows = r.json().get("data", [])
    loss = {}
    for row in rows:
        year = row.get("umd_tree_cover_loss__year")
        vals = [v for k, v in row.items() if k != "umd_tree_cover_loss__year"
                and isinstance(v, (int, float))]
        if year and vals:
            loss[int(year)] = float(vals[0])
    if not loss:
        raise RuntimeError("GFW returned no rows")
    return [round(loss.get(y, 0.0), 2) for y in YEARS]


def simulate_loss(lat, lon, radius_km, seed=42):
    """Statistically plausible simulated series: slow upward trend + noise + storm spikes."""
    rng = np.random.default_rng(seed)
    area_ha = math.pi * radius_km ** 2 * 100
    base = area_ha * 0.0012
    trend = np.linspace(0, base * 0.8, len(YEARS))
    noise = rng.normal(0, base * 0.15, len(YEARS))
    series = base + trend + noise
    for storm_year, factor in ((2009, 2.4), (2020, 2.9)):  # cyclone-like spikes
        series[YEARS.index(storm_year)] *= factor
    return [round(max(v, 0), 2) for v in series]


def simulate_hotspots(lat, lon, radius_km, n=250, seed=7):
    """Simulated spatial loss hotspots (lat, lon, intensity) clustered in 4 zones."""
    rng = np.random.default_rng(seed)
    deg = radius_km / 111.32
    centers = rng.uniform(-0.6, 0.6, size=(4, 2)) * deg
    pts = []
    for i in range(n):
        c = centers[i % 4]
        dy, dx = rng.normal(c, deg * 0.12)
        pts.append([round(lat + dy, 5),
                    round(lon + dx / math.cos(math.radians(lat)), 5),
                    round(float(rng.uniform(0.3, 1.0)), 2)])
    return pts


def analyze(series):
    arr = np.array(series, dtype=float)
    years = np.array(YEARS)
    slope, intercept = np.polyfit(years, arr, 1)
    mean, std = arr.mean(), arr.std(ddof=1)
    z = (arr - mean) / std if std > 0 else np.zeros_like(arr)
    last5, prev5 = arr[-5:].mean(), arr[-10:-5].mean()
    return {
        "total_loss_ha": round(float(arr.sum()), 1),
        "mean_annual_ha": round(float(mean), 1),
        "std_ha": round(float(std), 1),
        "trend_ha_per_year": round(float(slope), 2),
        "trend_direction": "increasing" if slope > 0 else "decreasing",
        "anomaly_years": [int(y) for y, s in zip(years, z) if s >= 2],
        "z_scores": [round(float(s), 2) for s in z],
        "last5_vs_prev5_pct": round(float((last5 - prev5) / prev5 * 100), 1) if prev5 else None,
        "projected_next_year_ha": round(float(slope * (YEARS[-1] + 1) + intercept), 1),
        "worst_year": int(years[int(arr.argmax())]),
    }


def get_forest_data(force=False):
    if not force and _cache["data"] and time.time() - _cache["ts"] < CACHE_SEC:
        return _cache["data"]
    lat, lon, r = config.CENTER_LAT, config.CENTER_LON, config.RADIUS_KM
    try:
        series = fetch_gfw_loss(lat, lon, r)
        source = "Global Forest Watch (UMD/Hansen) - real"
        error = None
    except Exception as e:  # noqa: BLE001
        series = simulate_loss(lat, lon, r)
        source = "Simulated statistical data"
        error = str(e)
    data = {
        "center": [lat, lon],
        "radius_km": r,
        "source": source,
        "fallback_reason": error,
        "years": YEARS,
        "loss_ha": series,
        "stats": analyze(series),
        "hotspots": simulate_hotspots(lat, lon, r),
        "hotspots_source": "Simulated",
    }
    _cache.update(ts=time.time(), data=data)
    return data
