import streamlit as st

from utils import football_data, scoring, sheets

st.set_page_config(page_title="Copa Mundial 2026", page_icon="🏆", layout="wide")

st.title("🏆 Copa Mundial 2026")

picks_df = sheets.read_picks()
fixtures_df = football_data.get_fixtures_df()
resultados_df = scoring.build_resultados(fixtures_df)
bonuses_df = scoring.build_bonuses(fixtures_df)

picks_long = scoring.normalize_picks(picks_df)
leaderboard = scoring.compute_leaderboard(picks_long, resultados_df, bonuses_df)

if leaderboard.empty:
    st.info("Aún no hay datos.")
else:
    leader = leaderboard.iloc[0]
    cols = st.columns(min(len(leaderboard), 3))
    for col, (_, row) in zip(cols, leaderboard.head(3).iterrows()):
        with col:
            st.metric(row["persona"], f"{int(row['total'])} pts")

    st.subheader("Tabla de posiciones")
    display = leaderboard.rename(columns={
        "persona": "Persona",
        "match_points": "Puntos Partidos",
        "bonus_points": "Puntos Eliminación",
        "total": "Total",
    })
    display.index = range(1, len(display) + 1)
    st.dataframe(display, use_container_width=True)

    st.caption(f"🥇 Líder actual: **{leader['persona']}** con {int(leader['total'])} puntos")
