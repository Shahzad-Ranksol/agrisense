import os
import httpx

SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"

# SoilGrids v2.0 valid properties — K and P are not available via this API;
# they are estimated from clay content and SOC using regional pedotransfer functions.
SOILGRIDS_PROPS = ["nitrogen", "phh2o", "clay", "soc"]


class SoilAgent:
    async def run(self, lat: float, lon: float) -> dict:
        if os.getenv("USE_MOCK_SOIL", "false").lower() == "true":
            return _mock_soil(lat, lon)

        raw = {}
        async with httpx.AsyncClient(timeout=30) as client:
            for prop in SOILGRIDS_PROPS:
                try:
                    resp = await client.get(
                        SOILGRIDS_URL,
                        params={"lon": lon, "lat": lat, "property": prop, "depth": "0-5cm", "value": "mean"},
                    )
                    resp.raise_for_status()
                    layers = resp.json().get("properties", {}).get("layers", [])
                    if layers:
                        raw[prop] = layers[0]["depths"][0]["values"].get("mean")
                except Exception:
                    raw[prop] = None

        # Unit conversions (SoilGrids stores scaled integers)
        # Fall back to South Asian alluvial-plain medians when API returns null
        N_raw   = raw.get("nitrogen")
        pH_raw  = raw.get("phh2o")
        clay_raw = raw.get("clay")
        soc_raw = raw.get("soc")

        all_null = all(v is None for v in [N_raw, pH_raw, clay_raw, soc_raw])
        N        = (N_raw   / 100.0) if N_raw   is not None else 1.1   # g/kg
        pH       = (pH_raw  / 10.0)  if pH_raw  is not None else 7.6
        clay_pct = (clay_raw / 10.0) if clay_raw is not None else 20.0  # %
        soc      = (soc_raw  / 10.0) if soc_raw  is not None else 0.5   # g/kg

        # Pedotransfer estimates for K and P (South Asian alluvial soils)
        K = max(80.0, clay_pct * 3.5 + soc * 8)
        P = max(5.0,  soc * 4.2 + N * 1.5)

        source_note = (
            "SoilGrids returned no data for this point — regional medians used for N, pH, clay, SOC."
            if all_null else
            "K and P are pedotransfer estimates; N, pH, clay, SOC from ISRIC SoilGrids."
        )

        deficiencies = []
        if N < 1.5:
            deficiencies.append(f"Nitrogen low ({N:.1f} g/kg, target >1.5)")
        if P < 10:
            deficiencies.append(f"Phosphorus low (est. {P:.0f} mg/kg, target >10)")
        if K < 100:
            deficiencies.append(f"Potassium low (est. {K:.0f} mg/kg, target >100)")
        if pH > 0 and not (5.5 <= pH <= 7.5):
            deficiencies.append(f"pH out of range ({pH:.1f}, optimal 5.5–7.5)")

        nutrient_score = (
            min(N / 3.0, 1.0) * 0.40
            + min(P / 20.0, 1.0) * 0.30
            + min(K / 200.0, 1.0) * 0.30
        )

        return {
            "N": round(N, 2),
            "P": round(P, 1),
            "K": round(K, 1),
            "pH": round(pH, 1),
            "clay_pct": round(clay_pct, 1),
            "soc": round(soc, 2),
            "deficiencies": deficiencies,
            "nutrient_score": round(nutrient_score, 3),
            "note": source_note,
        }


def _mock_soil(lat: float, lon: float) -> dict:
    """Typical Punjab alluvial soil values."""
    return {
        "N": 0.9, "P": 8.2, "K": 142.0, "pH": 7.8,
        "clay_pct": 22.0, "soc": 0.4,
        "deficiencies": [
            "Nitrogen low (0.9 g/kg, target >1.5)",
            "Phosphorus low (8 mg/kg, target >10)",
            "pH out of range (7.8, optimal 5.5–7.5)",
        ],
        "nutrient_score": 0.42,
        "note": "Mock data — representative of Punjab alluvial plains.",
    }
