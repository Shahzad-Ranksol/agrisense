# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Agentic Agriculture App** — a multi-agent system that takes a GPS pin (lat/long) and returns a Seasonal Planting Guide by orchestrating three specialized AI agents:

1. **Geospatial Agent** — fetches NASA Earthdata satellite imagery and runs land classification via `ibm-nasa-geospatial/Prithvi-100M`.
2. **Soil Chemist Agent** — queries ISRIC SoilGrids (or a local CSV) to estimate N-P-K balance and pH.
3. **Agronomist Agent (Orchestrator)** — Claude acts as the reasoning brain, synthesizing the satellite + soil + season data into a Markdown planting guide with a Confidence Score.

## Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI |
| Frontend | React + Mapbox GL JS (map-centric UI) |
| Satellite I/O | `pystac-client`, `stackstac`, `rasterio` |
| ML / Vision | PyTorch, Hugging Face `transformers` (Prithvi-100M) |
| Tabular/Crop ML | `Novadotgg/Crop-recommendation` via HF Inference API |
| Agentic Loop | LangChain + Anthropic Claude (claude-sonnet-4-6 default) |
| Weather | OpenWeatherMap API |
| Containerization | Docker + docker-compose |
| Config | `python-dotenv` (`.env` file) |

## Environment Variables (`.env`)

```
EARTHDATA_USERNAME=           # earthaccess reads these exact names
EARTHDATA_PASSWORD=
OPENWEATHERMAP_API_KEY=
HUGGINGFACE_TOKEN=
ANTHROPIC_API_KEY=
```

## Intended Directory Layout

```
PA-AgenticApp/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── agents/
│   │   ├── geospatial.py    # Geospatial Agent (NASA + Prithvi)
│   │   ├── soil.py          # Soil Chemist Agent (SoilGrids / CSV)
│   │   └── agronomist.py    # Orchestrator Agent (Claude)
│   ├── tools/
│   │   ├── nasa_api.py      # pystac-client tile fetcher
│   │   ├── prithvi.py       # HF Inference call for Prithvi-100M
│   │   └── weather.py       # OpenWeatherMap wrapper
│   └── models/
│       └── suitability.py   # Crop Suitability Index: S = w1*M + w2*N + w3*C
├── frontend/
│   └── src/
│       ├── App.jsx           # Full-screen Mapbox map
│       └── components/
│           ├── PinDrop.jsx   # GPS / pin capture
│           ├── ProgressHUD.jsx  # "Thinking" log overlay
│           └── ResultCard.jsx   # Slide-up report panel
├── docker-compose.yml
├── Dockerfile.backend
└── .env
```

## Common Commands

### Backend
```bash
# Install dependencies
pip install fastapi uvicorn pystac-client stackstac rasterio torch transformers \
            langchain anthropic python-dotenv httpx

# Run dev server
uvicorn backend.main:app --reload --port 8000

# Run a single test
pytest backend/tests/test_nasa_tool.py -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # Vite dev server (port 5173)
npm run build
```

### Docker
```bash
docker-compose up --build   # Builds and starts backend + frontend
docker-compose down
```

## Key Architectural Decisions

### Agentic Orchestration Pattern
The Agronomist agent in `agents/agronomist.py` is the single entry point. It:
1. Calls the Geospatial Agent (async) → returns `{land_type, moisture_index, vegetation_history}`.
2. Calls the Soil Agent (async) → returns `{N, P, K, pH, deficiencies}`.
3. Calls the Weather tool → returns `{season, forecasted_rainfall_mm, temp_C}`.
4. Passes all three payloads to Claude with the Master Agronomist system prompt.
5. Streams the Markdown response back to the frontend via a Server-Sent Events (SSE) endpoint.

### Crop Suitability Index
Ranking is done before the LLM call so Claude has structured scores to reason about:
```
S = w1 * M + w2 * N + w3 * C
```
- `M` = Soil Moisture (0–1, from NASA)
- `N` = Nutrient Score (0–1, normalized N-P-K)
- `C` = Climate/Season Match (0–1, from weather data)
- Weights `w1, w2, w3` are model-determined or configurable per crop type.

### NASA Tile Fetching
Authentication uses `.netrc` or session-based login via `earthaccess`. The tool in `tools/nasa_api.py` queries the HLS (Harmonized Landsat Sentinel-2) STAC collection, filters for cloud cover < 20%, and returns a `stackstac` lazy array. Pass the result to `rasterio` only when slicing to the pin's bounding box.

### Prithvi-100M Integration
The model expects 6-band HLS input (Blue, Green, Red, NIR, SWIR1, SWIR2). Normalize bands to [0,1] before inference. The model outputs a land-cover segmentation mask; extract the dominant class and mean NDVI/moisture proxy from the relevant bands.

### Frontend Progress HUD
The `ProgressHUD` component listens on the SSE stream (`/api/analyze/stream`). The backend emits discrete `event: step` messages as each agent finishes, then a final `event: result` with the full Markdown report. This gives the user real-time "thinking" feedback without polling.
