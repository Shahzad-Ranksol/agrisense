import asyncio
from backend.tools.nasa_api import fetch_hls_tile
from backend.tools.prithvi import analyze_land


class GeospatialAgent:
    async def run(self, lat: float, lon: float) -> dict:
        # Both calls are CPU/IO-bound — run in thread pool
        tile_data = await asyncio.to_thread(fetch_hls_tile, lat, lon)
        land_analysis = await asyncio.to_thread(analyze_land, tile_data["bands"])

        return {
            "land_type": land_analysis["land_type"],
            "moisture_index": land_analysis["moisture_index"],
            "ndvi_mean": land_analysis["ndvi_mean"],
            "ndwi_mean": land_analysis["ndwi_mean"],
            "vegetation_coverage": land_analysis["vegetation_coverage"],
            "acquisition_date": tile_data["acquisition_date"],
            "tile_id": tile_data["tile_id"],
            "cloud_cover": tile_data.get("cloud_cover"),
        }
