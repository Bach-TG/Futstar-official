from enum import Enum


class MatchStatus(str, Enum):
    SCHEDULED = "Scheduled"
    LIVE = "Live"
    ENDED = "Ended"
    TESTING = "Testing"

class PositionDuration(str, Enum):
    THIRTY_SECONDS = "30s"
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    TWO_MINUTES = "2m"
    THREE_MINUTES = "3m"
    TEN_MINUTES = "10m"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def to_seconds(cls, duration: str) -> int:
        mapping = {
            cls.THIRTY_SECONDS.value: 30,
            cls.ONE_MINUTE.value: 60,
            cls.TWO_MINUTES.value: 120,
            cls.THREE_MINUTES.value: 180,
            cls.FIVE_MINUTES.value: 300,
            cls.TEN_MINUTES.value: 600,
        }
        return mapping.get(duration, 0)


class MissionType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SPECIAL = "special"
    SOCIAL = "social"
    BEGINNER = "beginner"
    CHALLENGE = "challenge"
    RETENTION = "retention"


class SocialUrl(str, Enum):
    TWITTER_URL = "https://x.com/Futstarfun"
    TELEGRAM_URL = "https://t.me/Futstar_fun"
    DISCORD_URL = "https://discord.gg/futstar"