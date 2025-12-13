from enum import Enum
from typing import Optional


class TransfermarktAPI:
    """Centralized API endpoint manager with URL builder methods"""

    BASE_URL: str = "https://transfermarkt-api.fly.dev"

    class Competition:
        """Competition related endpoints"""

        SEARCH: str = "/competitions/search/{competition_name}"
        GET_CLUBS: str = "/competitions/{competition_id}/clubs"

        @staticmethod
        def search(competition_name: str) -> str:
            """
            Get competition search URL

            Args:
                competition_name: Name of the competition to search

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Competition.SEARCH.format(competition_name=competition_name)}"

        @staticmethod
        def get_clubs(competition_id: str) -> str:
            """
            Get clubs in a competition

            Args:
                competition_id: ID of the competition

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Competition.GET_CLUBS.format(competition_id=competition_id)}"

    class Club:
        """Club related endpoints"""

        SEARCH: str = "/clubs/search/{club_name}"
        PROFILE: str = "/clubs/{club_id}/profile"
        PLAYERS: str = "/clubs/{club_id}/players"

        @staticmethod
        def search(club_name: str) -> str:
            """
            Get club search URL

            Args:
                club_name: Name of the club to search

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Club.SEARCH.format(club_name=club_name)}"

        @staticmethod
        def profile(club_id: str) -> str:
            """
            Get club profile URL

            Args:
                club_id: ID of the club

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Club.PROFILE.format(club_id=club_id)}"

        @staticmethod
        def players(club_id: str) -> str:
            """
            Get club players URL

            Args:
                club_id: ID of the club

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Club.PLAYERS.format(club_id=club_id)}"

    class Player:
        """Player related endpoints"""

        SEARCH: str = "/players/search/{player_name}"
        PROFILE: str = "/players/{player_id}/profile"
        MARKET_VALUE: str = "/players/{player_id}/market_value"
        TRANSFERS: str = "/players/{player_id}/transfers"
        JERSEY_NUMBERS: str = "/players/{player_id}/jersey_numbers"
        STATS: str = "/players/{player_id}/stats"
        INJURIES: str = "/players/{player_id}/injuries"
        ACHIEVEMENTS: str = "/players/{player_id}/achievements"

        @staticmethod
        def search(player_name: str) -> str:
            """
            Get player search URL

            Args:
                player_name: Name of the player to search

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.SEARCH.format(player_name=player_name)}"

        @staticmethod
        def profile(player_id: str) -> str:
            """
            Get player profile URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.PROFILE.format(player_id=player_id)}"

        @staticmethod
        def market_value(player_id: int) -> str:
            """
            Get player market value URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.MARKET_VALUE.format(player_id=player_id)}"

        @staticmethod
        def transfers(player_id: int) -> str:
            """
            Get player transfers URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.TRANSFERS.format(player_id=player_id)}"

        @staticmethod
        def jersey_numbers(player_id: int) -> str:
            """
            Get player jersey numbers URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.JERSEY_NUMBERS.format(player_id=player_id)}"

        @staticmethod
        def stats(player_id: int) -> str:
            """
            Get player stats URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.STATS.format(player_id=player_id)}"

        @staticmethod
        def injuries(player_id: int) -> str:
            """
            Get player injuries URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.INJURIES.format(player_id=player_id)}"

        @staticmethod
        def achievements(player_id: int) -> str:
            """
            Get player achievements URL

            Args:
                player_id: ID of the player

            Returns:
                Complete URL string
            """
            return f"{TransfermarktAPI.BASE_URL}{TransfermarktAPI.Player.ACHIEVEMENTS.format(player_id=player_id)}"
