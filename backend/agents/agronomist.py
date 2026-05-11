import asyncio
import json
import os
from datetime import datetime
from typing import AsyncIterator

from backend.agents.geospatial import GeospatialAgent
from backend.agents.soil import SoilAgent
from backend.tools.weather import get_weather
from backend.models.suitability import compute_suitability
from backend.tools.groq_llm import stream_groq
from backend.agents.rule_report import generate as rule_report

SYSTEM_PROMPT = """You are a Master Agronomist specialising in precision agriculture and climate-adaptive farming.

You receive structured data from three sources:
1. Satellite analysis (NASA HLS / Prithvi-100M) — land type, moisture index, NDVI
2. Soil chemistry (ISRIC SoilGrids, 0-5cm) — N, P, K in real units, pH, deficiency flags
3. Weather forecast (OpenWeatherMap, 5-day) — current season, temperature, expected rainfall
4. Pre-computed Crop Suitability scores ranked by S = 0.35·M + 0.40·N + 0.25·C

Generate a **Seasonal Planting Guide** in Markdown:
- Start with a `## Confidence Score: XX%` heading derived from data quality and top crop score
- Recommend the **top 3 crops** with a paragraph each. Every claim must cite specific numbers from the input.
- A `## Soil Amendments` section — if deficiencies exist, give exact kg/hectare for each input.
- A `## Planting Timeline` with conditional triggers, e.g. "Begin sowing after the first 10mm rainfall event."
- A `> ⚠️ Warning:` blockquote if any critical constraint exists (waterlogging, drought, extreme pH, etc.).

Be precise and data-driven. Never give advice that is not grounded in the provided measurements."""


class AgronomistAgent:
    def __init__(self) -> None:
        self.geo_agent = GeospatialAgent()
        self.soil_agent = SoilAgent()

    async def run(self, lat: float, lon: float) -> AsyncIterator[dict]:
        yield {"type": "step", "data": {"message": "Fetching NASA Sentinel-2 imagery...", "step": 1}}

        # All three data fetches run concurrently
        geo_task = asyncio.create_task(self.geo_agent.run(lat, lon))
        soil_task = asyncio.create_task(self.soil_agent.run(lat, lon))
        weather_task = asyncio.create_task(get_weather(lat, lon))

        try:
            yield {"type": "step", "data": {"message": "Running Prithvi-100M land classification...", "step": 2}}
            geo_data = await geo_task
        except Exception as exc:
            yield {"type": "error", "data": {"message": f"Satellite analysis failed: {exc}"}}
            return

        try:
            yield {"type": "step", "data": {"message": "Analysing SoilGrids N-P-K data...", "step": 3}}
            soil_data = await soil_task
        except Exception as exc:
            yield {"type": "error", "data": {"message": f"Soil analysis failed: {exc}"}}
            return

        try:
            yield {"type": "step", "data": {"message": "Fetching seasonal weather forecast...", "step": 4}}
            weather_data = await weather_task
        except Exception as exc:
            yield {"type": "error", "data": {"message": f"Weather fetch failed: {exc}"}}
            return

        yield {"type": "step", "data": {"message": "Computing crop suitability scores...", "step": 5}}
        scores = compute_suitability(
            moisture_index=geo_data["moisture_index"],
            nutrient_score=soil_data["nutrient_score"],
            climate_score=weather_data["climate_score"],
            weather=weather_data,
            soil=soil_data,
        )

        yield {"type": "step", "data": {"message": "Generating planting guide with Claude...", "step": 6}}

        user_message = f"""
## Location
- Coordinates: {lat:.4f}°N, {lon:.4f}°E
- Analysis Date: {datetime.now().strftime("%B %d, %Y")}

## Satellite Analysis (NASA HLS / Prithvi-100M)
- Land Type: {geo_data["land_type"]}
- Soil Moisture Index: {geo_data["moisture_index"]:.2f} (0 = dry, 1 = saturated)
- Mean NDVI: {geo_data["ndvi_mean"]:.3f}
- Vegetation Coverage: {geo_data["vegetation_coverage"] * 100:.1f}%
- Imagery Date: {geo_data["acquisition_date"]}

## Soil Chemistry (ISRIC SoilGrids, 0–5 cm)
- Nitrogen: {soil_data["N"]} g/kg
- Phosphorus: {soil_data["P"]} mg/kg
- Potassium: {soil_data["K"]} mg/kg
- pH: {soil_data["pH"]}
- Deficiencies: {", ".join(soil_data["deficiencies"]) if soil_data["deficiencies"] else "None detected"}
- Nutrient Score: {soil_data["nutrient_score"]:.2f} / 1.00

## Weather Forecast (5-day, OpenWeatherMap)
- Current Season: {weather_data["season"]}
- Avg Temperature: {weather_data["avg_temp_c"]} °C
- Forecasted Rainfall: {weather_data["forecasted_rainfall_mm"]} mm
- Humidity: {weather_data["avg_humidity_pct"]}%
- Climate Score: {weather_data["climate_score"]:.2f} / 1.00

## Crop Suitability Index (S = 0.35·M + 0.40·N + 0.25·C, top 6)
{json.dumps(scores[:6], indent=2)}

Generate the Seasonal Planting Guide now.
"""

        # LLM priority: Groq (free) → rule-based (no API key needed)
        full_report = ""
        use_groq = bool(os.getenv("GROQ_API_KEY", "").strip())

        if use_groq:
            try:
                async for text in stream_groq(SYSTEM_PROMPT, user_message):
                    full_report += text
                    yield {"type": "token", "data": {"text": text}}
            except Exception as exc:
                yield {"type": "token", "data": {"text": f"\n\n_Groq error ({exc}), switching to rule-based report…_\n\n"}}
                full_report = rule_report(geo_data, soil_data, weather_data, scores)
                yield {"type": "token", "data": {"text": full_report}}
        else:
            # Instant rule-based report — no API key required
            full_report = rule_report(geo_data, soil_data, weather_data, scores)
            yield {"type": "token", "data": {"text": full_report}}

        confidence = round(min(0.95, (scores[0]["score"] if scores else 0) * 0.85 + 0.10), 2)

        yield {
            "type": "result",
            "data": {
                "report": full_report,
                "confidence": confidence,
                "geo": geo_data,
                "soil": soil_data,
                "weather": weather_data,
                "scores": scores[:3],
            },
        }
