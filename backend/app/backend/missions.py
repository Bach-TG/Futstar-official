import asyncio
from datetime import datetime, timezone
from uuid import UUID

from backend.users import UserOperations
from clients import Clients
from configs import get_logger
from hooks.error import MissionCheckingError, ResourceNotFound
from schemas.missions import MissionMetadata
from schemas.mongo.collections import MissionMetadataDB, UserMetadataDB, UserMissionDB
from schemas.response import UserClaimedSuccessResponse
from schemas.users import UserMetadata, UserMissionProgress
from utils.enums import MissionType

logger = get_logger(__name__)
mongo_client = Clients.get_mongo_client()





class MissionOperations:
    

    @staticmethod
    async def claim_user_mission_reward(user_id: str, mission_id: str) -> UserClaimedSuccessResponse:
        user_mission = await UserMissionDB.find_one(
            UserMissionDB.user_id == user_id,
            UserMissionDB.mission_id == mission_id
        )
        if not user_mission:
            logger.error(f"Mission with ID {mission_id} for user {user_id} not found.")
            raise ResourceNotFound(f"Mission with ID {mission_id} for user {user_id} not found.")
        if not user_mission.is_completed:
            logger.error(f"Mission with ID {mission_id} for user {user_id} is not completed yet.")
            raise MissionCheckingError(f"Mission with ID {mission_id} for user {user_id} is not completed yet.")
        if user_mission.is_claimed:
            logger.error(f"Mission with ID {mission_id} for user {user_id} has already been claimed.")
            raise MissionCheckingError(f"Mission with ID {mission_id} for user {user_id} has already been claimed.")
        mission = await MissionMetadataDB.find_one(MissionMetadataDB.id == UUID(mission_id))
        user_mission.is_claimed = True
        await UserOperations.update_user_experience_points(
            user_id=user_id,
            points=mission.reward_points if mission else 0
        )
        await user_mission.save()
        logger.info(f"User {user_id} has claimed reward for mission {mission_id}.")
        return UserClaimedSuccessResponse(
            user_id=user_id,
            mission_id=mission_id,
            claimed_at=datetime.now(timezone.utc),
            reward_points=mission.reward_points if mission else 0,
        )

    @staticmethod
    async def add_a_new_mission(mission_name: str, description: str, reward_points: int, type: MissionType, number_of_steps: int = 1, expiration_date: datetime | None = None, is_active: bool = True) -> MissionMetadata:
        new_mission = MissionMetadataDB(
            mission_name=mission_name,
            description=description,
            reward_points=reward_points,
            type=type.value,
            number_of_steps=number_of_steps,
            is_active=is_active,
            expiration_date=expiration_date,
        )
        await new_mission.save()
        logger.info(f"Added new mission {mission_name} with ID {new_mission.id}.")
        _ = asyncio.create_task(UserOperations.create_user_mission_for_all_users(str(new_mission.id)))
        return MissionMetadata(
            mission_id=str(new_mission.id),
            mission_name=new_mission.mission_name,
            description=new_mission.description,
            reward_points=new_mission.reward_points,
            type=MissionType(new_mission.type),
            is_active=new_mission.is_active,
            expiration_date=new_mission.expiration_date,
            created_at=new_mission.created_at,
        )



