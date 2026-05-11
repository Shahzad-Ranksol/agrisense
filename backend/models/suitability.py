from typing import Any

# Crop agronomic requirements used to adjust the base suitability score
CROP_PROFILES: dict[str, dict[str, Any]] = {
    "Maize":     {"temp": (20, 32), "min_rain_5d": 5,  "min_N": 1.5, "seasons": {"Spring (Pre-Monsoon)", "Summer (Monsoon)"}},
    "Wheat":     {"temp": (12, 25), "min_rain_5d": 3,  "min_N": 1.0, "seasons": {"Winter (Rabi)"}},
    "Rice":      {"temp": (22, 35), "min_rain_5d": 15, "min_N": 2.0, "seasons": {"Summer (Monsoon)"}},
    "Cotton":    {"temp": (25, 38), "min_rain_5d": 4,  "min_N": 1.2, "seasons": {"Spring (Pre-Monsoon)", "Summer (Monsoon)"}},
    "Sugarcane": {"temp": (20, 35), "min_rain_5d": 8,  "min_N": 1.8, "seasons": {"Spring (Pre-Monsoon)"}},
    "Soybean":   {"temp": (18, 30), "min_rain_5d": 6,  "min_N": 0.8, "seasons": {"Summer (Monsoon)"}},
    "Sorghum":   {"temp": (25, 35), "min_rain_5d": 4,  "min_N": 0.9, "seasons": {"Summer (Monsoon)", "Spring (Pre-Monsoon)"}},
    "Chickpea":  {"temp": (15, 29), "min_rain_5d": 2,  "min_N": 0.6, "seasons": {"Winter (Rabi)", "Autumn (Post-Monsoon)"}},
}


def compute_suitability(
    moisture_index: float,
    nutrient_score: float,
    climate_score: float,
    weather: dict,
    soil: dict,
    w1: float = 0.35,
    w2: float = 0.40,
    w3: float = 0.25,
) -> list[dict]:
    """
    S = w1*M + w2*N + w3*C, then adjusted by agronomic constraints.
    Returns crops ranked by score descending.
    """
    base = w1 * moisture_index + w2 * nutrient_score + w3 * climate_score

    results = []
    for crop, prof in CROP_PROFILES.items():
        score = base

        if weather["season"] in prof["seasons"]:
            score += 0.15

        t_min, t_max = prof["temp"]
        if not (t_min <= weather["avg_temp_c"] <= t_max):
            score -= 0.20

        if weather["forecasted_rainfall_mm"] / 5 < prof["min_rain_5d"]:
            score -= 0.10

        if soil["N"] < prof["min_N"]:
            score -= 0.10

        results.append({"crop": crop, "score": round(max(0.0, min(1.0, score)), 3)})

    return sorted(results, key=lambda x: x["score"], reverse=True)
