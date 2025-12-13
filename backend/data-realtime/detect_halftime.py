# =====================================================
# HALF-TIME / FULL-TIME DETECTOR
# =====================================================


class MatchState:
    def __init__(self):
        self.last_time = None
        self.last_stats = None
        self.freeze_count = 0
        self.state = "PLAYING"


def hash_stats(stats_all: dict) -> int:
    try:
        return hash(str(stats_all))
    except:
        return 0


async def detect_pause(
    state: MatchState, time_text: str, stats_all: dict
) -> str | None:
    HALF_TIME_TOKENS = {"HT", "Half time", "Halftime", "Break"}

    # Rule 1: Literal half-time text
    if time_text in HALF_TIME_TOKENS:
        state.state = "HALF_TIME"
        return "HALF_TIME"

    # Compute hash
    stats_hash = hash_stats(stats_all)

    # Detect freeze
    if state.last_time == time_text and state.last_stats == stats_hash:
        state.freeze_count += 1
    else:
        state.freeze_count = 0

    state.last_time = time_text
    state.last_stats = stats_hash

    # ===========================
    # Detect Half-time (45:00 freeze only)
    # ===========================
    if time_text.startswith("45:") and "+" not in time_text and state.freeze_count >= 4:
        state.state = "HALF_TIME"
        return "HALF_TIME"

    # ===========================
    # Detect Full-time
    # ===========================
    if time_text.startswith("90") and state.freeze_count >= 8:
        state.state = "FULL_TIME"
        return "FULL_TIME"

    # ===========================
    # Overtime (45+X / 90+X)
    # — NEVER pause
    # ===========================
    return None
