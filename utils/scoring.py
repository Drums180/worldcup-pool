import pandas as pd

from utils.football_data import FINISHED_STATUSES

MATCH_POINTS = {"W": 3, "D": 1, "L": 0}

# Bonus points for the furthest stage a team reaches
STAGE_BONUSES = {
    "Octavos": 2,
    "Cuartos": 4,
    "Semifinal": 6,
    "Final": 8,
    "Campeón": 12,
}

# A win in `stage` means the team advances to (reaches) the mapped stage
STAGE_PROGRESSION = {
    "Dieciseisavos": "Octavos",
    "Octavos": "Cuartos",
    "Cuartos": "Semifinal",
    "Semifinal": "Final",
    "Final": "Campeón",
}

STAGE_ORDER = ["Octavos", "Cuartos", "Semifinal", "Final", "Campeón"]


def normalize_picks(picks_df: pd.DataFrame) -> pd.DataFrame:
    """Convert a wide Picks/Equipos sheet (Persona, Equipo 1..8) to long format
    with one row per (persona, team). Already-long sheets pass through."""
    if picks_df.empty:
        return pd.DataFrame(columns=["persona", "team"])

    columns = list(picks_df.columns)
    if "persona" in columns and "team" in columns:
        return picks_df[["persona", "team"]]

    persona_col = columns[0]
    team_cols = columns[1:]
    long_df = picks_df.melt(
        id_vars=persona_col, value_vars=team_cols, value_name="team"
    )
    long_df = long_df.rename(columns={persona_col: "persona"})
    long_df["team"] = long_df["team"].astype(str).str.strip()
    long_df = long_df[long_df["team"] != ""]
    return long_df[["persona", "team"]].reset_index(drop=True)


def build_resultados(fixtures_df: pd.DataFrame) -> pd.DataFrame:
    """One row per team per finished fixture, with W/D/L result and match points."""
    columns = [
        "fixture_id", "team", "opponent", "stage", "status", "result", "points",
        "date", "goals_for", "goals_against",
    ]
    if fixtures_df.empty:
        return pd.DataFrame(columns=columns)

    finished = fixtures_df[fixtures_df["status"].isin(FINISHED_STATUSES)].copy()
    finished["date"] = pd.to_datetime(finished["date"])
    rows = []
    for _, f in finished.iterrows():
        home_goals, away_goals = f["home_goals"], f["away_goals"]
        if home_goals > away_goals:
            home_result, away_result = "W", "L"
        elif home_goals < away_goals:
            home_result, away_result = "L", "W"
        else:
            home_result, away_result = "D", "D"

        rows.append({
            "fixture_id": f["fixture_id"], "team": f["home_team"], "opponent": f["away_team"],
            "stage": f["stage"], "status": "FT", "result": home_result,
            "points": MATCH_POINTS[home_result],
            "date": f["date"], "goals_for": home_goals, "goals_against": away_goals,
        })
        rows.append({
            "fixture_id": f["fixture_id"], "team": f["away_team"], "opponent": f["home_team"],
            "stage": f["stage"], "status": "FT", "result": away_result,
            "points": MATCH_POINTS[away_result],
            "date": f["date"], "goals_for": away_goals, "goals_against": home_goals,
        })

    return pd.DataFrame(rows, columns=columns)


def build_bonuses(fixtures_df: pd.DataFrame) -> pd.DataFrame:
    """Furthest elimination stage each team has reached, with its bonus points."""
    columns = ["team", "stage_reached", "bonus_points"]
    if fixtures_df.empty:
        return pd.DataFrame(columns=columns)

    finished = fixtures_df[fixtures_df["status"].isin(FINISHED_STATUSES)]
    reached: dict[str, str] = {}

    for _, f in finished.iterrows():
        next_stage = STAGE_PROGRESSION.get(f["stage"])
        if not next_stage:
            continue

        winner = None
        if f["home_winner"] is True:
            winner = f["home_team"]
        elif f["away_winner"] is True:
            winner = f["away_team"]
        if winner is None:
            continue

        current = reached.get(winner)
        if current is None or STAGE_ORDER.index(next_stage) > STAGE_ORDER.index(current):
            reached[winner] = next_stage

    rows = [
        {"team": team, "stage_reached": stage, "bonus_points": STAGE_BONUSES[stage]}
        for team, stage in reached.items()
    ]
    return pd.DataFrame(rows, columns=columns)


def build_history(fixtures_df: pd.DataFrame, picks_long: pd.DataFrame) -> pd.DataFrame:
    """Cumulative point totals per person, one row per person per matchday date,
    reconstructed from each finished fixture's real date."""
    columns = ["date", "persona", "total"]
    if fixtures_df.empty or picks_long.empty:
        return pd.DataFrame(columns=columns)

    finished = fixtures_df[fixtures_df["status"].isin(FINISHED_STATUSES)].copy()
    if finished.empty:
        return pd.DataFrame(columns=columns)

    finished["date"] = pd.to_datetime(finished["date"]).dt.date
    finished = finished.sort_values("date")

    team_to_persona = picks_long.set_index("team")["persona"].to_dict()
    totals = {persona: 0 for persona in picks_long["persona"].unique()}
    team_bonus: dict = {}
    rows = []

    for date, day_fixtures in finished.groupby("date"):
        for _, f in day_fixtures.iterrows():
            home_goals, away_goals = f["home_goals"], f["away_goals"]
            if home_goals > away_goals:
                home_result, away_result = "W", "L"
            elif home_goals < away_goals:
                home_result, away_result = "L", "W"
            else:
                home_result, away_result = "D", "D"

            for team, result in ((f["home_team"], home_result), (f["away_team"], away_result)):
                persona = team_to_persona.get(team)
                if persona:
                    totals[persona] += MATCH_POINTS[result]

            next_stage = STAGE_PROGRESSION.get(f["stage"])
            if next_stage:
                winner = None
                if f["home_winner"] is True:
                    winner = f["home_team"]
                elif f["away_winner"] is True:
                    winner = f["away_team"]
                if winner:
                    new_bonus = STAGE_BONUSES[next_stage]
                    delta = new_bonus - team_bonus.get(winner, 0)
                    if delta:
                        persona = team_to_persona.get(winner)
                        if persona:
                            totals[persona] += delta
                        team_bonus[winner] = new_bonus

        for persona, total in totals.items():
            rows.append({"date": date, "persona": persona, "total": total})

    return pd.DataFrame(rows, columns=columns)


def compute_leaderboard(
    picks_long: pd.DataFrame, resultados_df: pd.DataFrame, bonuses_df: pd.DataFrame
) -> pd.DataFrame:
    """Per-person totals: match points (sum over their 8 teams) + elimination bonuses."""
    if picks_long.empty:
        return pd.DataFrame(columns=["persona", "match_points", "bonus_points", "total"])

    match_pts = (
        resultados_df.groupby("team")["points"].sum() if not resultados_df.empty else pd.Series(dtype="int64")
    )
    bonus_pts = (
        bonuses_df.set_index("team")["bonus_points"] if not bonuses_df.empty else pd.Series(dtype="int64")
    )

    picks_long = picks_long.copy()
    picks_long["match_points"] = picks_long["team"].map(match_pts).fillna(0).astype(int)
    picks_long["bonus_points"] = picks_long["team"].map(bonus_pts).fillna(0).astype(int)
    picks_long["total"] = picks_long["match_points"] + picks_long["bonus_points"]

    summary = picks_long.groupby("persona")[["match_points", "bonus_points", "total"]].sum().reset_index()
    return summary.sort_values("total", ascending=False).reset_index(drop=True)
