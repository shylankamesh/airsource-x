from __future__ import annotations

import json
from hashlib import sha256
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import joblib

from airsource.data import latest_by_station, prepare_observations
from airsource.forecast import detect_anomalies, evaluate_and_forecast, shap_explanation
from airsource.investigation import investigate
from airsource.live import fetch_delhi_context
from airsource.quality import audit_observations
from airsource.model_registry import load_verified_model, inspect_model_registry
from airsource.station_registry import validate_station_registry
from airsource.evaluation import evaluate_by_horizon
from airsource.replay import as_of_replay
from airsource.spatial import (attach_station_metadata, station_distance_matrix,
                               synchronized_station_snapshot, pairwise_spatial_statistics,
                               spatial_coverage_summary)
from airsource.episodes import detect_station_episodes, group_network_episodes, wind_quality_summary
from airsource.connectors import (fetch_openaq_location_latest, fetch_india_ogd_resource,
                                  fetch_firms_area, external_source_catalogue)
from airsource.ingestion import canonicalize_openaq, canonicalize_firms
from airsource.store import ObservationStore
from airsource.context_matching import match_fire_context
from airsource.decision_support import build_screening_brief
from airsource.reliability import ingestion_freshness, benchmark_summary


st.set_page_config(page_title="AirSource X · Environmental Intelligence", page_icon="🌫️",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Manrope', sans-serif; }
.stApp { background: radial-gradient(ellipse at 84% 0%, #12343B 0%, #07131D 43%); }
[data-testid="stSidebar"] { background: #0A1922; border-right: 1px solid #19313E; }
.block-container { padding-top: 1.7rem; max-width: 1440px; }
.brand { color: #60E1C2; font-size: 0.8rem; font-family: 'DM Mono', monospace; letter-spacing: .16em; text-transform: uppercase; }
.hero { padding: 1.35rem 1.6rem 1.5rem; border: 1px solid #24414D; border-radius: 20px; background: linear-gradient(120deg, rgba(17,48,58,.96), rgba(11,29,39,.78)); margin: .6rem 0 1.3rem; }
.hero h1 { font-size: clamp(2rem, 4vw, 3.25rem); line-height: 1.08; margin: .55rem 0 .45rem; letter-spacing: -.055em; color: #F2F7F5; }
.hero p { color: #A8C3C5; font-size: 1rem; max-width: 850px; margin: 0; }
.eyebrow { color: #60E1C2; font-family: 'DM Mono', monospace; font-size: .72rem; letter-spacing: .1em; text-transform: uppercase; }
.section-kicker { color: #60E1C2; font-family: 'DM Mono', monospace; font-size: .73rem; letter-spacing: .12em; text-transform: uppercase; margin: .2rem 0 .4rem; }
.source-pill { display:inline-block; padding: .32rem .62rem; border-radius: 99px; border: 1px solid #31535D; color:#BBD7D2; background:#0D252F; font-size:.73rem; font-family:'DM Mono',monospace; }
.fine { color: #9AB2B9; font-size: .84rem; }
.stMetric { background: linear-gradient(140deg, rgba(17,40,50,.95), rgba(11,27,37,.92)); border: 1px solid #203B47; border-radius: 14px; padding: 14px 16px; }
div[data-testid="stMetricLabel"] p { color:#9AB2B9; font-size:.78rem; letter-spacing:.05em; text-transform:uppercase; }
div[data-testid="stMetricValue"] { color:#F1F7F4; font-weight:700; }
.stButton > button[kind="primary"] { background: linear-gradient(90deg,#45C9AC,#76E4C6); color:#06201E; border:0; font-weight:800; border-radius:11px; min-height:2.8rem; }
.stButton > button { border-radius: 10px; border-color:#36515B; }
[data-testid="stDataFrame"] { border:1px solid #203B47; border-radius:12px; overflow:hidden; }
.stAlert { border-radius: 12px; }
hr { border-color:#1B3541; }
</style>
""", unsafe_allow_html=True)


def hero(title: str, subtitle: str, section: str = "AIR QUALITY INTELLIGENCE") -> None:
    st.markdown(f"<div class='hero'><div class='eyebrow'>{section}</div><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def banner(text: str, tone: str = "info") -> None:
    fn = {"warning": st.warning, "success": st.success, "error": st.error}.get(tone, st.info)
    fn(text)


def safe_datetime(value) -> str:
    return pd.Timestamp(value).strftime("%d %b %Y · %H:%M %Z")


@st.cache_data(ttl=900, show_spinner=False)
def _cached_live(lat: float, lon: float):
    data, provenance = fetch_delhi_context(lat, lon)
    return data, provenance


@st.cache_data(show_spinner=False)
def _cached_public_dataset():
    path = Path(__file__).parent / "data" / "processed" / "delhi_multisite_hourly.csv"
    content = path.read_bytes()
    hourly, report = prepare_observations(pd.read_csv(BytesIO(content)))
    # Git may normalize CSV line endings when checking out on Linux. Hash the
    # canonical newline representation so the bundled models load cross-platform.
    dataset_digest = sha256(content.replace(b"\r\n", b"\n")).hexdigest()
    return hourly, report, dataset_digest


@st.cache_resource(show_spinner=False)
def _cached_model_bundle(station: str, horizon: str, dataset_digest: str):
    """Load only the repository artifact trained for the exact bundled dataset."""
    model_dir = Path(__file__).parent / "models"
    manifest = json.loads((model_dir / "manifest.json").read_text(encoding="utf-8"))
    if dataset_digest != manifest.get("dataset_sha256"):
        return None
    record = next((item for item in manifest.get("artifacts", [])
                   if item.get("station") == station and item.get("horizon") == horizon), None)
    if record is None:
        return None
    path = model_dir / record["file"]
    if path.parent.resolve() != model_dir.resolve() or sha256(path.read_bytes()).hexdigest() != record.get("sha256"):
        return None
    return load_verified_model(model_dir, filename=record['file'], expected_sha256=record['sha256'])


def _source_state():
    return st.session_state.get("dataset_kind", "none"), st.session_state.get("observations"), st.session_state.get("provenance", {})


def _reset_dataset() -> None:
    for key in ("observations", "provenance", "quality_report", "dataset_kind", "forecast_results",
                "forecast_error", "anomaly_scores", "anomaly_error", "upload_digest"):
        st.session_state.pop(key, None)


def _plot_hourly(data: pd.DataFrame, title: str = "PM₂.₅ signal over time", prediction: dict | None = None):
    plot = data.dropna(subset=["pm25"]).sort_values("timestamp")
    fig = px.line(plot, x="timestamp", y="pm25", color="station", markers=False,
                  labels={"timestamp": "Local time (Asia/Kolkata)", "pm25": "PM₂.₅ (µg/m³)", "station": "Station"},
                  title=title, template="plotly_dark")
    fig.update_traces(line=dict(width=2.4))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=12, r=12, t=56, b=12), legend_title_text="")
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(116,155,167,.16)", rangemode="tozero")
    if prediction:
        latest = plot["timestamp"].max()
        values = [prediction.get("target_0_24h"), prediction.get("target_24_48h")]
        if all(v is not None for v in values):
            fig.add_trace(go.Scatter(x=[latest + pd.Timedelta(hours=12), latest + pd.Timedelta(hours=36)],
                                     y=values, mode="lines+markers", name="AirSource model",
                                     line=dict(color="#60E1C2", width=3, dash="dash"), marker=dict(size=9)))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _metrics_table(results: dict) -> pd.DataFrame:
    labels = {"target_0_24h": "Next 0–24 hours", "target_24_48h": "Following 24–48 hours"}
    rows = []
    for target, sets in results["metrics"].items():
        if "error" in sets:
            rows.append({"Horizon": labels[target], "Model": "AirSource", "Samples": 0,
                         "MAE (µg/m³)": "Pending", "RMSE (µg/m³)": "Pending", "Bias (µg/m³)": "Pending"})
            continue
        selected_name = sets.get("selected_model", "Selected model")
        for method, metric in ((selected_name, sets["model"]), ("Persistence", sets["persistence"]),
                               ("Weekly same-horizon naive", sets["seasonal"])):
            rows.append({"Horizon": labels[target], "Model": method, "Samples": metric["samples"],
                         "MAE (µg/m³)": metric["mae"], "RMSE (µg/m³)": metric["rmse"], "Bias (µg/m³)": metric["bias"]})
    return pd.DataFrame(rows)


def _clean_results(results: dict) -> dict:
    output = {k: v for k, v in results.items() if k not in {"models", "metrics"}}
    output["metrics"] = {}
    for target, group in results["metrics"].items():
        if "error" in group:
            output["metrics"][target] = group
            continue
        output["metrics"][target] = {name: {k: (None if not np.isfinite(v) else float(v)) if isinstance(v, (float, np.floating)) else int(v)
                                           for k, v in metric.items() if k != "residuals"}
                                     for name, metric in group.items() if name != "selected_model"}
    return output


def _footer() -> None:
    st.divider()
    st.caption("AirSource X is a research and screening prototype. It is not an official forecast, source-apportionment system, health diagnosis, or safety alert.")


with st.sidebar:
    st.markdown("<div class='brand'>◉ AIRSOURCE X</div>", unsafe_allow_html=True)
    st.caption("Forecast · investigate · measure")
    st.markdown("---")
    page = st.radio("WORKSPACE", ["Overview", "Forecast lab", "Station watch", "Spatial intelligence", "Episode intelligence", "Source investigation & evidence", "Historical replay", "External data", "Public impact", "Reliability & research", "Data & methods"], label_visibility="visible")
    st.markdown("---")
    st.markdown("<div class='section-kicker'>DATA SOURCE</div>", unsafe_allow_html=True)
    mode = st.radio("Choose a source", ["Bundled Delhi station history", "Public Delhi context", "Upload station CSV"], label_visibility="collapsed",
                    key="source_mode", on_change=_reset_dataset)
    if mode == "Bundled Delhi station history":
        st.caption("Six historical CPCB-derived stations · hourly · Jun 2018–Oct 2019 · CC BY 4.0")
        if st.session_state.get("dataset_kind") != "bundled_research":
            try:
                hourly, report, digest = _cached_public_dataset()
                st.session_state["observations"] = hourly
                st.session_state["quality_report"] = report
                st.session_state["provenance"] = {
                    "provider": "Delhi Multi-Site Air-Quality Data Set (Mendeley Data, V1)",
                    "doi": "10.17632/bzhzr9b64v.1",
                    "url": "https://data.mendeley.com/datasets/bzhzr9b64v/1",
                    "contributors": ["Shilpa Sonawani", "Kailas Patil"],
                    "upstream_source": "CPCB Continuous Ambient Air Quality Monitoring network, as described by the dataset authors",
                    "license": "CC BY 4.0",
                    "data_class": "Historical ground-monitor observations; source labels and measurement quality remain as provided by the dataset authors.",
                    "period": "2018-06-01 through 2019-10-01 (station end-times vary)",
                    "sha256": digest,
                    "preparation": "Station-specific timestamps preserved; WS converted from m/s to km/h based on dataset attribute units reported in cited literature; no missing pollutant values imputed.",
                }
                st.session_state["dataset_kind"] = "bundled_research"
                st.session_state.pop("forecast_results", None)
                st.session_state.pop("forecast_error", None)
                st.session_state.pop("anomaly_scores", None)
                st.session_state.pop("anomaly_error", None)
            except Exception as exc:
                st.error(f"Bundled research dataset could not be loaded: {exc}")
    elif mode == "Public Delhi context":
        st.caption("Provider grid estimates for Delhi. No key required. Not CPCB station readings.")
        lat = st.number_input("Latitude", min_value=-90.0, max_value=90.0, value=28.6139, step=0.001, format="%.4f")
        lon = st.number_input("Longitude", min_value=-180.0, max_value=180.0, value=77.2090, step=0.001, format="%.4f")
        if st.button("Fetch 48-hour provider context", type="primary", use_container_width=True):
            try:
                with st.spinner("Fetching air-quality and weather estimates…"):
                    live_data, live_provenance = _cached_live(lat, lon)
                    st.session_state["observations"] = live_data
                    st.session_state["provenance"] = live_provenance
                    st.session_state["dataset_kind"] = "provider_model"
                    st.session_state.pop("quality_report", None)
                    st.session_state.pop("forecast_results", None)
                    st.session_state.pop("anomaly_scores", None)
                    st.success("Context refreshed")
            except Exception as exc:
                st.error(f"Live provider is unavailable: {exc}")
    else:
        upload = st.file_uploader("Hourly station data (.csv)", type=["csv"], help="Required: timestamp and PM2.5; recommended: station, PM10, NO2, CO, wind, temperature and humidity.")
        if upload is not None:
            try:
                content = upload.getvalue()
                digest = sha256(content).hexdigest()
                if digest != st.session_state.get("upload_digest"):
                    hourly, report = prepare_observations(pd.read_csv(BytesIO(content)))
                    st.session_state["observations"] = hourly
                    st.session_state["quality_report"] = report
                    st.session_state["provenance"] = {"provider": "User-supplied CSV", "file_name": upload.name,
                        "sha256": digest,
                        "data_class": "Uploaded observations; source and measurement status have not been independently verified."}
                    st.session_state["dataset_kind"] = "uploaded_observations"
                    st.session_state["upload_digest"] = digest
                    st.session_state.pop("forecast_results", None)
                    st.session_state.pop("forecast_error", None)
                    st.session_state.pop("anomaly_scores", None)
                    st.session_state.pop("anomaly_error", None)
                    st.success(f"Loaded {report['hourly_rows']:,} hourly rows")
            except Exception as exc:
                st.error(str(exc))
    if st.session_state.get("dataset_kind"):
        kind, data, provenance = _source_state()
        if data is not None and not data.empty:
            st.markdown("---")
            st.markdown("<div class='section-kicker'>ACTIVE SOURCE</div>", unsafe_allow_html=True)
            source_label = {"provider_model": "PROVIDER GRID ESTIMATE", "bundled_research": "HISTORICAL CPCB-DERIVED DATA", "uploaded_observations": "UPLOADED DATA"}.get(kind, "DATA")
            st.markdown(f"<span class='source-pill'>{source_label}</span>", unsafe_allow_html=True)
            st.caption(f"{data['station'].nunique()} station label(s) · {len(data):,} hourly records")


kind, observations, provenance = _source_state()
selected_station = None
if observations is not None and not observations.empty:
    names = sorted(observations["station"].astype(str).unique())
    selected_station = st.sidebar.selectbox("FOCUS STATION", names, index=0)
    if st.session_state.get("result_station") not in (None, selected_station):
        st.session_state.pop("forecast_results", None)
        st.session_state.pop("forecast_error", None)
        st.session_state.pop("anomaly_scores", None)
    st.session_state["result_station"] = selected_station


def need_data() -> bool:
    if observations is None or observations.empty:
        banner("Load a CSV or fetch the public Delhi provider context from the sidebar to begin.", "warning")
        return False
    return True


if page == "Overview":
    hero("Air quality, with its evidence in view.",
         "A Delhi-first workspace that forecasts PM₂.₅, compares stations, surfaces competing signals, and shows where evidence is still missing.")
    if observations is None or observations.empty:
        col1, col2 = st.columns([1.4, 1])
        with col1:
            st.markdown("### Start with an evidence source")
            st.markdown("Use the **bundled historical Delhi stations** for an immediate reproducible evaluation, the provider context for a current grid-model outlook, or upload your own hourly monitor readings.")
            st.markdown("<span class='source-pill'>NO INVENTED METRICS</span> &nbsp; <span class='source-pill'>SOURCE ≠ PROOF</span> &nbsp; <span class='source-pill'>MISSING DATA STAYS MISSING</span>", unsafe_allow_html=True)
        with col2:
            st.info("The bundled six-station CPCB-derived dataset supports an immediate historical model evaluation. It is not a live feed.")
        st.markdown("### The investigation loop")
        cards = st.columns(4)
        for col, number, title, copy in zip(cards, ("01", "02", "03", "04"),
                                             ("Forecast", "Compare", "Investigate", "Measure next"),
                                             ("Two separate 24-hour horizons", "Station context and unusual patterns", "Support, contradiction, and abstention", "A transparent next-best data request")):
            with col:
                st.markdown(f"<div class='hero' style='min-height:145px'><div class='eyebrow'>{number}</div><h3>{title}</h3><p>{copy}</p></div>", unsafe_allow_html=True)
    else:
        if kind == "provider_model":
            banner("Provider mode: these are Open-Meteo grid estimates based on CAMS air-quality forecasts. They are not ground-monitor readings and are not used as training labels or validation truth.")
            st.caption("Air-quality source attribution: Open-Meteo and the Copernicus Atmosphere Monitoring Service (CAMS). [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api)")
        elif kind == "uploaded_observations":
            banner("Uploaded data are treated as observations supplied by you. Confirm station identity, units, quality flags, and licensing before interpreting results.", "warning")
        elif kind == "bundled_research":
            banner("Historical station data · June 2018–October 2019. This enables a reproducible retrospective benchmark; it does not represent today's air quality.", "warning")
        snapshot_heading = "HISTORICAL SNAPSHOT" if kind == "bundled_research" else "CURRENT SNAPSHOT"
        st.markdown(f"<div class='section-kicker'>{snapshot_heading}</div>", unsafe_allow_html=True)
        snapshot = latest_by_station(observations)
        if snapshot.empty:
            st.info("No valid PM2.5 measurements were found.")
        else:
            focus = snapshot.loc[snapshot.station.astype(str) == selected_station].iloc[-1]
            a, b, c, d = st.columns(4)
            snapshot_label = {"provider_model": "provider estimate", "bundled_research": "historical monitor value", "uploaded_observations": "uploaded value"}.get(kind, "")
            a.metric("PM₂.₅ concentration", f"{focus.pm25:.1f} µg/m³", snapshot_label)
            b.metric("PM₁₀", f"{focus.pm10:.1f} µg/m³" if pd.notna(focus.get("pm10")) else "Unavailable")
            c.metric("Wind speed", f"{focus.wind_speed_kmh:.1f} km/h" if pd.notna(focus.get("wind_speed_kmh")) else "Unavailable")
            d.metric("Timestamp", safe_datetime(focus.timestamp))
            _plot_hourly(observations, "PM₂.₅ concentration · station context")
            if kind == "provider_model":
                future = observations.loc[observations.timestamp > pd.Timestamp.now(tz="Asia/Kolkata")]
                if len(future) >= 24:
                    next_day = future.sort_values("timestamp").head(24)
                    after_day = future.sort_values("timestamp").iloc[24:48]
                    st.markdown("<div class='section-kicker'>PROVIDER OUTLOOK</div>", unsafe_allow_html=True)
                    one, two, three = st.columns(3)
                    one.metric("Provider PM₂.₅ · next 24h", f"{next_day.pm25.mean():.1f} µg/m³" if next_day.pm25.notna().any() else "Unavailable")
                    two.metric("Provider PM₂.₅ · following 24h", f"{after_day.pm25.mean():.1f} µg/m³" if after_day.pm25.notna().any() else "Unavailable")
                    three.metric("Forecast hours returned", f"{int(future.pm25.notna().sum())}")
                    st.caption("Means are computed over the provider time steps returned (global air-quality guidance is 3-hourly). These are gridded estimates, not AirSource X predictions or measured ground truth.")
            if "latitude" in observations and "longitude" in observations and observations[["latitude", "longitude"]].notna().all(axis=1).any():
                st.markdown("<div class='section-kicker'>STATION MAP</div>", unsafe_allow_html=True)
                points = snapshot.dropna(subset=["latitude", "longitude"])[["latitude", "longitude", "station", "pm25"]]
                if not points.empty:
                    st.map(points.rename(columns={"latitude": "lat", "longitude": "lon"}), size=70,
                           color="#60E1C2", use_container_width=True)
                    st.caption("Marker positions are provided with the source data; no spatial interpolation is performed.")
    _footer()

elif page == "Forecast lab":
    hero("Forecast lab", "Evaluate both horizons on a chronological holdout, compare against simple baselines, and inspect the exact test window.", "MODEL EVALUATION")
    if need_data():
        if kind == "provider_model":
            st.warning("Provider grid estimates are not ground-monitor truth. Model training and reported validation metrics are disabled in this mode. Switch to Upload station CSV with verified historical observations.")
        else:
            if kind == "bundled_research" and not st.session_state.get("forecast_results"):
                try:
                    station_data = observations.loc[observations.station.astype(str) == selected_station].copy()
                    preview = {horizon: _cached_model_bundle(selected_station, horizon, provenance.get("sha256", ""))
                               for horizon in ("target_0_24h", "target_24_48h")}
                    if all(preview.values()):
                        st.markdown("### Instant forecast · bundled research models")
                        as_of = preview["target_0_24h"]["trained_through"]
                        st.caption(f"Pre-trained artifacts for {selected_station} · historical issue time {safe_datetime(as_of)} · trained on the bundled dataset")
                        cols = st.columns(2)
                        preview_values = {}
                        for col, horizon, label in (
                            (cols[0], "target_0_24h", "Model · next 0–24h"),
                            (cols[1], "target_24_48h", "Model · following 24–48h"),
                        ):
                            bundle = preview[horizon]
                            value = float(bundle["forecast_pm25_ug_m3"])
                            low, high = bundle["forecast_interval_90"]
                            preview_values[horizon] = value
                            with col:
                                st.metric(label, f"{value:.1f} µg/m³",
                                          delta=f"90% historical interval {low:.1f}–{high:.1f}",
                                          delta_color="off")
                                st.caption(f"{bundle['selected_model']} · validation-selected")
                        _plot_hourly(station_data, "Historical PM₂.₅ and pre-trained model outlook", preview_values)
                        st.caption("This quick forecast uses the pre-trained artifact for the exact bundled historical dataset. The interval is calibrated from historical residuals; it is not a current-air alert. Run the evaluation below for the holdout metrics and a fresh fit.")
                        metric_rows = []
                        benchmark = pd.read_csv(Path(__file__).parent / "reports" / "public_benchmark.csv")
                        for horizon, bundle in preview.items():
                            subset = benchmark[(benchmark.station == selected_station) & (benchmark.horizon == horizon)]
                            metric_rows.append({"Horizon": "Next 0–24 h" if horizon == "target_0_24h" else "Following 24–48 h",
                                                "Model": bundle["selected_model"],
                                                "Test MAE (µg/m³)": bundle["holdout_metrics"]["mae"],
                                                "Test RMSE (µg/m³)": bundle["holdout_metrics"]["rmse"]})
                            for baseline in ("persistence", "Weekly same-horizon naive"):
                                row = subset[subset.model == baseline]
                                if not row.empty:
                                    metric_rows.append({"Horizon": "Next 0–24 h" if horizon == "target_0_24h" else "Following 24–48 h",
                                                        "Model": baseline,
                                                        "Test MAE (µg/m³)": float(row.iloc[0].mae),
                                                        "Test RMSE (µg/m³)": float(row.iloc[0].rmse)})
                        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)
                    else:
                        st.info("No matching pre-trained bundle is available for this station and dataset. Run the chronological evaluation below.")
                except Exception as exc:
                    st.warning(f"The pre-trained preview is unavailable; the evaluation below can still fit this dataset. Details: {exc}")
            if st.button("Run chronological evaluation + latest forecast", type="primary"):
                station_data = observations.loc[observations.station.astype(str) == selected_station].copy()
                with st.spinner("Building issue-time-safe features and evaluating the holdout…"):
                    try:
                        st.session_state["forecast_results"] = evaluate_and_forecast(station_data)
                        st.session_state.pop("forecast_error", None)
                    except Exception as exc:
                        st.session_state["forecast_error"] = str(exc)
            if st.session_state.get("forecast_error"):
                st.error(st.session_state["forecast_error"])
            results = st.session_state.get("forecast_results")
            if results:
                if results.get("latest_timestamp"):
                    st.caption(f"Focus station: {selected_station} · Latest usable issue time: {safe_datetime(results['latest_timestamp'])} · model: {results['model_name']}")
                if results["forecast"]:
                    f1, f2 = st.columns(2)
                    for col, target, label in ((f1, "target_0_24h", "AirSource model · next 0–24h"),
                                               (f2, "target_24_48h", "AirSource model · following 24–48h")):
                        with col:
                            value = results["forecast"].get(target)
                            interval = results.get("forecast_intervals", {}).get(target)
                            interval_text = (f"90% interval {interval[0]:.1f}–{interval[1]:.1f} µg/m³"
                                             if interval and value is not None else None)
                            st.metric(label, f"{value:.1f} µg/m³" if value is not None else "Not available",
                                      delta=interval_text, delta_color="off")
                _plot_hourly(observations.loc[observations.station.astype(str) == selected_station],
                             "Historical PM₂.₅ and two-horizon model outlook", results.get("forecast"))
                st.markdown("<div class='section-kicker'>UNTOUCHED CHRONOLOGICAL HOLDOUT</div>", unsafe_allow_html=True)
                st.dataframe(_metrics_table(results), use_container_width=True, hide_index=True)
                st.caption(f"Training issue times end before {safe_datetime(results['train_end'])}; holdout begins {safe_datetime(results['test_start'])}. Model choice uses three expanding-window validation folds; a later calibration block estimates 90% split-conformal interval width. A 48-hour purge protects each boundary. Coverage can drift across seasons and is measured on the holdout. The weekly naive baseline reuses the same target from one week earlier, when available.")
                uncertainty_rows = [{"Horizon": target.replace("target_", "").replace("_", " "),
                                     "Calibration samples": info["calibration_samples"],
                                     "Nominal interval": "90%",
                                     "Observed holdout coverage": info["test_coverage"],
                                     "Mean interval width (µg/m³)": info["mean_test_interval_width_ug_m3"]}
                                    for target, info in results.get("uncertainty", {}).items()]
                if uncertainty_rows:
                    st.markdown("#### Forecast uncertainty check")
                    st.dataframe(pd.DataFrame(uncertainty_rows), use_container_width=True, hide_index=True)
                    st.caption("Intervals are calibrated on a later historical block and evaluated on the untouched holdout. Their nominal coverage is not guaranteed under seasonal or distribution shift.")
                st.download_button("Download evaluated metrics (CSV)", _metrics_table(results).to_csv(index=False).encode(),
                                   "airsource_metrics.csv", "text/csv")
                st.download_button("Download model run manifest (JSON)", json.dumps(_clean_results(results), indent=2, default=str),
                                   "airsource_run_manifest.json", "application/json")
                st.markdown("#### What the model saw")
                st.write("Available issue-time features: observed pollutant and weather values, lagged concentrations, rolling history, cyclic calendar terms, and wind-direction components. Features are computed at the forecast issue time; targets are future PM₂.₅ averages.")
                st.info("Local SHAP explanations describe how this predictive model uses its inputs. They are not physical causation or source apportionment.")
                for target, label in (("target_0_24h", "next 0–24h"), ("target_24_48h", "following 24–48h")):
                    if target in results.get("models", {}) and st.button(f"Explain {label} prediction with SHAP", key=f"shap_{target}"):
                        try:
                            context = results["explain_data"][target]
                            local = shap_explanation(results["models"][target], context["row"], context["background"])
                            local = local.reindex(local.shap_value.abs().sort_values(ascending=False).index).head(12).sort_values("shap_value")
                            explain_fig = px.bar(local, x="shap_value", y="feature", orientation="h", color="shap_value",
                                                 color_continuous_scale=["#4D8DD5", "#90A7AF", "#54D5B3"],
                                                 labels={"shap_value":"SHAP contribution (µg/m³)","feature":"Input feature"},
                                                 title=f"Local SHAP · {label}", template="plotly_dark")
                            explain_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",coloraxis_showscale=False,margin=dict(l=8,r=8,t=50,b=10))
                            st.plotly_chart(explain_fig,use_container_width=True,config={"displayModeBar":False})
                            st.caption("SHAP contributions add to the model output relative to the sampled background. They explain prediction behaviour, not a pollution source.")
                        except Exception as exc:
                            st.error(f"SHAP explanation is unavailable for this model run: {exc}")
            else:
                st.info("No result has been computed yet. The evaluation uses a time-ordered 80/20 holdout, a 48-hour purge, and the same valid test rows for the learned model and persistence baseline.")
    _footer()

elif page == "Station watch":
    station_subtitle = ("Compare the latest observations within the selected historical dataset, catch unusual multivariate patterns, and inspect station coverage."
                        if kind == "bundled_research" else
                        "Compare synchronized station readings, catch unusual multivariate patterns, and keep spatial coverage visible.")
    hero("Station watch", station_subtitle, "SPATIAL CONTEXT")
    if need_data():
        latest = latest_by_station(observations)
        if latest.empty:
            st.info("No valid PM2.5 rows are available.")
        else:
            st.markdown("<div class='section-kicker'>LATEST OBSERVATIONS BY STATION</div>", unsafe_allow_html=True)
            display = [c for c in ("station", "timestamp", "pm25", "pm10", "no2", "co", "wind_speed_kmh", "latitude", "longitude") if c in latest]
            st.dataframe(latest[display].rename(columns={"station": "Station", "timestamp": "Local timestamp", "pm25": "PM₂.₅ (µg/m³)", "pm10": "PM₁₀ (µg/m³)", "no2": "NO₂", "co": "CO", "wind_speed_kmh": "Wind (km/h)"}), use_container_width=True, hide_index=True)
            st.caption("Station coverage is observational context only. This app does not interpolate between monitors or infer a pollution plume path.")
            if len(latest) >= 2:
                comp = px.bar(latest.sort_values("pm25", ascending=True), x="pm25", y="station", orientation="h",
                              labels={"pm25": "Latest PM₂.₅ (µg/m³)", "station": "Station"},
                              title="Latest station concentrations", template="plotly_dark", color="pm25",
                              color_continuous_scale=["#42BEA3", "#F0BF65", "#F07867"])
                comp.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False, margin=dict(l=8,r=8,t=52,b=12))
                st.plotly_chart(comp, use_container_width=True, config={"displayModeBar": False})
            st.markdown("### Unusual-pattern scan")
            st.write("Isolation Forest flags combinations that differ from this station's own history. An unusual row is not a confirmed pollution incident.")
            if st.button("Scan selected station", type="primary"):
                own = observations.loc[observations.station.astype(str) == selected_station]
                try:
                    st.session_state["anomaly_scores"] = detect_anomalies(own)
                    st.session_state.pop("anomaly_error", None)
                except Exception as exc:
                    st.session_state["anomaly_error"] = str(exc)
            if st.session_state.get("anomaly_error"):
                st.error(st.session_state["anomaly_error"])
            scored = st.session_state.get("anomaly_scores")
            if scored is not None:
                count = int(scored["is_unusual"].sum())
                a,b=st.columns(2)
                a.metric("Rows screened", f"{len(scored):,}")
                b.metric("Rows flagged unusual", f"{count:,}")
                fig = px.scatter(scored, x="timestamp", y="pm25", color="is_unusual", symbol="is_unusual",
                                 color_discrete_map={False:"#4CC5AA",True:"#F19C71"},
                                 labels={"timestamp":"Local timestamp","pm25":"PM₂.₅ (µg/m³)","is_unusual":"Unusual-pattern flag"},
                                 title="PM₂.₅ and multivariate pattern flags", template="plotly_dark")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=8,r=8,t=52,b=12))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                view = scored.loc[scored.is_unusual].sort_values("anomaly_score").tail(20)
                st.dataframe(view[["timestamp","pm25","anomaly_score","features_used"]],use_container_width=True,hide_index=True)
    _footer()

elif page == "Spatial intelligence":
    hero("Spatial intelligence", "Compare station geography, synchronized PM₂.₅ patterns, and pairwise temporal similarity without interpolating missing readings or inferring a pollution plume.", "MULTI-STATION ANALYTICS")
    if need_data():
        bundled_registry = Path(__file__).parent / "configs" / "delhi_station_registry.csv"
        uploaded_registry = st.file_uploader("Station registry with sourced coordinates (CSV)", type=["csv"], key="spatial_registry_upload")
        try:
            registry = pd.read_csv(uploaded_registry) if uploaded_registry is not None else pd.read_csv(bundled_registry)
            audit = validate_station_registry(registry)
            if not audit["valid"]:
                st.error("Station registry failed validation: " + "; ".join(audit["errors"]))
            else:
                spatial_data = attach_station_metadata(observations, registry)
                if spatial_data.empty:
                    st.warning("No observations matched the station registry. Check station IDs.")
                else:
                    coverage = spatial_coverage_summary(observations, registry)
                    a,b,c = st.columns(3)
                    a.metric("Registered stations", coverage["registered_stations"])
                    b.metric("Stations with data", coverage["stations_with_observations"])
                    c.metric("Matched observation rows", f"{coverage['observation_rows_with_coordinates']:,}")
                    if audit["warnings"]:
                        for warning in audit["warnings"]:
                            st.warning(warning)
                    st.markdown("### Station geography")
                    map_points = registry.dropna(subset=["latitude", "longitude"]).copy()
                    if not map_points.empty:
                        geo = px.scatter(map_points, x="longitude", y="latitude", text="station_name",
                            hover_data=["station_id", "operator", "site_type", "coordinate_quality"],
                            labels={"longitude":"Longitude","latitude":"Latitude"},
                            title="Registered monitoring station positions", template="plotly_dark")
                        geo.update_traces(marker=dict(size=12), textposition="top center")
                        geo.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                          margin=dict(l=8,r=8,t=52,b=8),yaxis_scaleanchor="x",yaxis_scaleratio=1)
                        st.plotly_chart(geo,use_container_width=True,config={"displayModeBar":False})
                    st.caption("Coordinates are sourced metadata rounded in the cited station inventory. They represent station locations, not pollution fields.")
                    st.markdown("### Synchronized station comparison")
                    snapshot = synchronized_station_snapshot(observations, registry)
                    if len(snapshot) >= 2:
                        st.caption(f"Latest timestamp shared by at least two monitors: {snapshot['timestamp'].max()}")
                        snap_fig = px.bar(snapshot.sort_values("pm25"),x="pm25",y="station",orientation="h",
                            labels={"pm25":"PM₂.₅ (µg/m³)","station":"Station"},
                            title="PM₂.₅ at the latest common timestamp",template="plotly_dark")
                        snap_fig.update_layout(paper_bgcolor="rgba(0,0,0",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=8,r=8,t=52,b=8))
                        st.plotly_chart(snap_fig,use_container_width=True,config={"displayModeBar":False})
                        st.dataframe(snapshot[["station","station_name","timestamp","pm25"]],use_container_width=True,hide_index=True)
                    else:
                        st.info("At least two stations need an exactly shared timestamp for this comparison. No values are interpolated.")
                    st.markdown("### Pairwise distance and temporal similarity")
                    min_overlap = st.number_input("Minimum overlapping hourly observations for correlation",min_value=12,max_value=1000,value=48,step=12)
                    stats = pairwise_spatial_statistics(observations,registry,min_overlap=int(min_overlap))
                    if not stats.empty:
                        st.dataframe(stats.round({"distance_km":2,"pearson_r":3}),use_container_width=True,hide_index=True)
                    st.caption("Pearson correlation is descriptive temporal similarity, not proof of a common source or transport. Distances are straight-line station-to-station distances.")
                    st.markdown("### PM₂.₅ time series")
                    fig = px.line(spatial_data.sort_values("timestamp"),x="timestamp",y="pm25",color="station",
                        labels={"timestamp":"Timestamp (UTC-normalized)","pm25":"PM₂.₅ (µg/m³)","station":"Station"},
                        title="Observed PM₂.₅ by station",template="plotly_dark")
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=8,r=8,t=52,b=8))
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                    st.download_button("Download pairwise spatial statistics",stats.to_csv(index=False),
                        "airsource_pairwise_spatial_statistics.csv","text/csv")
                    st.download_button("Download station registry audit",json.dumps({"audit":audit,"coverage":coverage},indent=2,default=str),
                        "airsource_spatial_audit.json","application/json")
        except Exception as exc:
            st.error(f"Spatial analysis could not run: {exc}")
    _footer()

elif page == "Episode intelligence":
    hero("Pollution episode intelligence",
         "Screen for persistent station-level PM₂.₅ rises, compare when stations respond, and inspect peak timing. Temporal association is not source attribution.",
         "EVENT DETECTION · MULTI-STATION")
    if need_data():
        st.markdown("### Detection settings")
        left, mid, right = st.columns(3)
        with left:
            baseline_hours = st.number_input("Prior baseline window (hours)", min_value=12, max_value=168, value=24, step=12)
            min_baseline_points = st.number_input("Minimum baseline observations", min_value=6, max_value=120, value=12, step=2)
        with mid:
            min_excess = st.number_input("Minimum rise above baseline (µg/m³)", min_value=5.0, max_value=200.0, value=25.0, step=5.0)
            min_pm25 = st.number_input("Minimum PM₂.₅ concentration (µg/m³)", min_value=25.0, max_value=500.0, value=75.0, step=5.0)
        with right:
            min_duration = st.number_input("Minimum persistent duration (hours)", min_value=1, max_value=24, value=2, step=1)
            link_hours = st.number_input("Maximum station onset grouping window (hours)", min_value=1, max_value=12, value=3, step=1)
        st.caption("Rule: PM₂.₅ must exceed the prior rolling median by the larger of the selected absolute rise or 2.5 × robust MAD-derived standard deviation, and exceed the concentration floor. The baseline uses earlier readings only.")
        try:
            with st.spinner("Screening station histories for persistent episodes…"):
                station_events = detect_station_episodes(
                    observations, baseline_hours=int(baseline_hours),
                    min_baseline_points=int(min_baseline_points),
                    min_excess_ug_m3=float(min_excess),
                    min_pm25_ug_m3=float(min_pm25),
                    min_duration_hours=int(min_duration))
                network_events = group_network_episodes(station_events, onset_link_hours=int(link_hours))
            k1, k2, k3 = st.columns(3)
            k1.metric("Station episodes", len(station_events))
            k2.metric("Multi-station episodes", len(network_events))
            k3.metric("Stations represented", station_events["station"].nunique() if not station_events.empty else 0)
            if kind == "bundled_research":
                st.info("The bundled station archive ends in 2019. These are historical retrospective detections, not current Delhi pollution alerts.")
            elif kind == "provider_model":
                st.warning("Provider grid estimates are not ground-monitor observations. Treat episode flags as exploratory provider-series anomalies only.")
            else:
                st.warning("Uploaded data are not independently verified. Check station identity, units, sampling cadence and quality flags.")
            if network_events.empty:
                st.info("No multi-station episodes met the current screening settings. This does not prove that no pollution episode occurred.")
            else:
                st.markdown("### Multi-station episode timeline")
                plot = network_events.copy()
                plot["first_onset_label"] = plot["first_onset"].dt.strftime("%Y-%m-%d %H:%M")
                fig = px.scatter(plot, x="first_onset", y="network_peak_pm25_ug_m3",
                    size="station_count", color="station_count", hover_name="episode_id",
                    hover_data=["stations_affected","lead_station","last_station","onset_span_hours","network_peak_time"],
                    labels={"first_onset":"First station onset","network_peak_pm25_ug_m3":"Highest station peak (µg/m³)",
                            "station_count":"Stations"}, title="Detected multi-station episodes", template="plotly_dark")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=8,r=8,t=52,b=8))
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                st.dataframe(network_events,use_container_width=True,hide_index=True)
            st.markdown("### Station-level onset and peak details")
            if station_events.empty:
                st.info("No station-level episodes met the current screening settings.")
            else:
                st.dataframe(station_events,use_container_width=True,hide_index=True)
                st.download_button("Download station episode table",station_events.to_csv(index=False),
                    "airsource_station_episodes.csv","text/csv")
            st.markdown("### Wind-data quality gate")
            wind_audit = wind_quality_summary(observations)
            if not wind_audit["available"]:
                st.info(wind_audit["reason"])
            else:
                w1,w2,w3 = st.columns(3)
                w1.metric("Rows passing plausibility screen", f"{wind_audit['plausible_fraction']:.1%}")
                w2.metric("Observed maximum wind speed", f"{wind_audit['observed_max_speed_kmh']:.1f} km/h")
                w3.metric("Wind context", "Eligible for review" if wind_audit["usable_for_context"] else "Blocked")
                if wind_audit["usable_for_context"]:
                    st.warning(wind_audit["reason"] + " Wind is not used here to infer a source or plume direction.")
                else:
                    st.error(wind_audit["reason"])
            st.caption("Interpretation limits: onset order and peak timing describe the supplied time series. They do not establish a shared emitter, transport direction, chemical source, or causal relationship. Event thresholds are screening parameters, not official regulatory alert thresholds.")
            st.download_button("Download network episode table",network_events.to_csv(index=False),
                "airsource_network_episodes.csv","text/csv")
            st.download_button("Download wind quality audit",json.dumps(wind_audit,indent=2,default=str),
                "airsource_wind_quality_audit.json","application/json")
        except Exception as exc:
            st.error(f"Episode screening could not run: {exc}")
    _footer()


elif page == "External data":
    hero("External environmental data",
         "Connect external observations and contextual datasets with explicit source metadata. Measurements, model estimates and satellite products remain separate.",
         "CONNECTORS · PROVENANCE · QUALITY")
    st.markdown("### Connector readiness")
    catalogue = pd.DataFrame(external_source_catalogue())
    st.dataframe(catalogue, use_container_width=True, hide_index=True)
    st.caption("Credentials are used only for the request and are not written to project files. For deployment, configure secrets through the hosting platform's secret manager.")
    tab_openaq, tab_ogd, tab_firms = st.tabs(["OpenAQ sensors", "India OGD / CPCB catalogue", "NASA FIRMS fires"])
    with tab_openaq:
        st.markdown("OpenAQ provides sensor-level measurements. Its `latest` endpoint returns the latest value in each sensor series, not necessarily the latest ingested measurement.")
        loc_id = st.number_input("OpenAQ location ID", min_value=1, value=2178, step=1)
        oq_key = st.text_input("OpenAQ API key", type="password", key="openaq_key")
        if st.button("Fetch OpenAQ latest readings", key="fetch_openaq"):
            try:
                with st.spinner("Requesting OpenAQ location data…"):
                    frame, meta = fetch_openaq_location_latest(int(loc_id), api_key=oq_key or None)
                st.success(f"Received {len(frame)} sensor readings.")
                st.dataframe(frame, use_container_width=True, hide_index=True)
                canonical = canonicalize_openaq(frame, meta)
                result = ObservationStore(Path(__file__).parent / "data" / "airsource_observations.sqlite").ingest(canonical, meta)
                st.session_state["v7_last_ingest"] = result
                st.success(f"Saved to local research store: {result['rows_inserted']} new · {result['rows_ignored']} duplicates/ignored.")
                st.json(meta)
                st.download_button("Download OpenAQ CSV", frame.to_csv(index=False), "airsource_openaq_latest.csv", "text/csv")
            except Exception as exc:
                st.error(f"OpenAQ request failed: {exc}")
    with tab_ogd:
        st.markdown("Use the exact resource ID from the government catalogue. The connector deliberately does not guess a resource ID or map unknown columns to PM2.5.")
        resource_id = st.text_input("data.gov.in resource ID")
        ogd_key = st.text_input("data.gov.in API key", type="password", key="ogd_key")
        limit = st.number_input("Maximum records", min_value=1, max_value=10000, value=1000, step=100)
        if st.button("Fetch configured government resource", key="fetch_ogd"):
            try:
                with st.spinner("Requesting government catalogue resource…"):
                    frame, meta = fetch_india_ogd_resource(resource_id, api_key=ogd_key or None, limit=int(limit))
                st.success(f"Received {len(frame)} records.")
                st.dataframe(frame.head(1000), use_container_width=True, hide_index=True)
                st.json(meta)
                st.download_button("Download government CSV", frame.to_csv(index=False), "airsource_india_ogd.csv", "text/csv")
            except Exception as exc:
                st.error(f"Government resource request failed: {exc}")
    with tab_firms:
        st.markdown("FIRMS detects thermal anomalies and active-fire candidates. It does not measure PM2.5 and cannot establish that a fire caused a station episode.")
        c1,c2,c3,c4 = st.columns(4)
        west = c1.number_input("West longitude", min_value=-180.0, max_value=180.0, value=76.70, step=0.05)
        south = c2.number_input("South latitude", min_value=-90.0, max_value=90.0, value=28.20, step=0.05)
        east = c3.number_input("East longitude", min_value=-180.0, max_value=180.0, value=77.80, step=0.05)
        north = c4.number_input("North latitude", min_value=-90.0, max_value=90.0, value=29.10, step=0.05)
        firms_source = st.selectbox("Satellite product", ["VIIRS_SNPP_NRT","VIIRS_NOAA20_NRT","VIIRS_NOAA21_NRT","MODIS_NRT","VIIRS_SNPP_SP"])
        day_range = st.slider("Days to request", 1, 5, 1)
        firms_key = st.text_input("NASA FIRMS MAP_KEY", type="password", key="firms_key")
        if st.button("Fetch FIRMS detections", key="fetch_firms"):
            try:
                with st.spinner("Requesting NASA FIRMS detections…"):
                    frame, meta = fetch_firms_area(west,south,east,north,source=firms_source,
                                                   day_range=int(day_range),map_key=firms_key or None)
                st.success(f"Received {len(frame)} satellite detections.")
                st.dataframe(frame, use_container_width=True, hide_index=True)
                canonical = canonicalize_firms(frame, meta)
                result = ObservationStore(Path(__file__).parent / "data" / "airsource_observations.sqlite").ingest(canonical, meta)
                st.session_state["v7_last_ingest"] = result
                st.success(f"Saved to local research store: {result['rows_inserted']} new · {result['rows_ignored']} duplicates/ignored.")
                st.json(meta)
                st.download_button("Download FIRMS CSV", frame.to_csv(index=False), "airsource_firms_detections.csv", "text/csv")
            except Exception as exc:
                st.error(f"FIRMS request failed: {exc}")
    st.markdown("### Local observation store · V7")
    store = ObservationStore(Path(__file__).parent / "data" / "airsource_observations.sqlite")
    with st.expander("Inspect stored observations and ingestion history", expanded=True):
        history = store.ingestion_history()
        health = store.source_health()
        if not health.empty:
            st.markdown("**Source collection health**")
            st.dataframe(health, use_container_width=True, hide_index=True)
        if not history.empty:
            st.markdown("**Recent ingestion runs**")
            st.dataframe(history.drop(columns=["metadata_json"], errors="ignore"), use_container_width=True, hide_index=True)
        stored = store.observations(limit=5000)
        st.metric("Stored canonical observations", len(stored))
        if not stored.empty:
            fire_points = stored[(stored["data_class"] == "satellite_fire_detection")].copy()
            if not fire_points.empty and {"latitude", "longitude"}.issubset(fire_points.columns):
                fire_points["latitude"] = pd.to_numeric(fire_points["latitude"], errors="coerce")
                fire_points["longitude"] = pd.to_numeric(fire_points["longitude"], errors="coerce")
                fire_points = fire_points.dropna(subset=["latitude", "longitude"])
                if not fire_points.empty:
                    st.markdown("**Stored satellite fire-context detections**")
                    st.map(fire_points.rename(columns={"latitude":"lat","longitude":"lon"})[["lat","lon"]])
                    st.caption("Detection locations are contextual observations, not verified pollution sources.")
            st.dataframe(stored.head(100), use_container_width=True, hide_index=True)
            st.download_button("Export stored observations (CSV)", stored.to_csv(index=False),
                               "airsource_canonical_observations.csv", "text/csv")
        st.caption("SQLite is local to this app instance. Ephemeral hosting may discard it on restart/redeploy; configure a persistent volume or external database for production.")
        st.markdown("**Screen FIRMS detections against a station episode/event CSV**")
        st.caption("CSV columns required: event_id, timestamp, latitude, longitude. This is a proximity/time screen, not causal attribution.")
        event_file = st.file_uploader("Upload event coordinates CSV", type=["csv"], key="v7_event_csv")
        if event_file is not None:
            try:
                events = pd.read_csv(event_file)
                detections = store.observations(data_class="satellite_fire_detection", limit=100000)
                if st.button("Match events to stored FIRMS detections", key="v7_match_context"):
                    matches = match_fire_context(events, detections, radius_km=25, window_hours=6)
                    st.session_state["v7_context_matches"] = matches
                matches = st.session_state.get("v7_context_matches")
                if matches is not None:
                    st.dataframe(matches, use_container_width=True, hide_index=True)
                    st.download_button("Download context matches", matches.to_csv(index=False),
                                       "airsource_event_fire_context.csv", "text/csv")
            except Exception as exc:
                st.error(f"Could not match event context: {exc}")
    st.markdown("### Satellite product integration policy")
    st.info("Sentinel-5P/TROPOMI NO₂ and NASA MAIAC aerosol optical depth are registered as future integrations, not yet ingested. Their columns/products require product-specific QA, cloud/retrieval screening, overpass-time handling and spatial/vertical interpretation before any comparison with surface PM₂.₅.")
    _footer()


elif page == "Source investigation & evidence":
    hero("Evidence room", "Inspect competing patterns, see contradictions and missing inputs, then remove an evidence family to see what changes.", "SOURCE SCREENING · NOT ATTRIBUTION")
    if need_data():
        if kind == "provider_model":
            st.warning("Source screening is disabled for provider grid estimates. Use time-aligned, quality-controlled monitor observations; gridded forecasts alone are not evidence of a local source.")
        else:
            families = ["Coarse particle + wind", "Combustion co-pollutants", "Concurrent station context"]
            excluded = set(st.multiselect("Counterfactual: remove evidence families", families,
                                           help="This recomputes the screening cards with the selected input family treated as unavailable. It is a software sensitivity check, not a causal intervention."))
            try:
                report = investigate(observations, selected_station, excluded)
                m1,m2 = st.columns([1,2])
                m1.metric("Selected station PM₂.₅", f"{report['pm25']:.1f} µg/m³")
                m2.markdown(f"**Current screening summary**  \n{report['summary']}")
                for claim in report["claims"]:
                    with st.container(border=True):
                        left,right=st.columns([1.2,2])
                        with left:
                            st.markdown(f"#### {claim['hypothesis']}")
                            tone = "success" if claim["status"] in {"Pattern present", "Shared elevation across monitors"} else "warning"
                            banner(claim["status"],tone)
                        with right:
                            if claim["supports"]:
                                st.markdown("**Signals**  \n"+"  \n".join("• "+x for x in claim["supports"]))
                            if claim["contradicts"]:
                                st.markdown("**Contradictions / non-support**  \n"+"  \n".join("• "+x for x in claim["contradicts"]))
                            st.caption(claim["reason"])
                st.markdown("### Missing evidence")
                missing = sorted(set(report["missing"] + ["Quality-screened satellite fire detections with overpass-time and location provenance",
                                                            "Boundary-layer height / vertical mixing context",
                                                            "Upwind and downwind measurements with reliable timestamps"]))
                if missing:
                    for item in missing:
                        st.markdown(f"- **Unavailable:** {item}")
                else:
                    st.markdown("No required input was explicitly unavailable for these screening rules; independent source evidence is still needed for attribution.")
                st.markdown("### Next most useful measurement")
                st.info(report["next_step"])
                st.markdown("### Guardrail")
                st.warning(report["limitation"]+" All thresholds here are relative to the uploaded station history and are preliminary screening heuristics, not validated source-detection thresholds.")
                audit = {k:v for k,v in report.items() if k != "claims"}
                audit["claims"] = report["claims"]
                audit["provenance"] = provenance
                audit["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
                st.download_button("Download investigation record (JSON)",json.dumps(audit,indent=2,default=str),
                                   "airsource_investigation.json","application/json")
            except Exception as exc:
                st.error(str(exc))
    _footer()

elif page == "Data & methods":
    hero("Trust starts in the data", "See what was loaded, what was transformed, which evaluation boundaries were used, and what this prototype cannot establish.", "PROVENANCE · LIMITATIONS")
    if observations is None or observations.empty:
        st.info("Load a data source to inspect its provenance and quality report.")
    else:
        st.markdown("### Provenance record")
        st.json(provenance, expanded=True)
        st.markdown("### Model artifact integrity")
        model_audit = inspect_model_registry(Path(__file__).parent / "models",
                                             dataset_sha256=st.session_state.get("upload_digest") if kind == "uploaded_observations" else None)
        if model_audit["status"] == "invalid":
            st.error("Model registry validation failed. Do not use affected artifacts.")
        elif model_audit["status"] == "warning":
            st.warning("Model files pass integrity checks, but the runtime differs from the training environment.")
        else:
            st.success("Model manifest and artifact checksums verified.")
        if model_audit["warnings"]:
            st.write("**Runtime compatibility warnings**")
            for warning in model_audit["warnings"]:
                st.caption(warning)
        if model_audit["errors"]:
            st.json(model_audit["errors"])
        st.dataframe(pd.DataFrame(model_audit["artifacts"]), use_container_width=True, hide_index=True)

        st.markdown("### Data quality diagnostics")
        try:
            diagnostics = audit_observations(observations)
            qa1, qa2, qa3, qa4 = st.columns(4)
            qa1.metric("Rows audited", f"{diagnostics['row_count']:,}")
            qa2.metric("Stations", str(diagnostics["station_count"]))
            qa3.metric("Duplicate station-times", str(diagnostics["duplicate_station_timestamps"]))
            age = diagnostics["latest_data_age_hours"]
            qa4.metric("Latest data age", "Unavailable" if age is None else f"{age:,.1f} h")
            if diagnostics["invalid_timestamps"] or diagnostics["range_violations"]:
                st.warning("Quality issues were detected. Review them before using this dataset for scientific conclusions.")
            if diagnostics["range_violations"]:
                st.markdown("**Physical-range screening flags**")
                st.json(diagnostics["range_violations"])
            if diagnostics["invalid_timestamps"]:
                st.write(f"Invalid timestamps: {diagnostics['invalid_timestamps']}")
            st.markdown("**Station-level temporal coverage**")
            st.dataframe(pd.DataFrame(diagnostics["stations"]), use_container_width=True, hide_index=True)
            st.caption(diagnostics["policy"])
        except Exception as exc:
            st.error(f"Could not complete data quality diagnostics: {exc}")
        if kind == "bundled_research":
            st.markdown("Dataset attribution: Sonawani & Patil (2021), [Delhi Multi-Site Air-Quality Data Set, V1](https://doi.org/10.17632/bzhzr9b64v.1), licensed CC BY 4.0. This is an author-curated historical dataset, not a live feed.")
        if kind in {"uploaded_observations", "bundled_research"} and st.session_state.get("quality_report"):
            report=st.session_state["quality_report"]
            a,b,c,d=st.columns(4)
            a.metric("Input rows",f"{report['input_rows']:,}")
            b.metric("Hourly rows",f"{report['hourly_rows']:,}")
            c.metric("Station labels",str(report["stations"]))
            d.metric("PM₂.₅ missing",f"{report['missing_pm25_rows']:,}")
            st.caption(report["timestamp_policy"]+" "+report["missing_policy"])
            st.markdown("#### Hourly station coverage")
            st.dataframe(report["coverage"],use_container_width=True,hide_index=True)
            if report["discarded_invalid_timestamps"] or report["duplicate_station_timestamps"] or report["negative_values_set_missing"]:
                st.markdown("#### Quality flags")
                st.json({k:report[k] for k in ("discarded_invalid_timestamps","duplicate_station_timestamps","negative_values_set_missing")})
        st.markdown("### Station metadata registry")
        st.caption("Upload a sourced station registry to validate metadata. Blank coordinates remain unverified; no locations are inferred.")
        registry_file = st.file_uploader("Station registry CSV", type=["csv"], key="station_registry_upload")
        if registry_file is not None:
            try:
                registry = pd.read_csv(registry_file)
                registry_result = validate_station_registry(registry)
                if registry_result["valid"]:
                    st.success(f"Registry structure valid · {registry_result.get('station_count', 0)} station(s)")
                else:
                    st.error("Registry validation failed.")
                for message in registry_result["errors"]:
                    st.write(f"Error: {message}")
                for message in registry_result["warnings"]:
                    st.warning(message)
                st.dataframe(registry, use_container_width=True, hide_index=True)
            except Exception as exc:
                st.error(f"Could not read station registry: {exc}")

        st.markdown("### Held-out forecast evaluation")
        st.caption("Optional CSV schema: actual, predicted, horizon. Severe-event classification requires a threshold in the same concentration units as the predictions.")
        evaluation_file = st.file_uploader("Prediction comparison CSV", type=["csv"], key="evaluation_upload")
        if evaluation_file is not None:
            threshold = st.number_input("Severe-event threshold (µg/m³; optional)", min_value=0.0, value=0.0, step=5.0, key="evaluation_threshold")
            try:
                comparison = pd.read_csv(evaluation_file)
                metrics = evaluate_by_horizon(comparison, severe_threshold=threshold if threshold > 0 else None)
                st.json(metrics, expanded=True)
                st.caption("Metrics describe only the uploaded comparison rows. The threshold is a user-defined research threshold, not an official AQI category.")
            except Exception as exc:
                st.error(f"Could not evaluate prediction file: {exc}")

        st.markdown("### Method card")
        st.markdown("""
| Stage | Method | Guardrail |
|---|---|---|
| Upload | Alias mapping, timestamp normalization, station-hour aggregation | No interpolation; negative pollutant values become missing |
| Targets | Mean PM₂.₅ in the next 0–24h and following 24–48h | Requires complete hourly target windows |
| Model | Select among regularized LightGBM configurations and HistGradientBoosting | Selected using a separate purged validation block |
| Validation | Chronological train / validation / calibration / test blocks; 48-hour purges | No random split; holdout remains untouched until final evaluation |
| Baselines | Persistence and weekly same-horizon naive target | Uses the target from one week earlier when it is observable at issue time |
| Uncertainty | 90% split-conformal absolute-residual intervals | Calibration-block radius and untouched-test coverage are both shown |
| Anomaly scan | Isolation Forest on available pollutant/weather columns | Flags unusual combinations, not incidents |
| Investigation | Relative station-history heuristics and synchronized peer context | Abstains; no causal source attribution |
""")
    st.markdown("### Known limitations")
    st.markdown("- Provider-mode values are gridded estimates and cannot validate a station model.\n- An upload's provenance, calibration, station siting, licenses, units, and quality flags are user responsibilities unless explicitly documented in the file.\n- A single station cannot reliably separate local emissions from regional transport.\n- SHAP or other model explanation is predictive, not causal.\n- Fire detections, satellite NO₂, boundary-layer height, trajectory modelling, calibrated uncertainty, and online drift monitoring are not connected in this first build.\n- Overall Indian AQI is not calculated; a PM₂.₅ concentration is not an overall AQI.")
    _footer()


elif page == "Historical replay":
    hero("Historical event replay", "Reconstruct what was knowable at a past decision time. Records without explicit availability timestamps are excluded rather than assumed available.", "AS-OF REPLAY · NO LOOK-AHEAD")
    st.markdown("### Upload a timestamped evidence ledger")
    st.caption("CSV must include observed_at and available_at. Optional columns can include station, parameter, value, source and event_id. Times are interpreted as UTC when timezone-naive; include offsets to avoid ambiguity.")
    replay_file = st.file_uploader("Evidence ledger CSV", type=["csv"], key="v8_replay_csv")
    if replay_file is not None:
        try:
            ledger = pd.read_csv(replay_file)
            if not {"observed_at", "available_at"}.issubset(ledger.columns):
                st.error("This file cannot support an as-of replay: both observed_at and available_at are required.")
            else:
                min_time = pd.to_datetime(ledger["available_at"], errors="coerce", utc=True).min()
                max_time = pd.to_datetime(ledger["available_at"], errors="coerce", utc=True).max()
                if pd.isna(min_time) or pd.isna(max_time):
                    st.error("No valid availability timestamps were found.")
                else:
                    cutoff_value = st.datetime_input("Replay cutoff (local time)", value=max_time.tz_convert("Asia/Kolkata").tz_localize(None).to_pydatetime(), key="v8_replay_cutoff")
                    cutoff = pd.Timestamp(cutoff_value).tz_localize("Asia/Kolkata").tz_convert("UTC")
                    replayed = as_of_replay(ledger, cutoff)
                    excluded = len(ledger) - len(replayed)
                    a,b,c = st.columns(3)
                    a.metric("Input records", f"{len(ledger):,}")
                    b.metric("Knowable at cutoff", f"{len(replayed):,}")
                    c.metric("Excluded", f"{excluded:,}")
                    st.caption(f"Cutoff: {cutoff.isoformat()} · excludes late, missing-time and impossible availability-before-observation records.")
                    st.dataframe(replayed, use_container_width=True, hide_index=True)
                    st.download_button("Download as-of evidence ledger", replayed.to_csv(index=False), "airsource_asof_replay.csv", "text/csv")
        except Exception as exc:
            st.error(f"Replay could not be evaluated: {exc}")
    st.info("The bundled historical dataset has observation timestamps but no independently verified publication/availability timestamps. It cannot, by itself, support a faithful historical information-set replay.")
    _footer()

elif page == "Public impact":
    hero("Public impact & decisions", "Translate monitor readings into transparent review priorities, with explicit thresholds, timestamps and limitations—not automated public-health advice.", "DECISION SUPPORT · HUMAN REVIEW")
    if need_data():
        threshold = st.number_input("User-defined PM₂.₅ review threshold (µg/m³)", min_value=1.0, max_value=1000.0, value=75.0, step=5.0)
        try:
            brief = build_screening_brief(observations, review_threshold_ug_m3=threshold)
            a,b,c = st.columns(3)
            a.metric("Stations with readings", brief["station_count"])
            b.metric("Stations flagged for review", brief["stations_for_review"])
            c.metric("Review threshold", f"{threshold:g} µg/m³")
            st.dataframe(brief["latest_by_station"], use_container_width=True, hide_index=True)
            st.markdown("### Suggested operational workflow")
            st.markdown("1. Verify monitor status, timestamp, units and quality flags.\n2. Compare nearby stations and check whether the elevation is spatially shared.\n3. Review weather and independent contextual evidence without treating proximity as causation.\n4. Have a responsible human review the evidence before communicating any finding.")
            st.markdown("### Guardrails")
            for item in brief["limitations"]:
                st.warning(item)
            export = {k:v for k,v in brief.items() if k != "latest_by_station"}
            export["latest_by_station"] = brief["latest_by_station"].to_dict("records")
            st.download_button("Download public-impact screening brief (JSON)", json.dumps(export, indent=2, default=str), "airsource_public_impact_brief.json", "application/json")
        except Exception as exc:
            st.error(f"Decision brief could not be created: {exc}")
    _footer()

elif page == "Reliability & research":
    hero("Reliability & research", "Inspect historical benchmark performance, source collection freshness and known failure modes before trusting a result.", "MODEL PERFORMANCE · SOURCE HEALTH")
    report_path = Path(__file__).parent / "reports" / "public_benchmark.json"
    if report_path.exists():
        try:
            benchmark = json.loads(report_path.read_text(encoding="utf-8"))
            st.markdown("### Historical benchmark context")
            st.warning(benchmark.get("dataset", {}).get("warning", "Benchmark scope is limited to its documented dataset and protocol."))
            st.json(benchmark.get("protocol", {}), expanded=False)
            bench_df = benchmark_summary(benchmark)
            if not bench_df.empty:
                st.dataframe(bench_df, use_container_width=True, hide_index=True)
                st.download_button("Download benchmark comparison", bench_df.to_csv(index=False), "airsource_benchmark_comparison.csv", "text/csv")
            else:
                st.info("No holdout runs were found in the saved benchmark report. See the raw report.")
            with st.expander("Inspect full benchmark report"):
                st.json(benchmark, expanded=False)
        except Exception as exc:
            st.error(f"Benchmark report could not be read: {exc}")
    else:
        st.info("No saved benchmark report is packaged.")
    st.markdown("### External source collection health")
    store = ObservationStore(Path(__file__).parent / "data" / "airsource_observations.sqlite")
    history = store.ingestion_history(limit=500)
    if history.empty:
        st.info("No external ingestion runs are recorded in this local instance yet.")
    else:
        cadence = st.number_input("Expected collection interval (hours)", min_value=1.0, max_value=720.0, value=24.0, step=1.0)
        freshness = ingestion_freshness(history, expected_interval_hours=cadence)
        st.dataframe(freshness, use_container_width=True, hide_index=True)
        st.caption("Freshness is computed from the last successful local retrieval, not from an independent provider uptime probe.")
        st.dataframe(history.drop(columns=["metadata_json"], errors="ignore"), use_container_width=True, hide_index=True)
    st.markdown("### Known reliability limitations")
    for item in ["Historical benchmark results do not establish present-day accuracy or transfer to other regions/seasons.",
                 "Prediction intervals can be wide; nominal conformal coverage is not guaranteed under distribution shift.",
                 "External-source freshness reflects local successful retrievals only.",
                 "A model or data-quality flag is a review prompt, not proof of a pollution event."]:
        st.warning(item)
    _footer()
