from enum import Enum


class SupportedCompetition(Enum):
    PREMIER_LEAGUE = "Premier League"
    LA_LIGA = "La Liga"
    SERIE_A = "Serie A"
    BUNDESLIGA = "Bundesliga"
    LIGUE_1 = "Ligue 1"

    @staticmethod
    def list_all_values():
        return list(map(lambda c: c.value, SupportedCompetition))
