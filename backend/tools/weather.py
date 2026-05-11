import os
import httpx
from datetime import datetime


async def get_weather(lat: float, lon: float) -> dict:
    api_key = os.environ["OPENWEATHERMAP_API_KEY"]

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric", "cnt": 40},
        )
        resp.raise_for_status()
        data = resp.json()

    forecasts = data["list"]
    avg_temp = sum(f["main"]["temp"] for f in forecasts) / len(forecasts)
    total_rain = sum(f.get("rain", {}).get("3h", 0) for f in forecasts)
    avg_humidity = sum(f["main"]["humidity"] for f in forecasts) / len(forecasts)

    month = datetime.now().month
    if month in (3, 4, 5):
        season = "Spring (Pre-Monsoon)"
    elif month in (6, 7, 8):
        season = "Summer (Monsoon)"
    elif month in (9, 10, 11):
        season = "Autumn (Post-Monsoon)"
    else:
        season = "Winter (Rabi)"

    # Ideal: 20–30°C, 10–50mm rain over 5 days
    temp_score = max(0.0, 1.0 - abs(avg_temp - 25) / 25)
    rain_score = min(total_rain / 50.0, 1.0)
    climate_score = temp_score * 0.6 + rain_score * 0.4

    return {
        "season": season,
        "avg_temp_c": round(avg_temp, 1),
        "forecasted_rainfall_mm": round(total_rain, 1),
        "avg_humidity_pct": round(avg_humidity, 1),
        "climate_score": round(climate_score, 3),
        "current_month": month,
    }
