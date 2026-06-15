from typing import Optional

import pandas as pd

# Resolution of every group-stage "self-matchup" (a match where both teams belong
# to the same person). For each one, one team stays with its original owner and
# the other is temporarily loaned to a different player for that match's group-stage
# points only. Assignment generated with seed=180 (random team-kept choice, then a
# seeded shuffle + backtracking search for a valid receiver assignment honoring the
# loan quotas: David 1, Elizabeth 1, Marcos 2, Marian 1, Mateo 3, Mayeli 3) so it is
# reproducible and fixed regardless of when the app reloads.
LOANS = [
    {"fixture_id": 537334, "match": "Qatar vs Suiza", "owner": "Mateo", "team_kept": "Qatar", "team_loaned": "Suiza", "receiver": "Marcos"},
    {"fixture_id": 537370, "match": "Arabia Saudita vs Uruguay", "owner": "Mayeli", "team_kept": "Uruguay", "team_loaned": "Arabia Saudita", "receiver": "Mateo"},
    {"fixture_id": 537348, "match": "Estados Unidos vs Australia", "owner": "Marcos", "team_kept": "Australia", "team_loaned": "Estados Unidos", "receiver": "Elizabeth"},
    {"fixture_id": 537354, "match": "Ecuador vs Curazao", "owner": "Marian", "team_kept": "Ecuador", "team_loaned": "Curazao", "receiver": "Mayeli"},
    {"fixture_id": 537371, "match": "España vs Arabia Saudita", "owner": "Mayeli", "team_kept": "Arabia Saudita", "team_loaned": "España", "receiver": "Mateo"},
    {"fixture_id": 537393, "match": "Francia vs Irak", "owner": "Mateo", "team_kept": "Francia", "team_loaned": "Irak", "receiver": "Marian"},
    {"fixture_id": 537405, "match": "Portugal vs Uzbekistán", "owner": "Marcos", "team_kept": "Portugal", "team_loaned": "Uzbekistán", "receiver": "David"},
    {"fixture_id": 537406, "match": "Colombia vs RD Congo", "owner": "Mateo", "team_kept": "Colombia", "team_loaned": "RD Congo", "receiver": "Mayeli"},
    {"fixture_id": 537361, "match": "Túnez vs Países Bajos", "owner": "Elizabeth", "team_kept": "Países Bajos", "team_loaned": "Túnez", "receiver": "Mayeli"},
    {"fixture_id": 537373, "match": "Uruguay vs España", "owner": "Mayeli", "team_kept": "Uruguay", "team_loaned": "España", "receiver": "Marcos"},
    {"fixture_id": 537413, "match": "Panamá vs Inglaterra", "owner": "David", "team_kept": "Panamá", "team_loaned": "Inglaterra", "receiver": "Mateo"},
]

LOAN_QUOTAS = {"David": 1, "Elizabeth": 1, "Marcos": 2, "Marian": 1, "Mateo": 3, "Mayeli": 3}


def loans_df() -> pd.DataFrame:
    return pd.DataFrame(LOANS)


def get_loan(fixture_id: int, team: str) -> Optional[dict]:
    """Return the loan affecting this team's result in this fixture, if any."""
    for loan in LOANS:
        if loan["fixture_id"] == fixture_id and loan["team_loaned"] == team:
            return loan
    return None
