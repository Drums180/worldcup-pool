import pandas as pd
import streamlit as st

from utils import football_data, scoring, sheets

st.set_page_config(page_title="Partidos del Día - Copa Mundial 2026", page_icon="🔥", layout="wide")

st.title("🔥 Partidos del Día")

try:
    fixtures_df = football_data.get_fixtures_df()
except Exception as e:
    st.error(f"No se pudo obtener el calendario desde la API: {e}")
    st.stop()

picks_df = sheets.read_picks()
picks_long = scoring.normalize_picks(picks_df)
team_to_persona = picks_long.set_index("team")["persona"].to_dict()

resultados_df = scoring.build_resultados(fixtures_df)
if resultados_df.empty:
    record = pd.DataFrame(columns=["W", "D", "L"])
else:
    record = resultados_df.groupby("team")["result"].value_counts().unstack(fill_value=0)
    for col in ["W", "D", "L"]:
        if col not in record.columns:
            record[col] = 0

fixtures_df = fixtures_df.copy()
fixtures_df["date"] = pd.to_datetime(fixtures_df["date"]).dt.tz_convert("America/Monterrey").dt.tz_localize(None)

today = pd.Timestamp.now(tz="America/Monterrey").tz_localize(None).date()
todays = fixtures_df[fixtures_df["date"].dt.date == today].sort_values("date")

if todays.empty:
    st.info("No hay partidos programados para hoy.")
    st.stop()

GREEN = "background-color: #c8f7c5"
YELLOW = "background-color: #fff3b0"
RED = "background-color: #f7c5c5"


def team_info(team: str):
    persona = team_to_persona.get(team, "Sin asignar")
    g = int(record["W"].get(team, 0))
    e = int(record["D"].get(team, 0))
    p = int(record["L"].get(team, 0))
    return persona, g, e, p


for _, f in todays.iterrows():
    home_persona, home_g, home_e, home_p = team_info(f["home_team"])
    away_persona, away_g, away_e, away_p = team_info(f["away_team"])

    header = f"**{f['date'].strftime('%H:%M')}** · {f['stage']} · {football_data.translate_status(f['status'])}"
    if pd.notna(f["home_goals"]) and pd.notna(f["away_goals"]):
        header += f" · {int(f['home_goals'])} - {int(f['away_goals'])}"
    if home_persona == away_persona and home_persona != "Sin asignar":
        header += f" · 🆚 ¡**{home_persona}** juega contra sí mismo!"
    st.markdown(header)

    match_df = pd.DataFrame({
        "Equipo": [f["home_team"], f["away_team"]],
        "Persona": [home_persona, away_persona],
        "G": [home_g, away_g],
        "E": [home_e, away_e],
        "P": [home_p, away_p],
    })
    styler = (
        match_df.style
        .map(lambda v: GREEN if v > 0 else "", subset=["G"])
        .map(lambda v: YELLOW if v > 0 else "", subset=["E"])
        .map(lambda v: RED if v > 0 else "", subset=["P"])
    )
    st.table(styler)
    st.divider()
