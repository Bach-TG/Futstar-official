import math
from enum import Enum
from queue import Queue

from pydantic import BaseModel

from clients import Clients
from configs import match_config
from mongo.schemas import (
    MatchAttackStats,
    MatchDefenceStats,
    MatchDisciplineStats,
    MatchDistributionStats,
    MatchGeneralStats,
)


class LambdaEnumForDuration(float, Enum):
    THIRTY_SECONDS = 0.0693
    TWO_MINUTES = 0.0347
    THREE_MINUTES = 0.0154
    FIVE_MINUTES = 0.0046


mongo_client = Clients.get_mongo_client()


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


class MomentumUsedStats(BaseModel):
    goals: int = 0
    shots_on_target: int = 0
    shots_inside_box: int = 0
    shots_headed: int = 0
    shots_outside_box: int = 0
    shots_blocked: int = 0
    key_passes: int = 0
    through_balls: int = 0
    penalty_area_entries: int = 0
    open_play_crosses: int = 0
    final_thirds_entries: int = 0
    dribbles_success: int = 0
    corners_won: int = 0
    fouls_won: int = 0
    possession_lost_defensive: int = 0
    possession_lost_midfield: int = 0
    offsides: int = 0
    ball_recoveries_attacking: int = 0
    interceptions: int = 0
    tackles: int = 0
    ball_recoveries_midfield: int = 0
    ball_recoveries_defensive: int = 0
    clearances: int = 0
    fouls_conceded: int = 0
    cards_yellow: int = 0
    cards_red: int = 0


class TeamMomentumStats(BaseModel):
    time_in_match: str
    stats: MomentumUsedStats


class TeamThreatScore(BaseModel):
    time_in_match: str
    threat_score: float


async def get_stats_from_db() -> tuple[
    list[TeamMomentumStats], list[TeamMomentumStats]
]:
    await mongo_client.initialize()
    home_team_full_time_stats: list[TeamMomentumStats] = []
    away_team_full_time_stats: list[TeamMomentumStats] = []

    all_attack_stats = await MatchAttackStats.find_all().to_list()
    all_defence_stats = await MatchDefenceStats.find_all().to_list()
    all_discipline_stats = await MatchDisciplineStats.find_all().to_list()
    all_distribution_stats = await MatchDistributionStats.find_all().to_list()
    all_general_stats = await MatchGeneralStats.find_all().to_list()

    defence_map = {s.time_in_match: s for s in all_defence_stats}
    discipline_map = {s.time_in_match: s for s in all_discipline_stats}
    distribution_map = {s.time_in_match: s for s in all_distribution_stats}
    general_map = {s.time_in_match: s for s in all_general_stats}

    for stat in all_attack_stats:
        time_in_match = stat.time_in_match

        home_team_stats = MomentumUsedStats(
            goals=stat.goals[0],
            shots_on_target=stat.shots_on_target[0],
            shots_inside_box=stat.shots_inside_box[0],
            shots_headed=stat.shots_headed[0],
            shots_outside_box=stat.shots_outside_box[0],
            shots_blocked=stat.shots_blocked[0],
            key_passes=stat.key_passes[0],
            through_balls=distribution_map[time_in_match].through_balls[0],
            penalty_area_entries=distribution_map[time_in_match].penalty_area_entries[
                0
            ],
            open_play_crosses=distribution_map[time_in_match].open_play_crosses[0],
            final_thirds_entries=distribution_map[time_in_match].final_thirds_entries[
                0
            ],
            dribbles_success=general_map[time_in_match].dribbles_success[0],
            corners_won=general_map[time_in_match].corners_won[0],
            possession_lost_defensive=general_map[
                time_in_match
            ].possession_lost_defensive[0],
            possession_lost_midfield=general_map[
                time_in_match
            ].possession_lost_midfield[0],
            offsides=general_map[time_in_match].offsides[0],
            ball_recoveries_attacking=defence_map[
                time_in_match
            ].ball_recoveries_attacking[0],
            interceptions=defence_map[time_in_match].interceptions[0],
            ball_recoveries_midfield=defence_map[
                time_in_match
            ].ball_recoveries_midfield[0],
            ball_recoveries_defensive=defence_map[
                time_in_match
            ].ball_recoveries_defensive[0],
            tackles=defence_map[time_in_match].tackles[0],
            clearances=defence_map[time_in_match].clearances[0],
            fouls_conceded=discipline_map[time_in_match].fouls_conceded[0],
            fouls_won=general_map[time_in_match].fouls_won[0],
            cards_yellow=discipline_map[time_in_match].cards_yellow[0],
            cards_red=discipline_map[time_in_match].cards_red[0],
        )

        away_team_stats = MomentumUsedStats(
            goals=stat.goals[1],
            shots_on_target=stat.shots_on_target[1],
            shots_inside_box=stat.shots_inside_box[1],
            shots_headed=stat.shots_headed[1],
            shots_outside_box=stat.shots_outside_box[1],
            shots_blocked=stat.shots_blocked[1],
            key_passes=stat.key_passes[1],
            through_balls=distribution_map[time_in_match].through_balls[1],
            penalty_area_entries=distribution_map[time_in_match].penalty_area_entries[
                1
            ],
            open_play_crosses=distribution_map[time_in_match].open_play_crosses[1],
            final_thirds_entries=distribution_map[time_in_match].final_thirds_entries[
                1
            ],
            dribbles_success=general_map[time_in_match].dribbles_success[1],
            corners_won=general_map[time_in_match].corners_won[1],
            possession_lost_defensive=general_map[
                time_in_match
            ].possession_lost_defensive[1],
            possession_lost_midfield=general_map[
                time_in_match
            ].possession_lost_midfield[1],
            offsides=general_map[time_in_match].offsides[1],
            ball_recoveries_attacking=defence_map[
                time_in_match
            ].ball_recoveries_attacking[1],
            interceptions=defence_map[time_in_match].interceptions[1],
            ball_recoveries_midfield=defence_map[
                time_in_match
            ].ball_recoveries_midfield[1],
            ball_recoveries_defensive=defence_map[
                time_in_match
            ].ball_recoveries_defensive[1],
            tackles=defence_map[time_in_match].tackles[1],
            clearances=defence_map[time_in_match].clearances[1],
            fouls_conceded=discipline_map[time_in_match].fouls_conceded[1],
            fouls_won=general_map[time_in_match].fouls_won[1],
            cards_yellow=discipline_map[time_in_match].cards_yellow[1],
            cards_red=discipline_map[time_in_match].cards_red[1],
        )
        home_team_full_time_stats.append(
            TeamMomentumStats(time_in_match=stat.time_in_match, stats=home_team_stats)
        )
        away_team_full_time_stats.append(
            TeamMomentumStats(time_in_match=stat.time_in_match, stats=away_team_stats)
        )
    if not home_team_full_time_stats[0].time_in_match.startswith("0"):
        home_team_full_time_stats.reverse()
        away_team_full_time_stats.reverse()
    print("Fetched stats from DB")
    return home_team_full_time_stats, away_team_full_time_stats


async def convert_to_seconds(time_in_match: str) -> int:
    if time_in_match.find("+") != -1:
        main_time, extra_time = time_in_match.split("+")
        extra_minutes, extra_seconds = extra_time.split(":")
        return int(main_time) * 60 + int(extra_minutes) * 60 + int(extra_seconds)
    else:
        minutes, seconds = time_in_match.split(":")
        return int(minutes) * 60 + int(seconds)


async def calculate_difference_time(
    previous_time: str, current_time: str, first_half_end_time: str | None = None
) -> int:
    previous_seconds = await convert_to_seconds(previous_time)
    current_seconds = await convert_to_seconds(current_time)
    if previous_time.find("+") != -1 and current_time.find("+") == -1:
        if first_half_end_time:
            first_half_end_seconds = await convert_to_seconds(first_half_end_time)
            return (
                (first_half_end_seconds - previous_seconds)
                + current_seconds
                - (await convert_to_seconds("45:00"))
            )
        else:
            return 1
    return current_seconds - previous_seconds


async def calculate_difference_stats(
    previous_stats: MomentumUsedStats, current_stats: MomentumUsedStats
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
        possession_lost_defensive=current_stats.possession_lost_defensive
        - previous_stats.possession_lost_defensive,
        possession_lost_midfield=current_stats.possession_lost_midfield
        - previous_stats.possession_lost_midfield,
        offsides=current_stats.offsides - previous_stats.offsides,
        ball_recoveries_attacking=current_stats.ball_recoveries_attacking
        - previous_stats.ball_recoveries_attacking,
        interceptions=current_stats.interceptions - previous_stats.interceptions,
        ball_recoveries_midfield=current_stats.ball_recoveries_midfield
        - previous_stats.ball_recoveries_midfield,
        ball_recoveries_defensive=current_stats.ball_recoveries_defensive
        - previous_stats.ball_recoveries_defensive,
        tackles=current_stats.tackles - previous_stats.tackles,
        clearances=current_stats.clearances - previous_stats.clearances,
        fouls_conceded=current_stats.fouls_conceded - previous_stats.fouls_conceded,
        fouls_won=current_stats.fouls_won - previous_stats.fouls_won,
        cards_yellow=current_stats.cards_yellow - previous_stats.cards_yellow,
        cards_red=current_stats.cards_red - previous_stats.cards_red,
    )


async def calculate_threat_score(
    action_list: list[TeamMomentumStats],
    lambda_value: LambdaEnumForDuration,
    current_time: str,
) -> float:
    threat_score = 100.0
    for action in action_list:
        stats = action.stats
        threat_contribution: float = 100.0 * (
            1.0 * stats.goals * 1
            + 1.0 * stats.shots_on_target * 0.3
            + 1.0 * stats.shots_inside_box * 0.15
            + 1.0 * stats.shots_headed * 0.1
            + 1.0 * stats.shots_outside_box * 0.04
            + 1.0 * stats.shots_blocked * 0.02
            + 1.0 * stats.key_passes * 0.12
            + 1.0 * stats.through_balls * 0.1
            + 1.0 * stats.penalty_area_entries * 0.08
            + 1.0 * stats.open_play_crosses * 0.03
            + 1.0 * stats.final_thirds_entries * 0.03
            + 1.0 * stats.dribbles_success * 0.04
            + 1.0 * stats.corners_won * 0.03
            + 1.0 * stats.fouls_won * 0.02
            + 1.0 * stats.possession_lost_defensive * (-0.2)
            + 1.0 * stats.possession_lost_midfield * (-0.05)
            + 1.0 * stats.offsides * (-0.03)
            + 1.0 * stats.ball_recoveries_attacking * 0.15
            + 1.0 * stats.interceptions * 0.1
            + 1.0 * stats.tackles * 0.03
            + 1.0 * stats.ball_recoveries_midfield * 0.02
            + 1.0 * stats.ball_recoveries_defensive * 0.02
            + 1.0 * stats.clearances * 0.01
            + 1.0 * stats.fouls_conceded * (-0.04)
            + 1.0 * stats.cards_yellow * (-0.08)
            + 1.0 * stats.cards_red * (-0.5)
        )
        time_diff = await calculate_difference_time(
            previous_time=action.time_in_match, current_time=current_time
        )
        decay_factor = math.exp(-lambda_value.value * time_diff)
        threat_score += threat_contribution * decay_factor
    return threat_score


async def calculate_momentum_stats(
    team_stats: list[TeamMomentumStats], lambda_value: LambdaEnumForDuration
) -> list[TeamThreatScore]:
    threat_scores: list[TeamThreatScore] = []
    previous_momentum_stats: MomentumUsedStats = MomentumUsedStats(
        goals=0,
        shots_on_target=0,
        shots_inside_box=0,
        shots_headed=0,
        shots_outside_box=0,
        shots_blocked=0,
        key_passes=0,
        through_balls=0,
        penalty_area_entries=0,
        open_play_crosses=0,
        final_thirds_entries=0,
        dribbles_success=0,
        corners_won=0,
        possession_lost_defensive=0,
        possession_lost_midfield=0,
        offsides=0,
        ball_recoveries_attacking=0,
        interceptions=0,
        tackles=0,
        ball_recoveries_midfield=0,
        ball_recoveries_defensive=0,
        clearances=0,
        fouls_conceded=0,
        fouls_won=0,
        cards_yellow=0,
        cards_red=0,
    )

    first_half_end_time = None
    actions_list: list[TeamMomentumStats] = []
    for s in team_stats:
        time_in_match = s.time_in_match
        stat = s.stats
        actions_list.append(
            TeamMomentumStats(
                time_in_match=time_in_match,
                stats=await calculate_difference_stats(
                    previous_stats=previous_momentum_stats, current_stats=stat
                ),
            )
        )
        if time_in_match.find("+") != -1:
            first_half_end_time = time_in_match
        while (
            len(actions_list) > 1
            and (
                await calculate_difference_time(
                    actions_list[0].time_in_match, time_in_match, first_half_end_time
                )
            )
            > 600
        ):
            actions_list.pop(0)
        threat_score = await calculate_threat_score(
            actions_list, lambda_value, time_in_match
        )
        threat_scores.append(
            TeamThreatScore(time_in_match=time_in_match, threat_score=threat_score)
        )
        print(f"Calculated threat score for time {time_in_match}: {threat_score}")
        previous_momentum_stats = stat
    return threat_scores


async def calculate_full_momentum():
    home_team_stats, away_team_stats = await get_stats_from_db()
    print("Starting momentum calculations")
    print("Calculating Home Team momentum")
    home_team_momentum = await calculate_momentum_stats(
        home_team_stats, LambdaEnumForDuration.FIVE_MINUTES
    )
    print("Home Team momentum calculation complete")
    print("Calculating Away Team momentum")
    away_team_momentum = await calculate_momentum_stats(
        away_team_stats, LambdaEnumForDuration.FIVE_MINUTES
    )
    print("Away Team momentum calculation complete")
    return home_team_momentum, away_team_momentum


if __name__ == "__main__":
    import asyncio
    import json

    home_team_momentum, away_team_momentum = asyncio.run(calculate_full_momentum())
    momentum_index = []
    momentum_index_first_half = []
    momentum_index_second_half = []
    check_second_half = False
    for hm, am in zip(home_team_momentum, away_team_momentum):
        momentum_score = (
            hm.threat_score / (hm.threat_score + am.threat_score) * 100
            if (hm.threat_score + am.threat_score) != 0
            else 50.0
        )
        print(
            f"At time {hm.time_in_match}, Home Team Threat Score: {hm.threat_score}, Away Team Threat Score: {am.threat_score}, Momentum Index: {momentum_score}"
        )

        if hm.time_in_match.startswith("45:") and momentum_index[-1][
            "time_in_match"
        ].startswith("45+"):
            check_second_half = True
        if not check_second_half:
            momentum_index_first_half.append(
                {
                    "time_in_match": hm.time_in_match,
                    "home_team_threat_score": hm.threat_score,
                    "away_team_threat_score": am.threat_score,
                    "momentum_index": momentum_score,
                }
            )
        else:
            momentum_index_second_half.append(
                {
                    "time_in_match": hm.time_in_match,
                    "home_team_threat_score": hm.threat_score,
                    "away_team_threat_score": am.threat_score,
                    "momentum_index": momentum_score,
                }
            )
        momentum_index.append(
            {"time_in_match": hm.time_in_match, "momentum_index": momentum_score}
        )

    with open("momentum_index.json", "w") as f:
        json.dump(momentum_index, f, indent=4)
    with open("momentum_index_first_half.json", "w") as f:
        json.dump(momentum_index_first_half, f, indent=4)
    with open("momentum_index_second_half.json", "w") as f:
        json.dump(momentum_index_second_half, f, indent=4)
