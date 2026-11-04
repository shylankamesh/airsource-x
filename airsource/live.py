"""Public, keyless Open-Meteo context fetcher. Values are provider estimates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

from .data import prepare_observations

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_delhi_context(latitude: float = 28.6139, longitude: float = 77.2090) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Fetch a 48-hour provider-modelled outlook with recent context.

    Open-Meteo output is not a Delhi government monitor reading. The UI and
    provenance export retain that distinction.
    """
    common = {"latitude": latitude, "longitude": longitude, "timezone": "Asia/Kolkata",
              "forecast_hours": 48, "past_hours": 48}
    air_params = {**common, "hourly": "pm2_5,pm10,nitrogen_dioxide,carbon_monoxide,sulphur_dioxide,ozone"}
    weather_params = {**common, "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation"}
    headers = {"User-Agent": "AirSource-X/0.1 (research prototype)"}
    responses = []
    for url, params in ((AIR_URL, air_params), (WEATHER_URL, weather_params)):
        response = requests.get(url, params=params, headers=headers, timeout=25)
        response.raise_for_status()
        payload = response.json()
        if "hourly" not in payload or "time" not in payload["hourly"]:
            raise ValueError("The provider returned no hourly data for this request.")
        responses.append(payload)
    air, weather = responses
    a = pd.DataFrame(air["hourly"])
    w = pd.DataFrame(weather["hourly"])
    w = w.rename(columns={"time": "timestamp", "temperature_2m": "temperature_c",
                          "relative_humidity_2m": "humidity_pct", "wind_speed_10m": "wind_speed_kmh",
                          "wind_direction_10m": "wind_direction_deg", "precipitation": "precipitation_mm"})
    merged = a.rename(columns={"time": "timestamp", "pm2_5": "pm25", "nitrogen_dioxide": "no2",
                               "carbon_monoxide": "co", "sulphur_dioxide": "so2", "ozone": "o3"})
    merged = merged.merge(w, on="timestamp", how="left")
    merged["station"] = "Delhi — Open-Meteo grid estimate"
    merged["latitude"] = latitude
    merged["longitude"] = longitude
    prepared, quality = prepare_observations(merged)
    provenance = {
        "provider": "Open-Meteo Air Quality API and Forecast API",
        "endpoints": [AIR_URL, WEATHER_URL],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "coordinates": {"latitude": latitude, "longitude": longitude},
        "data_class": "Provider-modelled air-quality and weather estimates; not ground-station observations.",
        "attribution": "Air-quality estimates from Open-Meteo based on Copernicus Atmosphere Monitoring Service (CAMS) forecasts. See https://open-meteo.com/en/docs/air-quality-api.",
        "license_note": "Review the provider's current terms and attribution requirements before public deployment.",
        "quality": {k: v for k, v in quality.items() if k != "coverage"},
    }
    return prepared, provenance
