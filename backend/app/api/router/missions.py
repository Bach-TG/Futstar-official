import asyncio
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from backend.missions import MissionOperations
from backend.users import UserOperations
from configs import get_logger
from hooks.error import MissionCheckingError, ResourceNotFound
from schemas.missions import MissionMetadata
from schemas.response import ApiResponse, UserClaimedSuccessResponse
from utils.enums import MissionType, SocialUrl

logger = get_logger(__name__)


router = APIRouter(
    prefix="/missions",
    tags=["missions"],
)


@router.post("/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(mission_name: str, description: str, reward_points: int, type: MissionType, number_of_steps: int = 1, expiration_date: datetime | None = None, is_active: bool = True):
    """**Create a new mission.**
    Inputs:
    - **mission_name**: Name of the mission.
    - **description**: Description of the mission.
    - **reward_points**: Reward points for completing the mission.
    - **type**: Type of the mission.
    - (Optional) **number_of_steps**: Number of steps required to complete the mission (default is 1).
    - (Optional) **expiration_date**: Expiration date of the mission.
    - (Optional) **is_active**: Indicates if the mission is currently active (default is True).
    Returns:
    - ApiResponse: Confirmation of mission creation.
        - `success`: Indicates if the operation was successful.
        - `status_code`: HTTP status code of the response.
        - `message`: Confirmation message.
        - `data`: Details of the created mission including mission ID, name, description, reward points, type, active status, and expiration date.
    """
    try:
        mission = await MissionOperations.add_a_new_mission(
            mission_name=mission_name,
            description=description,
            reward_points=reward_points,
            type=type,
            number_of_steps=number_of_steps,
            expiration_date=expiration_date,
            is_active=is_active,
        )
        return ApiResponse(
            success=True,
            status_code=status.HTTP_201_CREATED,
            message="Mission created successfully.",
            data=mission.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred. {str(e)}")


@router.post("/claim", response_model=UserClaimedSuccessResponse, status_code=status.HTTP_200_OK)
async def claim_user_mission_reward(user_id: str, mission_id: str):
    """**Claim reward for a completed mission.**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - **mission_id**: Unique identifier for the mission.
    Returns:
    - UserClaimedSuccessResponse: Confirmation of successful reward claim.
        - `message`: Confirmation message.
        - `user_id`: Unique identifier for the user.
        - `mission_id`: Unique identifier for the mission.
    """
    try:
        response = await MissionOperations.claim_user_mission_reward(user_id=user_id, mission_id=mission_id)
        return response
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except MissionCheckingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred. {str(e)}")


@router.get("/social_url", response_model=str, status_code=status.HTTP_200_OK)
async def get_url_for_social_following_mission(user_id: str, mission_id: str, social_platform: Literal["twitter", "telegram", "discord"]):
    """**Get social URL for social following missions.**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - **mission_id**: Unique identifier for the mission.
    - **social_platform**: The social media platform (twitter, telegram, discord).
    Returns:
    - str: Social URL associated with the specified social platform.
    """
    # Validate mission existence and type
    _ = asyncio.create_task(UserOperations.add_completed_step_to_user_mission(
        user_id=user_id,
        mission_id=mission_id,
        number_of_completed_steps=1
     ))
    if social_platform == "twitter":
        return SocialUrl.TWITTER_URL.value
    elif social_platform == "telegram":
        return SocialUrl.TELEGRAM_URL.value
    elif social_platform == "discord":
        return SocialUrl.DISCORD_URL.value