import numpy as np


def analyze_land(band_array: np.ndarray) -> dict:
    """
    Classify land cover and derive moisture index from 6-band HLS data.
    band_array: (6, H, W) float32 in [0, 1] — bands B02, B03, B04, B8A, B11, B12.

    Uses spectral indices as a lightweight proxy for the full Prithvi-100M pipeline.
    To use the actual model, replace this function with an HF Inference API call:
      POST https://api-inference.huggingface.co/models/ibm-nasa-geospatial/Prithvi-100M
      Authorization: Bearer <HUGGINGFACE_TOKEN>
      Body: {"inputs": {"data": band_array.tolist()}}   # (T=1, C=6, H, W)
    """
    blue, green, red, nir, swir1, swir2 = band_array

    ndvi = np.where((nir + red) > 0, (nir - red) / (nir + red), 0.0)
    ndwi = np.where((green + nir) > 0, (green - nir) / (green + nir), 0.0)
    ndbi = np.where((swir1 + nir) > 0, (swir1 - nir) / (swir1 + nir), 0.0)

    mean_ndvi = float(ndvi.mean())
    mean_ndwi = float(ndwi.mean())
    mean_ndbi = float(ndbi.mean())

    if mean_ndwi > 0.30:
        land_type = "Water Body"
    elif mean_ndvi > 0.55:
        land_type = "Dense Vegetation / Forest"
    elif mean_ndvi > 0.25:
        land_type = "Agricultural Land"
    elif mean_ndvi > 0.10:
        land_type = "Sparse Vegetation / Rangeland"
    elif mean_ndbi > 0.20:
        land_type = "Urban / Built-up"
    else:
        land_type = "Bare Soil / Degraded Land"

    # Moisture proxy: weighted combination of NDVI and NDWI
    moisture_index = float(np.clip(mean_ndvi * 0.6 + max(mean_ndwi, 0) * 0.4, 0.0, 1.0))

    return {
        "land_type": land_type,
        "moisture_index": round(moisture_index, 3),
        "ndvi_mean": round(mean_ndvi, 3),
        "ndwi_mean": round(mean_ndwi, 3),
        "vegetation_coverage": round(float((ndvi > 0.20).mean()), 3),
    }
