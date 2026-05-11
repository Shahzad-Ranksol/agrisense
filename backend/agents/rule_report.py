"""
Rule-based planting report generator.
Produces a fully structured Markdown report from structured data —
no LLM API key required.
"""
from __future__ import annotations

AMENDMENT_RATES = {
    "Nitrogen":   {"product": "Urea (46-0-0)",            "kg_per_deficit": 2.2},
    "Phosphorus": {"product": "Single Super Phosphate",   "kg_per_deficit": 6.25},
    "Potassium":  {"product": "Muriate of Potash (MOP)",  "kg_per_deficit": 1.67},
}

CROP_NOTES = {
    "Maize":     "heavy nitrogen feeder; plant in rows 75 cm apart, 25 cm within row.",
    "Wheat":     "sow at 100–120 kg seed/ha; needs cool nights for grain fill.",
    "Rice":      "requires standing water or controlled irrigation; transplant at 21-day seedlings.",
    "Cotton":    "heat-tolerant; ridge planting improves drainage and root depth.",
    "Sugarcane": "ratoon crop — plant setts 90 cm apart; 12-month cycle.",
    "Soybean":   "nitrogen-fixer; minimal N fertiliser needed; inoculate seed with Rhizobium.",
    "Sorghum":   "most drought-tolerant grain; good fallback when rainfall < 400 mm/season.",
    "Chickpea":  "cool-season legume; plant after first frost risk passes.",
}


def generate(geo: dict, soil: dict, weather: dict, scores: list[dict]) -> str:
    top = scores[:3]
    base_score = top[0]["score"] if top else 0
    confidence = round(min(90, max(15, base_score * 85 + 10)))

    # ── Warnings ──────────────────────────────────────────────────────────────
    warnings = []
    if weather["avg_temp_c"] > 35:
        warnings.append(f"Extreme heat ({weather['avg_temp_c']} °C) — irrigation is mandatory before sowing.")
    if weather["forecasted_rainfall_mm"] == 0:
        warnings.append("No rainfall forecast over 5 days — do not sow rain-fed crops.")
    if soil["pH"] > 8.0:
        warnings.append(f"High pH ({soil['pH']}) — apply Gypsum at 500 kg/ha to lower pH before planting.")
    if soil["pH"] < 5.5 and soil["pH"] > 0:
        warnings.append(f"Low pH ({soil['pH']}) — apply Agricultural Lime at 1–2 t/ha.")
    if geo["moisture_index"] < 0.2:
        warnings.append("Low soil moisture index — irrigate to field capacity before sowing.")
    if soil["deficiencies"]:
        for d in soil["deficiencies"]:
            warnings.append(d)

    # ── Soil amendments ───────────────────────────────────────────────────────
    amendments = []
    if soil["N"] < 1.5:
        deficit_n = round(1.5 - soil["N"], 1)
        kg = round(deficit_n * 100 * AMENDMENT_RATES["Nitrogen"]["kg_per_deficit"])
        amendments.append(f"**Nitrogen:** Apply **{kg} kg Urea/ha** in 2 splits (pre-plant + knee-high).")
    if soil["P"] < 10:
        deficit_p = round(10 - soil["P"], 1)
        kg = round(deficit_p * AMENDMENT_RATES["Phosphorus"]["kg_per_deficit"])
        amendments.append(f"**Phosphorus:** Apply **{kg} kg SSP/ha** as pre-plant basal dose.")
    if soil["K"] < 100:
        deficit_k = round(100 - soil["K"], 1)
        kg = round(deficit_k * AMENDMENT_RATES["Potassium"]["kg_per_deficit"])
        amendments.append(f"**Potassium:** Apply **{kg} kg MOP/ha** incorporated to 10 cm depth.")

    # ── Build report ──────────────────────────────────────────────────────────
    lines: list[str] = []

    lines.append(f"## Confidence Score: {confidence}%\n")
    lines.append(
        f"> Based on: {geo['land_type']} · NDVI {geo['ndvi_mean']:.2f} · "
        f"Moisture {geo['moisture_index']:.2f} · {weather['season']} · "
        f"{weather['avg_temp_c']} °C · {weather['forecasted_rainfall_mm']} mm rain\n"
    )

    if warnings:
        lines.append("> ⚠️ **Warnings**")
        for w in warnings:
            lines.append(f"> - {w}")
        lines.append("")

    lines.append("---\n## Top Crop Recommendations\n")
    for i, s in enumerate(top, 1):
        crop = s["crop"]
        score = s["score"]
        note = CROP_NOTES.get(crop, "")
        lines.append(f"### {i}. {crop} — Score {score:.2f}/1.00")
        lines.append(
            f"Suitable for **{weather['season']}** at {weather['avg_temp_c']} °C. "
            f"Soil moisture index {geo['moisture_index']:.2f} "
            f"{'supports' if geo['moisture_index'] > 0.3 else 'is marginal for'} this crop. "
        )
        if note:
            lines.append(f"*Agronomic note:* {note}")
        lines.append("")

    lines.append("---\n## Soil Amendments\n")
    if amendments:
        for a in amendments:
            lines.append(f"- {a}")
    else:
        lines.append("- No amendments required — soil nutrients are within target range.")
    lines.append("")

    lines.append("---\n## Planting Timeline\n")
    month = weather["current_month"]
    if month in (3, 4, 5):
        window = "**April – May** (Pre-Monsoon Kharif preparation)"
        trigger = "Begin sowing after the first 15 mm rainfall event or once irrigated."
    elif month in (6, 7, 8):
        window = "**June – July** (Main Kharif season)"
        trigger = "Sow within 7 days of monsoon onset to maximise growing season."
    elif month in (9, 10, 11):
        window = "**October – November** (Rabi preparation)"
        trigger = "Sow after soil temperature drops below 25 °C."
    else:
        window = "**December – February** (Rabi season)"
        trigger = "Sow when night temperatures stabilise above 5 °C."

    lines.append(f"- **Optimal window:** {window}")
    lines.append(f"- **Trigger condition:** {trigger}")
    lines.append(f"- Apply all amendments **at least 7 days before** sowing.")
    lines.append(
        f"- If rainfall < 10 mm in the next 5 days, **pre-irrigate** to field capacity (60–80 mm)."
    )
    lines.append("")
    lines.append(
        "_Report generated by rule-based agronomic engine. "
        "For AI-enhanced reasoning, set GROQ_API_KEY in .env (free at groq.com)._"
    )

    return "\n".join(lines)
