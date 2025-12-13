from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, status

from backend.momentum import MomentumOperations
from backend.users import UserOperations
from configs import get_logger
from hooks.error import MissionCheckingError, ResourceNotFound
from schemas.momentum import MomentumPositions
from schemas.response import ApiResponse, UserClaimedSuccessResponse
from schemas.users import UserMetadata, UserMissionProgress

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/create", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_wallet: str | None = None, telegram_handle: str | None = None, twitter_handle: str | None = None, discord_handle: str | None = None, email: str | None = None):
    """**Create a new user with an initial balance.**
    Inputs:
    - (Optional) **user_wallet**: Wallet address of the user.
    - ( Optional ) **telegram_handle**: Telegram handle of the user.
    - ( Optional ) **twitter_handle**: Twitter handle of the user.
    - ( Optional ) **discord_handle**: Discord handle of the user.
    - ( Optional ) **email**: Email address of the user.
    Returns:
    - ApiResponse: Confirmation of user creation.
        - `success`: Indicates if the operation was successful.
        - `status_code`: HTTP status code of the response.
        - `message`: Confirmation message.
        - `data`: Details of the created user including user ID and initial balance.
            - `user_id`: Unique identifier for the user.
            - `balance`: Initial balance of the user.
            - `wallet_address`: Wallet address of the user.
            - `telegram_handle`: Telegram handle of the user (if provided).
            - `twitter_handle`: Twitter handle of the user (if provided).
            - `discord_handle`: Discord handle of the user (if provided).
            - `email`: Email address of the user (if provided).
            - `bonus_points`: Bonus points awarded to the user (default is 0).
            - `user_level`: User's level in the application (default is 1).
            - `experience_points`: User's experience points in the application (default is 0).
            - `level_up_required_experience`: Experience points required for level up (if applicable).
    """
    if not user_wallet and not telegram_handle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_wallet or telegram_handle must be provided."
        )
    user = await UserOperations.create_user_if_not_exists(user_wallet=user_wallet, telegram_handle=telegram_handle, twitter_handle=twitter_handle, discord_handle=discord_handle, email=email)
    return ApiResponse(
        success=True,
        status_code=status.HTTP_201_CREATED,    
        message="User created successfully.",
        data=user.model_dump(),
    )


@router.get("/metadata", response_model=UserMetadata, status_code=status.HTTP_200_OK)
async def get_user_metadata(user_id: str):
    """**Fetch user metadata by user ID.**
    Inputs:
    - **user_id**: Unique identifier for the user.
    Returns:
    - **UserMetadata**: Metadata information about the user.
        - `user_id`: Unique identifier for the user.
        - `balance`: Current balance of the user.
        - `wallet_address`: Wallet address of the user.
        - `telegram_handle`: Telegram handle of the user (if available).
        - `bonus_points`: Bonus points awarded to the user.
        - `user_level`: User's level in the application.
        - `experience_points`: User's experience points in the application.
        - `twitter_handle`: Twitter handle of the user (if available).
        - `discord_handle`: Discord handle of the user (if available).
        - `email`: Email address of the user (if available).
        - `level_up_required_experience`: Experience points required for level up (if applicable).
    """
    try:
        user = await UserOperations.get_user_metadata(user_id)
        return user
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

@router.get("/closed_positions_history", response_model=dict[datetime, MomentumPositions], status_code=status.HTTP_200_OK)
async def get_closed_positions_history(user_id: str, match_id: str | None = None):
    """**Fetch user closed momentum positions (status is Closed) by user ID (Long / Short).**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - ( Optional ) **match_id**: Unique identifier for the match. If provided, filters positions for that match only, otherwise fetches all positions for the user.
    Returns:
    - Keyed by timestamp:
        - Each MomentumPositions contains:
            - `position_id`: Unique identifier for the position.
            - `type`: Type of position ('Long' or 'Short').
            - `duration`: Duration of the position. 
            - `entry_value`: Entry value of the position.
            - `closed_value`: Closed value of the position (if closed).
            - `pnl_percentage`: Profit and loss percentage of the position.
            - `amount`: Amount for the position.
            - `timestamp`: Timestamp when the position was created.
            - `user_id`: Unique identifier for the user.
            - `match_id`: Unique identifier for the match.
            - `time_in_match_entry`: Time in match when the position was entered.
            - `time_in_match_closed`: Time in match when the position was closed (if closed).
            - `status`: Status of the position ('Open' or 'Closed').
            - `bonus_points_rewarded`: Bonus points rewarded for this position.
            - `home_team`: Home team name.
            - `away_team`: Away team name.
            - `competition`: Competition name.
                
    """
    return await UserOperations.get_positions_history(user_id, match_id)


@router.get("/missions", response_model=dict[str, UserMissionProgress], status_code=status.HTTP_200_OK)
async def get_user_missions(user_id: str, is_claimed: bool | None = None):
    """**Fetch user missions by user ID.**
    Inputs:
    - **user_id**: Unique identifier for the user.
    - (Optional) **is_claimed**: Filter missions based on whether they have been claimed or not.
    Returns:
    - **dict[str, UserMissionProgress]**: A dictionary mapping mission IDs to the user's progress on each mission.
        - `user_id`: Unique identifier for the user.
        - `progress_percentage`: Progress percentage of the mission.
        - `is_completed`: Indicates if the mission is completed by the user.
        - `completion_date`: Date when the mission was completed (if applicable).
        - `last_updated`: Timestamp of the last update to the mission progress.
        - `is_claimed`: Indicates if the mission reward has been claimed by the user.
        - `number_of_steps_completed`: Number of steps completed by the user for this mission.
        - `mission`: Details of the mission including mission ID, name, description, and reward points.
            - `mission_id`: Unique identifier for the mission.
            - `mission_name`: Name of the mission.
            - `description`: Description of the mission.
            - `reward_points`: Reward points for completing the mission.
            - `is_active`: Indicates if the mission is currently active.
            - `expiration_date`: Expiration date of the mission (if applicable).
            - `number_of_steps`: Number of steps required to complete the mission.
    """
    try:
        user_missions = await UserOperations.get_user_missions(user_id, is_claimed)
        return user_missions
    except ResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred.")

