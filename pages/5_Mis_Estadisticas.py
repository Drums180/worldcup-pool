import altair as alt
import pandas as pd
import streamlit as st

from utils import football_data, scoring, sheets

st.title("📈 Mis Estadísticas")

try:
    fixtures_df = football_data.get_fixtures_df()
except Exception as e:
    st.error(f"No se pudo obtener el calendario desde la API: {e}")
    st.stop()

try:
    picks_df = sheets.read_picks()
except Exception as e:
    st.error(f"No se pudieron obtener los equipos desde Google Sheets: {e}")
    st.stop()
picks_long = scoring.normalize_picks(picks_df)

if picks_long.empty:
    st.info("No se encontraron equipos en la hoja de Picks/Equipos.")
    st.stop()

personas = sorted(picks_long["persona"].unique())
persona = st.selectbox("Selecciona tu nombre", personas)

resultados_df = scoring.build_resultados(fixtures_df)
bonuses_df = scoring.build_bonuses(fixtures_df)

my_teams = picks_long[picks_long["persona"] == persona]["team"].tolist()
my_results = resultados_df[resultados_df["team"].isin(my_teams)].copy()

if my_results.empty:
    st.info("Todavía no hay partidos finalizados para tus equipos.")
    st.stop()

my_results["date"] = my_results["date"].dt.tz_convert("America/Monterrey").dt.tz_localize(None)
my_results = my_results.sort_values("date")

played = len(my_results)
won = int((my_results["result"] == "W").sum())
drawn = int((my_results["result"] == "D").sum())
lost = int((my_results["result"] == "L").sum())
goals_for = int(my_results["goals_for"].sum())
goals_against = int(my_results["goals_against"].sum())

cols = st.columns(6)
cols[0].metric("Partidos jugados", played)
cols[1].metric("Ganados", won)
cols[2].metric("Empatados", drawn)
cols[3].metric("Perdidos", lost)
cols[4].metric("Goles (F-C)", f"{goals_for}-{goals_against}")
cols[5].metric("% de victorias", f"{won / played:.0%}")

st.divider()

chart_col, time_col = st.columns(2)

with chart_col:
    st.subheader("Ganados / Empatados / Perdidos")
    donut_df = pd.DataFrame({
        "Resultado": ["Ganados", "Empatados", "Perdidos"],
        "Partidos": [won, drawn, lost],
    })
    donut_df = donut_df[donut_df["Partidos"] > 0]
    donut_df["Porcentaje"] = donut_df["Partidos"] / played

    donut = alt.Chart(donut_df).mark_arc(innerRadius=70).encode(
        theta=alt.Theta("Partidos", type="quantitative"),
        color=alt.Color(
            "Resultado",
            scale=alt.Scale(
                domain=["Ganados", "Empatados", "Perdidos"],
                range=["#2ecc71", "#f1c40f", "#e74c3c"],
            ),
        ),
        tooltip=["Resultado", "Partidos", alt.Tooltip("Porcentaje", format=".0%")],
    )
    st.altair_chart(donut, use_container_width=True)

with time_col:
    st.subheader("Partidos jugados a través del tiempo")
    time_df = my_results.copy()
    time_df["Partidos acumulados"] = range(1, len(time_df) + 1)
    time_df["Fecha"] = time_df["date"].dt.strftime("%d-%b").map(football_data.to_spanish_date)
    # one point per day (last cumulative value of that day)
    time_df = time_df.drop_duplicates("Fecha", keep="last").set_index("Fecha")[["Partidos acumulados"]]
    st.line_chart(time_df)

st.divider()

st.subheader("Desempeño por equipo")
stage_reached = bonuses_df.set_index("team")["stage_reached"] if not bonuses_df.empty else None

team_stats = my_results.groupby("team").agg(
    PJ=("result", "count"),
    G=("result", lambda s: (s == "W").sum()),
    E=("result", lambda s: (s == "D").sum()),
    P=("result", lambda s: (s == "L").sum()),
    GF=("goals_for", "sum"),
    GC=("goals_against", "sum"),
    Pts=("points", "sum"),
).reset_index()
team_stats["DG"] = team_stats["GF"] - team_stats["GC"]
team_stats["Etapa Alcanzada"] = team_stats["team"].map(stage_reached) if stage_reached is not None else "-"
team_stats["Etapa Alcanzada"] = team_stats["Etapa Alcanzada"].fillna("Grupos")
team_stats = team_stats.rename(columns={"team": "Equipo"})
team_stats = team_stats.sort_values("Pts", ascending=False)

st.dataframe(
    team_stats[["Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts", "Etapa Alcanzada"]],
    use_container_width=True,
    hide_index=True,
)
