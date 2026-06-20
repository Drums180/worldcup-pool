import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from utils import football_data, loans as loans_mod, scoring, sheets

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

# Build loan-adjusted result set:
# - owned team results minus fixtures where that team was loaned out
# - plus results for teams loaned TO this persona
if resultados_df.empty:
    my_results = pd.DataFrame(columns=resultados_df.columns)
else:
    team_to_persona = picks_long.set_index("team")["persona"].to_dict()

    def scoring_persona(row):
        orig = team_to_persona.get(row["team"])
        if orig is None:
            return None
        for loan in loans_mod.LOANS:
            if loan["fixture_id"] == row["fixture_id"] and loan["team_loaned"] == row["team"]:
                return loan["receiver"]
        return orig

    mask = resultados_df.apply(scoring_persona, axis=1) == persona
    my_results = resultados_df[mask].copy()

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
    result_data = [
        (v, f"{l} ({v / played:.0%})", c)
        for v, l, c in [
            (won, "Ganados", "#2ecc71"),
            (drawn, "Empatados", "#f1c40f"),
            (lost, "Perdidos", "#e74c3c"),
        ]
        if v > 0
    ]
    if result_data:
        values, labels, colors = zip(*result_data)
        fig, ax = plt.subplots(figsize=(4, 4))
        wedges, _ = ax.pie(
            list(values),
            colors=list(colors),
            startangle=90,
            wedgeprops={"width": 0.5},
        )
        ax.legend(wedges, list(labels), loc="center left", bbox_to_anchor=(0.85, 0.5), fontsize=9)
        ax.axis("equal")
        st.pyplot(fig)
        plt.close(fig)

with time_col:
    st.subheader("Partidos jugados a través del tiempo")
    time_df = my_results.copy()
    time_df["Partidos acumulados"] = range(1, len(time_df) + 1)
    time_df["Fecha"] = time_df["date"].dt.strftime("%d-%b").map(football_data.to_spanish_date)
    time_df = time_df.drop_duplicates("Fecha", keep="last")
    fig2, ax2 = plt.subplots(figsize=(5, 3))
    ax2.plot(time_df["Fecha"].tolist(), time_df["Partidos acumulados"].tolist(), marker="o", color="#3498db")
    ax2.set_ylabel("Partidos acumulados")
    ax2.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

st.divider()

st.subheader("Desempeño por equipo")
stage_reached = bonuses_df.set_index("team")["stage_reached"] if not bonuses_df.empty else None

# Teams in my_results not owned by this persona are received loans
received_loan_teams = set(my_results["team"].unique()) - set(my_teams)

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
team_stats["Equipo"] = team_stats["team"].apply(
    lambda t: f"{t} (préstamo)" if t in received_loan_teams else t
)
team_stats = team_stats.sort_values("Pts", ascending=False)

st.dataframe(
    team_stats[["Equipo", "PJ", "G", "E", "P", "GF", "GC", "DG", "Pts", "Etapa Alcanzada"]],
    use_container_width=True,
    hide_index=True,
)
