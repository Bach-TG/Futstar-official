import argparse
import asyncio
import json
import math
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from mongo.schemas import (
    MatchAttackStats,
    MatchDefenceStats,
    MatchDisciplineStats,
    MatchDistributionStats,
    MatchGeneralStats,
)

MONGO_URL = "mongodb://mongodb:mongodb@131.153.239.187:27037/"


# ============================================================
# MODELS
# ============================================================
class MomentumUsedStats(BaseModel):
    goals: int
    shots_on_target: int
    shots_inside_box: int
    shots_headed: int
    shots_outside_box: int
    shots_blocked: int
    key_passes: int
    through_balls: int
    penalty_area_entries: int
    open_play_crosses: int
    final_thirds_entries: int
    dribbles_success: int
    corners_won: int
    fouls_won: int
    possession_lost_defensive: int
    possession_lost_midfield: int
    offsides: int
    ball_recoveries_attacking: int
    interceptions: int
    tackles: int
    ball_recoveries_midfield: int
    ball_recoveries_defensive: int
    clearances: int
    fouls_conceded: int
    cards_yellow: int
    cards_red: int


class TeamMomentumStats(BaseModel):
    time_in_match: str
    stats: MomentumUsedStats


class TeamThreatScore(BaseModel):
    time_in_match: str
    threat_score: float


# ============================================================
# TIME HELPERS
# ============================================================
def convert_to_seconds(t: str) -> int:
    """
    Chuẩn xử lý thời gian dạng 45+3:10 so với 46:00.
    """
    if "+" in t:
        main, extra = t.split("+")
        mm, ss = extra.split(":")
        return int(main) * 60 + int(mm) * 60 + int(ss)
    else:
        mm, ss = t.split(":")
        return int(mm) * 60 + int(ss)


def is_second_half(t: str) -> bool:
    """
    Hiệp 2 bắt đầu khi gặp timestamp >= 46:00 (không có dấu +).
    """
    if "+" in t:
        return False
    return convert_to_seconds(t) >= 46 * 60


# ============================================================
# LOAD MATCH STATS
# ============================================================
async def load_match_stats(db_name: str):
    client = AsyncIOMotorClient(MONGO_URL)
    await init_beanie(
        database=client[db_name],
        document_models=[
            MatchAttackStats,
            MatchDefenceStats,
            MatchDisciplineStats,
            MatchDistributionStats,
            MatchGeneralStats,
        ],
    )

    attacks = await MatchAttackStats.find_all().to_list()
    defences = await MatchDefenceStats.find_all().to_list()
    disciplines = await MatchDisciplineStats.find_all().to_list()
    distributions = await MatchDistributionStats.find_all().to_list()
    generals = await MatchGeneralStats.find_all().to_list()

    def_map = {x.time_in_match: x for x in defences}
    dis_map = {x.time_in_match: x for x in disciplines}
    dist_map = {x.time_in_match: x for x in distributions}
    gen_map = {x.time_in_match: x for x in generals}

    home_stats, away_stats = [], []

    for a in attacks:
        t = a.time_in_match

        home = MomentumUsedStats(
            goals=a.goals[0],
            shots_on_target=a.shots_on_target[0],
            shots_inside_box=a.shots_inside_box[0],
            shots_headed=a.shots_headed[0],
            shots_outside_box=a.shots_outside_box[0],
            shots_blocked=a.shots_blocked[0],
            key_passes=a.key_passes[0],
            through_balls=dist_map[t].through_balls[0],
            penalty_area_entries=dist_map[t].penalty_area_entries[0],
            open_play_crosses=dist_map[t].open_play_crosses[0],
            final_thirds_entries=dist_map[t].final_thirds_entries[0],
            dribbles_success=gen_map[t].dribbles_success[0],
            corners_won=gen_map[t].corners_won[0],
            fouls_won=gen_map[t].fouls_won[0],
            possession_lost_defensive=gen_map[t].possession_lost_defensive[0],
            possession_lost_midfield=gen_map[t].possession_lost_midfield[0],
            offsides=gen_map[t].offsides[0],
            ball_recoveries_attacking=def_map[t].ball_recoveries_attacking[0],
            interceptions=def_map[t].interceptions[0],
            tackles=def_map[t].tackles[0],
            ball_recoveries_midfield=def_map[t].ball_recoveries_midfield[0],
            ball_recoveries_defensive=def_map[t].ball_recoveries_defensive[0],
            clearances=def_map[t].clearances[0],
            fouls_conceded=dis_map[t].fouls_conceded[0],
            cards_yellow=dis_map[t].cards_yellow[0],
            cards_red=dis_map[t].cards_red[0],
        )

        away = MomentumUsedStats(
            goals=a.goals[1],
            shots_on_target=a.shots_on_target[1],
            shots_inside_box=a.shots_inside_box[1],
            shots_headed=a.shots_headed[1],
            shots_outside_box=a.shots_outside_box[1],
            shots_blocked=a.shots_blocked[1],
            key_passes=a.key_passes[1],
            through_balls=dist_map[t].through_balls[1],
            penalty_area_entries=dist_map[t].penalty_area_entries[1],
            open_play_crosses=dist_map[t].open_play_crosses[1],
            final_thirds_entries=dist_map[t].final_thirds_entries[1],
            dribbles_success=gen_map[t].dribbles_success[1],
            corners_won=gen_map[t].corners_won[1],
            fouls_won=gen_map[t].fouls_won[1],
            possession_lost_defensive=gen_map[t].possession_lost_defensive[1],
            possession_lost_midfield=gen_map[t].possession_lost_midfield[1],
            offsides=gen_map[t].offsides[1],
            ball_recoveries_attacking=def_map[t].ball_recoveries_attacking[1],
            interceptions=def_map[t].interceptions[1],
            tackles=def_map[t].tackles[1],
            ball_recoveries_midfield=def_map[t].ball_recoveries_midfield[1],
            ball_recoveries_defensive=def_map[t].ball_recoveries_defensive[1],
            clearances=def_map[t].clearances[1],
            fouls_conceded=dis_map[t].fouls_conceded[1],
            cards_yellow=dis_map[t].cards_yellow[1],
            cards_red=dis_map[t].cards_red[1],
        )

        home_stats.append(TeamMomentumStats(time_in_match=t, stats=home))
        away_stats.append(TeamMomentumStats(time_in_match=t, stats=away))

    # CHUẨN: sort theo giây đúng → không lẫn 45+ với 46
    home_stats.sort(key=lambda x: convert_to_seconds(x.time_in_match))
    away_stats.sort(key=lambda x: convert_to_seconds(x.time_in_match))

    return home_stats, away_stats


# ============================================================
# MOMENTUM CALCULATION (GỐC)
# ============================================================
async def diff_stats(prev: MomentumUsedStats, cur: MomentumUsedStats):
    return MomentumUsedStats(
        **{f: getattr(cur, f) - getattr(prev, f) for f in cur.dict()}
    )


async def threat_from_stats(stats: MomentumUsedStats):
    return (
        1 * stats.goals
        + 0.3 * stats.shots_on_target
        + 0.15 * stats.shots_inside_box
        + 0.1 * stats.shots_headed
        + 0.04 * stats.shots_outside_box
        + 0.02 * stats.shots_blocked
        + 0.12 * stats.key_passes
        + 0.1 * stats.through_balls
        + 0.08 * stats.penalty_area_entries
        + 0.03 * stats.open_play_crosses
        + 0.03 * stats.final_thirds_entries
        + 0.04 * stats.dribbles_success
        + 0.03 * stats.corners_won
        + 0.02 * stats.fouls_won
        - 0.2 * stats.possession_lost_defensive
        - 0.05 * stats.possession_lost_midfield
        - 0.03 * stats.offsides
        + 0.15 * stats.ball_recoveries_attacking
        + 0.1 * stats.interceptions
        + 0.03 * stats.tackles
        + 0.02 * stats.ball_recoveries_midfield
        + 0.02 * stats.ball_recoveries_defensive
        + 0.01 * stats.clearances
        - 0.04 * stats.fouls_conceded
        - 0.08 * stats.cards_yellow
        - 0.5 * stats.cards_red
    )


async def calculate_momentum(team_stats):
    lambda_value = 0.0046  # Decay 5 phút
    threat_scores = []

    prev_stats = MomentumUsedStats(**{k: 0 for k in team_stats[0].stats.dict()})
    action_list = []

    for entry in team_stats:
        t = entry.time_in_match
        diff = await diff_stats(prev_stats, entry.stats)
        action_list.append(TeamMomentumStats(time_in_match=t, stats=diff))

        # remove events older than 10 mins
        while len(action_list) > 1:
            delta = convert_to_seconds(t) - convert_to_seconds(
                action_list[0].time_in_match
            )
            if delta > 600:
                action_list.pop(0)
            else:
                break

        score = 100.0
        for a in action_list:
            base = await threat_from_stats(a.stats)
            dt = convert_to_seconds(t) - convert_to_seconds(a.time_in_match)
            score += base * math.exp(-lambda_value * dt)

        threat_scores.append(TeamThreatScore(time_in_match=t, threat_score=score))
        prev_stats = entry.stats

    return threat_scores


# ============================================================
# MAIN PIPELINE
# ============================================================
async def run_pipeline(db_name, out_file):
    home, away = await load_match_stats(db_name)

    home_m = await calculate_momentum(home)
    away_m = await calculate_momentum(away)

    output, first, second = [], [], []

    second_half_started = False

    for h, a in zip(home_m, away_m):
        t = h.time_in_match
        total = h.threat_score + a.threat_score
        mom = h.threat_score / total * 100 if total > 0 else 50

        entry = {
            "time_in_match": t,
            "home_team_threat": h.threat_score,
            "away_team_threat": a.threat_score,
            "momentum_index": mom,
        }

        if not second_half_started:
            if is_second_half(t):
                second_half_started = True
                second.append(entry)
            else:
                first.append(entry)
        else:
            second.append(entry)

        output.append(entry)

    with open(out_file, "w") as f:
        json.dump(output, f, indent=4)
    with open(out_file.replace(".json", "_first_half.json"), "w") as f:
        json.dump(first, f, indent=4)
    with open(out_file.replace(".json", "_second_half.json"), "w") as f:
        json.dump(second, f, indent=4)

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--output", default="momentum.json")
    args = parser.parse_args()

    asyncio.run(run_pipeline(args.db, args.output))
