from __future__ import annotations

import os
from datetime import datetime
import numpy as np

BAND_ASSETS = ["B02", "B03", "B04", "B8A", "B11", "B12"]  # Blue, Green, Red, NIR, SWIR1, SWIR2


def fetch_hls_tile(lat: float, lon: float, buffer_deg: float = 0.05) -> dict:
    """
    Fetch the most recent cloud-free HLS Sentinel-2 tile for a given lat/lon.
    Returns band arrays (6, H, W) normalised to [0, 1] plus derived indices.

    Falls back to realistic synthetic data when USE_MOCK_NASA=true or when
    rioxarray/GDAL is not installed (set env var to skip the real API call).
    """
    if os.getenv("USE_MOCK_NASA", "false").lower() == "true":
        return _mock_tile(lat, lon)

    try:
        import earthaccess
        import rioxarray  # requires GDAL / rasterio
    except ImportError as exc:
        missing = str(exc).split("'")[1]
        raise ImportError(
            f"'{missing}' is not installed. Either `pip install rioxarray rasterio` "
            f"(needs system GDAL) or set USE_MOCK_NASA=true for synthetic data."
        ) from exc

    earthaccess.login(strategy="environment")
    bbox = (lon - buffer_deg, lat - buffer_deg, lon + buffer_deg, lat + buffer_deg)

    results = earthaccess.search_data(short_name="HLSS30", bounding_box=bbox, count=10)
    if not results:
        raise ValueError(f"No HLS tiles found near ({lat:.4f}, {lon:.4f})")

    clear = [r for r in results if r.get("umm", {}).get("CloudCover", 100) < 20]
    if not clear:
        raise ValueError(f"No cloud-free (<20%) HLS tiles found near ({lat:.4f}, {lon:.4f})")

    best = clear[0]
    file_links = earthaccess.open([best])

    bands = []
    for link in file_links[: len(BAND_ASSETS)]:
        da = rioxarray.open_rasterio(link, masked=True).squeeze()
        bands.append(da.values.astype(np.float32))

    data = np.stack(bands, axis=0)
    data = np.clip(data / 10_000.0, 0.0, 1.0)

    nir, red, green = data[3], data[2], data[1]
    ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), 0.0)
    ndwi = np.where((green + nir) > 0, (green - nir) / (green + nir), 0.0)

    umm = best.get("umm", {})
    acquisition_date = (
        umm.get("TemporalExtent", {}).get("RangeDateTime", {}).get("EndingDateTime", "unknown")
    )
    return {
        "bands": data,
        "ndvi_mean": float(ndvi.mean()),
        "ndwi_mean": float(ndwi.mean()),
        "acquisition_date": acquisition_date,
        "tile_id": best["meta"].get("concept-id", "unknown"),
        "cloud_cover": umm.get("CloudCover"),
    }


def _mock_tile(lat: float, lon: float) -> dict:
    """Synthetic HLS data representative of semi-arid agricultural land."""
    rng = np.random.default_rng(seed=int(abs(lat * 1000 + lon * 100)))
    H, W = 64, 64

    # Pre-monsoon Punjab cropland — partly harvested wheat, bare soil patches
    # Typical NDVI range 0.15–0.35 for this season/region
    blue  = rng.normal(0.08, 0.01, (H, W)).clip(0, 1).astype(np.float32)
    green = rng.normal(0.12, 0.01, (H, W)).clip(0, 1).astype(np.float32)
    red   = rng.normal(0.14, 0.02, (H, W)).clip(0, 1).astype(np.float32)
    nir   = rng.normal(0.28, 0.04, (H, W)).clip(0, 1).astype(np.float32)
    swir1 = rng.normal(0.22, 0.03, (H, W)).clip(0, 1).astype(np.float32)
    swir2 = rng.normal(0.15, 0.02, (H, W)).clip(0, 1).astype(np.float32)

    data = np.stack([blue, green, red, nir, swir1, swir2], axis=0)
    ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), 0.0)
    ndwi = np.where((green + nir) > 0, (green - nir) / (green + nir), 0.0)

    return {
        "bands": data,
        "ndvi_mean": float(ndvi.mean()),
        "ndwi_mean": float(ndwi.mean()),
        "acquisition_date": datetime.now().strftime("%Y-%m-%dT00:00:00Z") + " (mock)",
        "tile_id": f"MOCK-{lat:.2f}-{lon:.2f}",
        "cloud_cover": 5,
    }
