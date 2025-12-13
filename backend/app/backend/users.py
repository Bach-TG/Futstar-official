import asyncio
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from beanie.operators import And

from clients import Clients
from configs import get_logger
from hooks.error import ResourceNotFound
from schemas.missions import MissionMetadata
from schemas.momentum import MomentumPositions
from schemas.mongo.collections import (
    MatchMetadataDB,
    MissionMetadataDB,
    PositionHistoryDB,
    UserMetadataDB,
    UserMissionDB,
)
from schemas.users import UserMetadata, UserMissionProgress
from utils import LEVEL_UP_POINTS
from utils.enums import MissionType

logger = get_logger(__name__)

mongo_client = Clients.get_mongo_client()



class UserOperations:
    @staticmethod
    async def create_user_if_not_exists(user_wallet: str | None = None, telegram_handle: str | None = None, twitter_handle: str | None = None, discord_handle: str | None = None, email: str | None = None) -> UserMetadata:
        if user_wallet:
            user = await UserMetadataDB.find_one(UserMetadataDB.wallet_address == user_wallet)
        elif telegram_handle:
            user = await UserMetadataDB.find_one(UserMetadataDB.telegram_handle == telegram_handle)
        elif twitter_handle:
            user = await UserMetadataDB.find_one(UserMetadataDB.twitter_handle == twitter_handle)
        elif discord_handle:
            user = await UserMetadataDB.find_one(UserMetadataDB.discord_handle == discord_handle)
        elif email:
            user = await UserMetadataDB.find_one(UserMetadataDB.email == email)
        if not user:
            user = UserMetadataDB(
                wallet_address=user_wallet,
                balance=0.0,
                bonus_points=100,
                user_level=1,
                experience_points=0,
                telegram_handle=telegram_handle,
                twitter_handle=twitter_handle,
                discord_handle=discord_handle,
                email=email,
            )
            await user.insert()
            logger.info(f"Created new user with wallet: {user_wallet}")
            _ = asyncio.create_task(UserOperations.create_user_mission_for_a_user(str(user.id)))
        mission_name = "Welcome to Futstar"
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.mission_name == mission_name)
        if mission:
            _ = asyncio.create_task(UserOperations.add_completed_step_to_user_mission(
                user_id=str(user.id),
                mission_id=str(mission.id),
                number_of_completed_steps=1
            ))
        
        level_up_point: int = LEVEL_UP_POINTS.get(str(user.user_level), int(1e9))
        return UserMetadata(
            user_id=str(user.id),
            balance=user.balance,
            wallet_address=user.wallet_address,
            telegram_handle=user.telegram_handle,
            bonus_points=user.bonus_points,
            user_level=user.user_level,
            experience_points=user.experience_points,
            twitter_handle=user.twitter_handle,
            discord_handle=user.discord_handle,
            email=user.email,
            level_up_required_experience=level_up_point - user.experience_points,
        )


    
    @staticmethod
    async def get_user_metadata(user_id: str) -> UserMetadata:
        user = await UserMetadataDB.find_one(UserMetadataDB.id == UUID(user_id))
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            raise ResourceNotFound(f"User with ID {user_id} not found.")
        level_up_point: int = LEVEL_UP_POINTS.get(str(user.user_level), int(1e9))
        return UserMetadata(
            user_id=str(user.id),
            balance=user.balance,
            wallet_address=user.wallet_address,
            telegram_handle=user.telegram_handle,
            bonus_points=user.bonus_points,
            user_level=user.user_level,
            experience_points=user.experience_points,
            twitter_handle=user.twitter_handle,
            discord_handle=user.discord_handle,
            email=user.email,
            level_up_required_experience=level_up_point - user.experience_points,
        )

    @staticmethod
    async def get_positions_history(user_id: str, match_id: str | None = None) -> dict[datetime, MomentumPositions]:
        if match_id:
            positions_cursor = PositionHistoryDB.find(
                And(PositionHistoryDB.user_id == user_id, PositionHistoryDB.match_id == match_id)
            )
        else: 
            positions_cursor = PositionHistoryDB.find(
                PositionHistoryDB.user_id == user_id
            )
        positions: dict[datetime, MomentumPositions] = {}
        async for position in positions_cursor:
            match = await MatchMetadataDB.find_one(MatchMetadataDB.id == UUID(position.match_id))
            positions[position.timestamp] = MomentumPositions(
                position_id=str(position.id),
                type=position.type,
                duration=position.duration,
                entry_value=position.entry_value,
                closed_value=position.closed_value,
                pnl_percentage=position.pnl_percentage,
                amount=position.amount,
                timestamp=position.timestamp,
                user_id=position.user_id,
                match_id=position.match_id,
                time_in_match_entry=position.time_in_match_entry,
                time_in_match_closed=position.time_in_match_closed,
                status=position.status,
                bonus_points_rewarded=position.bonus_points_rewarded,
                home_team=match.home_team if match else None,
                away_team=match.away_team if match else None,
                competition=match.competition if match else None,
            )
        return positions

    @staticmethod
    async def update_user_bonus_points(user_id: str, points: float):
        user = await UserMetadataDB.find_one(UserMetadataDB.id == UUID(user_id))
        if not user:
            logger.error(f"User with ID {user_id} not found for bonus points update.")
            raise ResourceNotFound(f"User with ID {user_id} not found.")
        if user.bonus_points is None:
            user.bonus_points = 0
        user.bonus_points += points
        user.timestamp = datetime.now(timezone.utc)
        await user.save()
        logger.info(f"Updated bonus points for user {user_id} by {points}. New total: {user.bonus_points}")


    @staticmethod
    async def update_user_experience_points(user_id: str, points: int):
        user = await UserMetadataDB.find_one(UserMetadataDB.id == UUID(user_id))
        if not user:
            logger.error(f"User with ID {user_id} not found for experience points update.")
            raise ResourceNotFound(f"User with ID {user_id} not found.")
        if user.experience_points is None:
            user.experience_points = 0
            user.user_level = 1
        user.experience_points += points
        while user.experience_points >= LEVEL_UP_POINTS.get(str(user.user_level), int(1e9)):
            user.experience_points -= LEVEL_UP_POINTS.get(str(user.user_level), int(1e9))
            user.user_level += 1
            logger.info(f"User {user_id} leveled up to level {user.user_level}!")
        user.timestamp = datetime.now(timezone.utc)
        await user.save()
        logger.info(f"Updated experience points for user {user_id} by {points}. New total: {user.experience_points}")



    

    @staticmethod
    async def get_user_missions(user_id: str, is_claimed: bool | None = None) -> dict[str, UserMissionProgress]:
        if is_claimed is None:
            user_missions_cursor = UserMissionDB.find(UserMissionDB.user_id == user_id)
        else:
            user_missions_cursor = UserMissionDB.find(
                And(
                    UserMissionDB.user_id == user_id,
                    UserMissionDB.is_claimed == is_claimed
                )
            )
        user_missions: dict[str, UserMissionProgress] = {}
        async for user_mission in user_missions_cursor:
            mission = await MissionMetadataDB.find_one(MissionMetadataDB.id == UUID(user_mission.mission_id))
            if mission and mission.is_active:
                user_missions[user_mission.mission_id] = UserMissionProgress(
                    user_id=user_mission.user_id,
                    progress_percentage=user_mission.progress_percentage,
                    is_completed=user_mission.is_completed,
                    completion_date=user_mission.completion_date,
                    last_updated=user_mission.last_updated,
                    is_claimed=user_mission.is_claimed,
                    number_of_steps_completed=user_mission.number_of_steps_completed,
                    mission=MissionMetadata(
                        mission_id=str(mission.id),
                        mission_name=mission.mission_name,
                        description=mission.description,
                        reward_points=mission.reward_points,
                        type=MissionType(mission.type),
                        is_active=mission.is_active,
                        expiration_date=mission.expiration_date,
                        number_of_steps=mission.number_of_steps,
                        created_at=mission.created_at,
                    )
                )

        return user_missions

    @staticmethod
    async def create_user_mission_for_a_user(user_id: str):
        missions_cursor = MissionMetadataDB.find(MissionMetadataDB.is_active == True)
        async for mission in missions_cursor:
            existing_user_mission = await UserMissionDB.find_one(
                And(
                    UserMissionDB.user_id == user_id,
                    UserMissionDB.mission_id == str(mission.id)
                )
            )
            if not existing_user_mission:
                new_user_mission = UserMissionDB(
                    user_id=user_id,
                    mission_id=str(mission.id),
                    progress_percentage=0.0,
                    is_completed=False,
                    is_claimed=False,
                    number_of_steps_completed=0,
                    last_updated=datetime.now(timezone.utc),
                )
                await new_user_mission.insert()
                logger.info(f"Created mission {mission.id} for user {user_id}.")


    @staticmethod
    async def create_user_mission_for_all_users(mission_id: str):
        users_cursor = UserMetadataDB.find()
        async for user in users_cursor:
            existing_user_mission = await UserMissionDB.find_one(
                And(
                    UserMissionDB.user_id == str(user.id),
                    UserMissionDB.mission_id == mission_id
                )
            )
            if not existing_user_mission:
                new_user_mission = UserMissionDB(
                    user_id=str(user.id),
                    mission_id=mission_id,
                    progress_percentage=0.0,
                    is_completed=False,
                    is_claimed=False,
                    number_of_steps_completed=0,
                    last_updated=datetime.now(timezone.utc),
                )
                await new_user_mission.insert()
                logger.info(f"Created mission {mission_id} for user {user.id}.")

    @staticmethod
    async def add_completed_step_to_user_mission(user_id: str, mission_id: str, number_of_completed_steps: int = 1):
        user_mission = await UserMissionDB.find_one(
            UserMissionDB.user_id == user_id,
            UserMissionDB.mission_id == mission_id
        )
        if not user_mission:
            logger.error(f"Mission with ID {mission_id} for user {user_id} not found.")
            raise ResourceNotFound(f"Mission with ID {mission_id} for user {user_id} not found.")
        if user_mission.is_completed:
            logger.info(f"Mission with ID {mission_id} for user {user_id} is already completed.")
            return
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.id == UUID(mission_id))
        if not mission:
            logger.error(f"Mission metadata with ID {mission_id} not found.")
            raise ResourceNotFound(f"Mission metadata with ID {mission_id} not found.")
        user_mission.number_of_steps_completed += number_of_completed_steps
        user_mission.progress_percentage = (user_mission.number_of_steps_completed / mission.number_of_steps) * 100.0
        if user_mission.number_of_steps_completed >= mission.number_of_steps:
            user_mission.is_completed = True
            user_mission.completion_date = datetime.now(timezone.utc)
        user_mission.last_updated = datetime.now(timezone.utc)
        await user_mission.save()
        logger.info(f"Added completed step to mission {mission_id} for user {user_id}. Now at {user_mission.number_of_steps_completed} steps completed.")


    


class UserMissionCheckingOperations:
    @staticmethod
    async def check_mission_first_kick(user_id: str, mission_name: str = "First Kick"):
        """ 
        - Name: First Kick.
        - Description: Make your first live momentum trade.
        """
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.mission_name == mission_name)
        if not mission:
            logger.error(f"Mission with name {mission_name} not found.")
            raise ResourceNotFound(f"Mission with name {mission_name} not found.")
        user_mission = await UserMissionDB.find_one(
            UserMissionDB.user_id == user_id,
            UserMissionDB.mission_id == str(mission.id)
        )
        if not user_mission:
            logger.error(f"Mission {mission_name} for user {user_id} not found.")
            raise ResourceNotFound(f"Mission {mission_name} for user {user_id} not found.")
        if not user_mission.is_completed:
            user_mission.is_completed = True
            user_mission.progress_percentage = 100.0
            user_mission.number_of_steps_completed = 1
            user_mission.completion_date = datetime.now(timezone.utc)
            user_mission.last_updated = datetime.now(timezone.utc)
            await user_mission.save()
            logger.info(f"User {user_id} completed mission {mission_name}")

    @staticmethod
    async def check_mission_hot_streak_200(user_id: str, match_id: str, mission_name: str = "Hot Streak"):
        """ 
        - Name: Hot Streak.
        - Description: Hit 200 XP in a single match.
        """
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.mission_name == mission_name)
        if not mission:
            logger.error(f"Mission with name {mission_name} not found.")
            raise ResourceNotFound(f"Mission with name {mission_name} not found.")
        user_mission = await UserMissionDB.find_one(
            UserMissionDB.user_id == user_id,
            UserMissionDB.mission_id == str(mission.id)
        )
        if not user_mission:
            logger.error(f"Mission {mission_name} for user {user_id} not found.")
            raise ResourceNotFound(f"Mission {mission_name} for user {user_id} not found.")
        if not user_mission.is_completed:
            user_match_positions = await UserOperations.get_positions_history(user_id=user_id, match_id=match_id)
            total_bonus_points = 0
            for position in user_match_positions.values():
                total_bonus_points += round(position.bonus_points_rewarded) if position.bonus_points_rewarded else 0
            if total_bonus_points >= 200:
                user_mission.is_completed = True
                user_mission.progress_percentage = 100.0
                user_mission.number_of_steps_completed = 1
                user_mission.completion_date = datetime.now(timezone.utc)
                user_mission.last_updated = datetime.now(timezone.utc)
                await user_mission.save()
                logger.info(f"User {user_id} completed mission {mission_name}.")

    
        
    @staticmethod
    async def check_mission_matchday_grinder(user_id: str, mission_name: str = "Matchday Grinder"):
        """ 
        - Name: Matchday Grinder.
        - Description: Place trades in 3 different live matches.
        """
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.mission_name == mission_name)
        if not mission:
            logger.error(f"Mission with name {mission_name} not found.")
            raise ResourceNotFound(f"Mission with name {mission_name} not found.")
        user_mission = await UserMissionDB.find_one(
            UserMissionDB.user_id == user_id,
            UserMissionDB.mission_id == str(mission.id)
        )
        if not user_mission:
            logger.error(f"Mission {mission_name} for user {user_id} not found.")
            raise ResourceNotFound(f"Mission {mission_name} for user {user_id} not found.")
        if not user_mission.is_completed:
            user_positions = await UserOperations.get_positions_history(user_id=user_id)
            match_ids = set()
            for position in user_positions.values():
                match_ids.add(position.match_id)
            if len(match_ids) >= 3:
                user_mission.is_completed = True
                user_mission.progress_percentage = 100.0
                user_mission.number_of_steps_completed = 1
                user_mission.completion_date = datetime.now(timezone.utc)
                user_mission.last_updated = datetime.now(timezone.utc)
                await user_mission.save()
                logger.info(f"User {user_id} completed mission {mission_name}.")
            else:
                user_mission.progress_percentage = (len(match_ids) / 3) * 100.0
                user_mission.last_updated = datetime.now(timezone.utc)
                await user_mission.save()
                logger.info(f"User {user_id} progress updated for mission {mission_name} : {len(match_ids)}/3 matches.")

    @staticmethod
    async def check_mission_podium_finish(match_id: str, mission_name: str = "Podium Finish"):
        """ 
        - Name: Podium Finish.
        - Description: Finish Top 3 in any match leaderboard.
        """
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.mission_name == mission_name)
        if not mission:
            logger.error(f"Mission with name {mission_name} not found.")
            raise ResourceNotFound(f"Mission with name {mission_name} not found.")
        match = await MatchMetadataDB.find_one(MatchMetadataDB.id == UUID(match_id))
        if not match:
            logger.error(f"Match with ID {match_id} not found for podium finish mission check.")
            raise ResourceNotFound(f"Match with ID {match_id} not found.")
        positions_cursor = PositionHistoryDB.find(
            PositionHistoryDB.match_id == match_id
        )
        user_pnls: dict[str, float] = {}
        async for position in positions_cursor:
            if position.user_id not in user_pnls:
                user_pnls[position.user_id] = 0.0
            user_pnls[position.user_id] += position.pnl_percentage
        sorted_users = sorted(user_pnls.items(), key=lambda item: item[1], reverse=True)[:3]
        for rank, (user_id, total_pnl) in enumerate(sorted_users, start=1):
            if rank > 3:
                break
            user_mission = await UserMissionDB.find_one(
                And(
                    UserMissionDB.user_id == user_id,
                    UserMissionDB.mission_id == str(mission.id)
                )
            )
            if not user_mission:
                logger.error(f"Mission with name {mission_name} for user {user_id} not found.")
                continue
            if not user_mission.is_completed:
                user_mission.is_completed = True
                user_mission.progress_percentage = 100.0
                user_mission.number_of_steps_completed = 1
                user_mission.completion_date = datetime.now(timezone.utc)
                user_mission.last_updated = datetime.now(timezone.utc)
                await user_mission.save()
                logger.info(f"User {user_id} completed mission {mission_name} with rank {rank}.")