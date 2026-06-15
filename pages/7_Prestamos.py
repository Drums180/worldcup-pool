import pandas as pd
import streamlit as st

from utils import football_data, loans, scoring, sheets

st.title("🔄 Préstamos de Equipos Auto-enfrentados")

st.write(
    "Cuando los 8 equipos de una persona incluyen dos que se enfrentan entre sí, "
    "uno se queda con su dueño original y el otro se presta temporalmente a otra "
    "persona, solo para los puntos de fase de grupos de ese partido. Los bonos de "
    "eliminación siempre se quedan con el dueño original."
)

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

resultados_df = scoring.build_resultados(fixtures_df)
bonuses_df = scoring.build_bonuses(fixtures_df)

fixtures_by_id = fixtures_df.set_index("fixture_id")
results_by_team_fixture = (
    resultados_df.set_index(["fixture_id", "team"]) if not resultados_df.empty else None
)

st.subheader("Asignación de préstamos")
rows = []
for loan in loans.LOANS:
    fixture = fixtures_by_id.loc[loan["fixture_id"]]
    status = football_data.translate_status(fixture["status"])
    if pd.notna(fixture["home_goals"]) and pd.notna(fixture["away_goals"]):
        score = f"{int(fixture['home_goals'])} - {int(fixture['away_goals'])}"
    else:
        score = "-"

    points = "-"
    if results_by_team_fixture is not None:
        try:
            row = results_by_team_fixture.loc[(loan["fixture_id"], loan["team_loaned"])]
            points = str(int(row["points"]))
        except KeyError:
            pass

    rows.append({
        "Partido": loan["match"],
        "Dueño Original": loan["owner"],
        "Equipo que se queda": loan["team_kept"],
        "Equipo prestado": loan["team_loaned"],
        "Receptor Temporal": loan["receiver"],
        "Estado": status,
        "Marcador": score,
        "Puntos del equipo prestado": points,
    })

loans_table = pd.DataFrame(rows)
st.dataframe(loans_table, use_container_width=True, hide_index=True)

st.subheader("Validación")
quotas = loans.LOAN_QUOTAS
received_counts = loans_table["Receptor Temporal"].value_counts().to_dict()
self_donated_counts = loans_table["Dueño Original"].value_counts().to_dict()

checks = []
checks.append(("Total de préstamos asignados", len(loans.LOANS), 11, len(loans.LOANS) == 11))
for persona, quota in quotas.items():
    received = received_counts.get(persona, 0)
    checks.append((f"Préstamos recibidos por {persona}", received, quota, received == quota))
for loan in loans.LOANS:
    checks.append((
        f"{loan['owner']} no recibe su propio préstamo ({loan['match']})",
        loan["receiver"], f"≠ {loan['owner']}", loan["receiver"] != loan["owner"],
    ))
for persona in quotas:
    appearances = self_donated_counts.get(persona, 0)
    received = received_counts.get(persona, 0)
    total_appearances = 24 - appearances + received
    checks.append((f"Apariciones de fase de grupos de {persona}", total_appearances, 24, total_appearances == 24))

checks_df = pd.DataFrame(checks, columns=["Validación", "Valor", "Esperado", "OK"])
checks_df["Valor"] = checks_df["Valor"].astype(str)
checks_df["Esperado"] = checks_df["Esperado"].astype(str)
checks_df["OK"] = checks_df["OK"].map({True: "✅", False: "❌"})
st.dataframe(checks_df, use_container_width=True, hide_index=True)

if (checks_df["OK"] == "❌").any():
    st.error("Hay validaciones que no se cumplen.")
else:
    st.success("Todas las validaciones se cumplen: 11 préstamos, cuotas exactas, sin auto-préstamos y 24 apariciones por persona.")

st.subheader("Tabla de posiciones: original vs. con préstamos")
original = scoring.compute_leaderboard(picks_long, resultados_df, bonuses_df)
with_loans = scoring.compute_leaderboard_with_loans(picks_long, resultados_df, bonuses_df, loans.LOANS)

comparison = original[["persona", "total"]].rename(columns={"total": "Total Original"}).merge(
    with_loans[["persona", "total"]].rename(columns={"total": "Total con Préstamos"}),
    on="persona",
)
comparison["Diferencia"] = comparison["Total con Préstamos"] - comparison["Total Original"]
comparison = comparison.rename(columns={"persona": "Persona"}).sort_values("Total con Préstamos", ascending=False)
st.dataframe(comparison, use_container_width=True, hide_index=True)
