import streamlit as st

from utils import scoring, sheets

st.set_page_config(page_title="Equipos - Copa Mundial 2026", page_icon="🎯", layout="wide")

st.title("🎯 Equipos por persona")

picks_df = sheets.read_picks()
resultados_df = sheets.read_resultados()
bonuses_df = sheets.read_bonuses()

picks_long = scoring.normalize_picks(picks_df)

if picks_long.empty:
    st.info("No se encontraron equipos en la hoja de Picks/Equipos.")
    st.stop()

match_pts = resultados_df.groupby("team")["points"].sum() if not resultados_df.empty else None
bonus_pts = bonuses_df.set_index("team")["bonus_points"] if not bonuses_df.empty else None
stage_reached = bonuses_df.set_index("team")["stage_reached"] if not bonuses_df.empty else None

for persona, group in picks_long.groupby("persona"):
    st.subheader(persona)
    rows = []
    for team in group["team"]:
        mp = int(match_pts.get(team, 0)) if match_pts is not None else 0
        bp = int(bonus_pts.get(team, 0)) if bonus_pts is not None else 0
        sr = stage_reached.get(team, "-") if stage_reached is not None else "-"
        rows.append({
            "Equipo": team,
            "Puntos Partidos": mp,
            "Etapa Alcanzada": sr,
            "Puntos Eliminación": bp,
            "Total": mp + bp,
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)
