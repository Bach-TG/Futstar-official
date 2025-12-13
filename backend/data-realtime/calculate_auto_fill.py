import math
from collections import deque
from enum import Enum
from typing import AsyncGenerator, Optional, Tuple

from crawler_v2 import crawl_match_data_stream
from momentum.calculate import MomentumUsedStats, TeamMomentumStats


# ============================================================
# SAME LAMBDA AS OFFLINE (exact value)
# ============================================================
class LambdaEnumForDuration(float, Enum):
    FIVE_MINUTES = math.log(2) / 120  # EXACT offline value


# ============================================================
# TIME PARSER (EXACT MATCH w/ OFFLINE)
# ============================================================
def to_seconds(t: str) -> int:
    """
    Hỗ trợ:
      - 12:30
      - 45:00+3:12
      - 90:00+4:15
    """
    t = t.strip()

    if "+" in t:
        base, extra = t.split("+")
        base = base.strip()
        extra = extra.strip()

        m1, s1 = map(int, base.split(":"))
        m2, s2 = map(int, extra.split(":"))

        return m1 * 60 + s1 + m2 * 60 + s2

    # mm:ss
    m, s = map(int, t.split(":"))
    return m * 60 + s


# ============================================================
# SAME AS OFFLINE — difference time
# ============================================================
async def calculate_difference_time(
    previous_time: str,
    current_time: str,
    first_half_end_time: Optional[str],
) -> int:
    prev_sec = to_seconds(previous_time)
    curr_sec = to_seconds(current_time)

    # special case:
    # previous = "45:00+X"
    # current  = "mm:ss" (start of 2nd half)
    if ("+" in previous_time) and ("+" not in current_time):
        if first_half_end_time:
            fhe = to_seconds(first_half_end_time)  # exact end of 1st half
            extra_first_half = fhe - prev_sec  # remaining ET of 1st half
            after_ht = curr_sec - (45 * 60)
            return extra_first_half + after_ht
        else:
            return curr_sec - prev_sec

    return curr_sec - prev_sec


# ============================================================
# SAME AS OFFLINE — difference stats
# ============================================================
async def calculate_difference_stats(
    previous_stats: MomentumUsedStats,
    current_stats: MomentumUsedStats,
) -> MomentumUsedStats:
    return MomentumUsedStats(
        goals=current_stats.goals - previous_stats.goals,
        shots_on_target=current_stats.shots_on_target - previous_stats.shots_on_target,
        shots_inside_box=current_stats.shots_inside_box
        - previous_stats.shots_inside_box,
        shots_headed=current_stats.shots_headed - previous_stats.shots_headed,
        shots_outside_box=current_stats.shots_outside_box
        - previous_stats.shots_outside_box,
        shots_blocked=current_stats.shots_blocked - previous_stats.shots_blocked,
        key_passes=current_stats.key_passes - previous_stats.key_passes,
        through_balls=current_stats.through_balls - previous_stats.through_balls,
        penalty_area_entries=current_stats.penalty_area_entries
        - previous_stats.penalty_area_entries,
        open_play_crosses=current_stats.open_play_crosses
        - previous_stats.open_play_crosses,
        final_thirds_entries=current_stats.final_thirds_entries
        - previous_stats.final_thirds_entries,
        dribbles_success=current_stats.dribbles_success
        - previous_stats.dribbles_success,
        corners_won=current_stats.corners_won - previous_stats.corners_won,
        fouls_won=current_stats.fouls_won - previous_stats.fouls_won,
        possession_lost_defensive=current_stats.possession_lost_defensive
        - previous_stats.possession_lost_defensive,
        possession_lost_midfield=current_stats.possession_lost_midfield
        - previous_stats.possession_lost_midfield,
        offsides=current_stats.offsides - previous_stats.offsides,
        ball_recoveries_attacking=current_stats.ball_recoveries_attacking
        - previous_stats.ball_recoveries_attacking,
        interceptions=current_stats.interceptions - previous_stats.interceptions,
        tackles=current_stats.tackles - previous_stats.tackles,
        ball_recoveries_midfield=current_stats.ball_recoveries_midfield
        - previous_stats.ball_recoveries_midfield,
        ball_recoveries_defensive=current_stats.ball_recoveries_defensive
        - previous_stats.ball_recoveries_defensive,
        clearances=current_stats.clearances - previous_stats.clearances,
        fouls_conceded=current_stats.fouls_conceded - previous_stats.fouls_conceded,
        cards_yellow=current_stats.cards_yellow - previous_stats.cards_yellow,
        cards_red=current_stats.cards_red - previous_stats.cards_red,
    )


# ============================================================
# SAME AS OFFLINE — threat score
# ============================================================
async def calculate_threat_score(
    action_list: list[TeamMomentumStats],
    lambda_value: LambdaEnumForDuration,
    current_time: str,
) -> float:
    threat_score = 100.0
    curr_sec = to_seconds(current_time)

    for action in action_list:
        s = action.stats

        threat_contribution = 100.0 * (
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
            + s.ball_recoveries_attacking * 0.15
            + s.interceptions * 0.1
            + s.tackles * 0.03
            + s.ball_recoveries_midfield * 0.02
            + s.ball_recoveries_defensive * 0.02
            + s.clearances * 0.01
            - s.possession_lost_defensive * 0.2
            - s.possession_lost_midfield * 0.05
            - s.offsides * 0.03
            - s.fouls_conceded * 0.04
            - s.cards_yellow * 0.08
            - s.cards_red * 0.5
        )

        dt = curr_sec - to_seconds(action.time_in_match)
        decay = math.exp(-lambda_value.value * dt)

        threat_score += threat_contribution * decay

    return threat_score


# ============================================================
# FINAL REALTIME LOOP (100% offline formula)
# ============================================================
async def realtime_momentum_loop(
    match_url: str,
    db_name: str,
) -> AsyncGenerator[dict, None]:
    crawler_stream = crawl_match_data_stream(match_url=match_url, db_name=db_name)

    # FIRST TICK
    (
        first_time,
        first_half,
        first_home,
        first_away,
    ) = await crawler_stream.__anext__()

    print(f"[RealtimeLoop] First tick: {first_time}")

    prev_home = first_home.stats
    prev_away = first_away.stats

    home_window = deque()
    away_window = deque()

    first_half_end_time = None
    WINDOW_SECONDS = 600
    lambda_value = LambdaEnumForDuration.FIVE_MINUTES
    last_momentum = 0
    # last_time = "0"
    # Emit initial
    yield {
        "time_in_match": first_time,
        "home_goals": first_home.stats.goals,
        "away_goals": first_away.stats.goals,
        "momentum_value": 50.0,
    }

    # MAIN LOOP
    async for t_time, t_half, t_home, t_away in crawler_stream:
        if t_time == "Half Time":
            yield {
                "time_in_match": "Half Time",
                "home_goals": t_home.stats.goals,
                "away_goals": t_away.stats.goals,
                "momentum_value": 50,
            }
            continue
        if t_time == "Full Time":
            yield {
                "time_in_match": "Full Time",
                "home_goals": t_home.stats.goals,
                "away_goals": t_away.stats.goals,
                "momentum_value": last_momentum,
            }
            break
        # if last_time == t_time:
        #     continue

        # detect first half end
        if ("+" in t_time) and not first_half_end_time:
            first_half_end_time = t_time

        # delta stats
        delta_home = await calculate_difference_stats(prev_home, t_home.stats)
        delta_away = await calculate_difference_stats(prev_away, t_away.stats)

        prev_home = t_home.stats
        prev_away = t_away.stats

        home_window.append(TeamMomentumStats(time_in_match=t_time, stats=delta_home))
        away_window.append(TeamMomentumStats(time_in_match=t_time, stats=delta_away))

        # window trim
        while (
            home_window
            and (
                await calculate_difference_time(
                    home_window[0].time_in_match,
                    t_time,
                    first_half_end_time,
                )
            )
            > WINDOW_SECONDS
        ):
            home_window.popleft()

        while (
            away_window
            and (
                await calculate_difference_time(
                    away_window[0].time_in_match,
                    t_time,
                    first_half_end_time,
                )
            )
            > WINDOW_SECONDS
        ):
            away_window.popleft()

        # threat
        home_thr = await calculate_threat_score(home_window, lambda_value, t_time)
        away_thr = await calculate_threat_score(away_window, lambda_value, t_time)

        total = home_thr + away_thr
        momentum = home_thr / total * 100 if total else 50.0
        last_momentum = momentum
        # last_time = t_time
        yield {
            "time_in_match": t_time,
            "home_goals": t_home.stats.goals,
            "away_goals": t_away.stats.goals,
            "momentum_value": round(momentum, 2),
        }
