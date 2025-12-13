import math
from collections import deque
from enum import Enum
from typing import AsyncGenerator, List, Optional

from pydantic import BaseModel

from crawler_v2 import crawl_match_data_stream
from momentum.calculate import MomentumUsedStats, TeamMomentumStats


# =====================================
# ENUM DECAY
# =====================================
class LambdaEnumForDuration(float, Enum):
    FIVE_MINUTES = math.log(2) / 120  # ~0.00577


# =====================================
# DATA MODELS (Y NGUYÊN TỪ BẢN GỐC)
# =====================================
# class MomentumUsedStats(BaseModel):
#     goals: int
#     shots_on_target: int
#     shots_inside_box: int
#     shots_headed: int
#     shots_outside_box: int
#     shots_blocked: int
#     key_passes: int
#     through_balls: int
#     penalty_area_entries: int
#     open_play_crosses: int
#     final_thirds_entries: int
#     dribbles_success: int
#     corners_won: int
#     fouls_won: int
#     possession_lost_defensive: int
#     possession_lost_midfield: int
#     offsides: int
#     ball_recoveries_attacking: int
#     interceptions: int
#     tackles: int
#     ball_recoveries_midfield: int
#     ball_recoveries_defensive: int
#     clearances: int
#     fouls_conceded: int
#     cards_yellow: int
#     cards_red: int


# class TeamMomentumStats(BaseModel):
#     time_in_match: str
#     stats: MomentumUsedStats


# =====================================
# TIME HELPERS (Y NGUYÊN BẢN GỐC)
# =====================================
async def convert_to_seconds(t: str) -> int:
    if "+" in t:
        main, extra = t.split("+")
        em, es = extra.split(":")
        return int(main) * 60 + int(em) * 60 + int(es)
    m, s = t.split(":")
    return int(m) * 60 + int(s)


async def calculate_difference_time(
    previous_time: str,
    current_time: str,
    first_half_end_time: Optional[str] = None,
) -> int:
    prev_sec = await convert_to_seconds(previous_time)
    curr_sec = await convert_to_seconds(current_time)

    # rollover hiệp 1 → hiệp 2
    if "+" in previous_time and "+" not in current_time:
        if first_half_end_time:
            fh_end_sec = await convert_to_seconds(first_half_end_time)
            forty_five = await convert_to_seconds("45:00")
            return (fh_end_sec - prev_sec) + curr_sec - forty_five
        return 1

    return curr_sec - prev_sec


# =====================================
# STATS DIFFERENCE (CHUẨN GỐC)
# =====================================
async def calculate_difference_stats(
    prev: MomentumUsedStats, cur: MomentumUsedStats
) -> MomentumUsedStats:
    fields = prev.model_fields.keys()
    diffs = {f: getattr(cur, f) - getattr(prev, f) for f in fields}
    return MomentumUsedStats(**diffs)


# =====================================
# THREAT SCORE (CHUẨN 100% CÔNG THỨC GỐC)
# =====================================
async def calculate_threat_score(
    actions: List[TeamMomentumStats],
    lambda_value: LambdaEnumForDuration,
    current_time: str,
) -> float:
    score = 100.0  # baseline như bản gốc

    for act in actions:
        s = act.stats

        base = 100.0 * (
            s.goals * 1.0
            + s.shots_on_target * 0.3
            + s.shots_inside_box * 0.15
            + s.shots_headed * 0.1
            + s.shots_outside_box * 0.04
            + s.shots_blocked * 0.02
            + s.key_passes * 0.12
            + s.through_balls * 0.1
            + s.penalty_area_entries * 0.08
            + s.open_play_crosses * 0.03
            + s.final_thirds_entries * 0.03
            + s.dribbles_success * 0.04
            + s.corners_won * 0.03
            + s.fouls_won * 0.02
            - s.possession_lost_defensive * 0.2
            - s.possession_lost_midfield * 0.05
            - s.offsides * 0.03
            + s.ball_recoveries_attacking * 0.15
            + s.interceptions * 0.1
            + s.tackles * 0.03
            + s.ball_recoveries_midfield * 0.02
            + s.ball_recoveries_defensive * 0.02
            + s.clearances * 0.01
            - s.fouls_conceded * 0.04
            - s.cards_yellow * 0.08
            - s.cards_red * 0.5
        )

        dt = await calculate_difference_time(act.time_in_match, current_time)
        decay = math.exp(-lambda_value.value * dt)

        score += base * decay

    return score


# =====================================
# REALTIME MOMENTUM LOOP (CHUẨN GỐC)
# =====================================
async def realtime_momentum_loop(
    match_url: str,
    db_name: str,
) -> AsyncGenerator[dict, None]:
    stream = crawl_match_data_stream(match_url=match_url, db_name=db_name)

    home_window = deque()
    away_window = deque()

    prev_home: Optional[MomentumUsedStats] = None
    prev_away: Optional[MomentumUsedStats] = None

    first_half_end: Optional[str] = None
    lambda_value = LambdaEnumForDuration.FIVE_MINUTES
    WINDOW_SECONDS = 600  # 10 phút

    async for home_tick, away_tick in stream:
        # đánh dấu khi vào stoppage-time hiệp 1
        if "+" in home_tick.time_in_match:
            first_half_end = home_tick.time_in_match
        # ------------------------------------
        print(f"Processing stats: {home_tick.stats}")
        print(f"Processing stats: {away_tick.stats}")

        # --------- DELTA CALCULATION ----------
        if prev_home is None:
            delta_home = home_tick.stats
            delta_away = away_tick.stats
        else:
            delta_home = await calculate_difference_stats(prev_home, home_tick.stats)
            delta_away = await calculate_difference_stats(prev_away, away_tick.stats)
            # DEBUG LOG — KIỂM TRA INPUT TRUYỀN VÀO MOMENTUM
            print("\n========== DEBUG MOMENTUM INPUT ==========")
            print(f"⏱ Time: {home_tick.time_in_match}")

            print("\n--- Δ HOME (delta_home) ---")
            print(delta_home.model_dump())

            print("\n--- Δ AWAY (delta_away) ---")
            print(delta_away.model_dump())

            print("\n--- HOME WINDOW (last 10 min actions) ---")
            for i, act in enumerate(home_window):
                print(f"Home[{i}] {act.time_in_match} : {act.stats.model_dump()}")

            print("\n--- AWAY WINDOW (last 10 min actions) ---")
            for i, act in enumerate(away_window):
                print(f"Away[{i}] {act.time_in_match} : {act.stats.model_dump()}")
            print("==========================================\n")

        prev_home = home_tick.stats
        prev_away = away_tick.stats

        # push vào windows (model_copy để fix Pydantic 2)
        home_window.append(
            TeamMomentumStats(
                time_in_match=home_tick.time_in_match,
                stats=delta_home,  # FIXED — không wrap lại
            )
        )

        away_window.append(
            TeamMomentumStats(
                time_in_match=away_tick.time_in_match,
                stats=delta_away,  # FIXED
            )
        )
        # --------- TRIM 10-MIN WINDOW ----------
        while len(home_window) > 1:
            dt = await calculate_difference_time(
                home_window[0].time_in_match,
                home_tick.time_in_match,
                first_half_end,
            )
            if dt > WINDOW_SECONDS:
                home_window.popleft()
            else:
                break

        while len(away_window) > 1:
            dt = await calculate_difference_time(
                away_window[0].time_in_match,
                away_tick.time_in_match,
                first_half_end,
            )
            if dt > WINDOW_SECONDS:
                away_window.popleft()
            else:
                break

        # --------- THREAT SCORE ----------
        home_threat = await calculate_threat_score(
            home_window, lambda_value, home_tick.time_in_match
        )
        away_threat = await calculate_threat_score(
            away_window, lambda_value, away_tick.time_in_match
        )

        total = home_threat + away_threat
        momentum = (home_threat / total * 100) if total != 0 else 50.0

        print(
            f"[{home_tick.time_in_match}] "
            f"Momentum={momentum:.2f} | "
            f"Home={home_threat:.2f} | "
            f"Away={away_threat:.2f}"
        )

        yield {
            "time": home_tick.time_in_match,
            "home_threat": round(home_threat, 2),
            "away_threat": round(away_threat, 2),
            "momentum_index": round(momentum, 2),
        }
