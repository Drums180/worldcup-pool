import pandas as pd
import streamlit as st

from utils import football_data

st.set_page_config(page_title="Calendario - Copa Mundial 2026", page_icon="📅", layout="wide")

st.title("📅 Calendario y Resultados")

try:
    fixtures_df = football_data.get_fixtures_df()
except Exception as e:
    st.error(f"No se pudo obtener el calendario desde la API: {e}")
    st.stop()

if fixtures_df.empty:
    st.info("Todavía no hay partidos disponibles.")
    st.stop()

fixtures_df = fixtures_df.copy()
fixtures_df["date"] = pd.to_datetime(fixtures_df["date"]).dt.tz_convert("America/Monterrey").dt.tz_localize(None)

stages = ["Todas"] + sorted(fixtures_df["stage"].unique().tolist())
status_options = {
    "Todos": None,
    "Por jugar": ["SCHEDULED", "TIMED", "POSTPONED"],
    "En juego": ["IN_PLAY", "PAUSED", "SUSPENDED"],
    "Finalizados": list(football_data.FINISHED_STATUSES),
}

col1, col2 = st.columns(2)
with col1:
    stage_filter = st.selectbox("Etapa", stages)
with col2:
    status_filter = st.selectbox("Estado", list(status_options.keys()))

filtered = fixtures_df
if stage_filter != "Todas":
    filtered = filtered[filtered["stage"] == stage_filter]
status_values = status_options[status_filter]
if status_values:
    filtered = filtered[filtered["status"].isin(status_values)]

filtered = filtered.sort_values("date")

display = pd.DataFrame({
    "Fecha": filtered["date"].dt.strftime("%d-%b %H:%M"),
    "Etapa": filtered["stage"],
    "Local": filtered["home_team"],
    "Marcador": [
        f"{int(h)} - {int(a)}" if pd.notna(h) and pd.notna(a) else "vs"
        for h, a in zip(filtered["home_goals"], filtered["away_goals"])
    ],
    "Visitante": filtered["away_team"],
    "Estado": filtered["status"],
})

st.dataframe(display, use_container_width=True, hide_index=True)
