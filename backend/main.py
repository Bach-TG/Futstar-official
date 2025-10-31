"""
Futstar Momentum Trading Backend
Real-time football match momentum calculation and trading API
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import random
import numpy as np
from enum import Enum
import aiohttp
import pandas as pd

app = FastAPI(
    title="Futstar Momentum Trading API",
    description="Real-time football momentum trading on Solana",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Data Models ====================

class PositionType(str, Enum):
    LONG = "long"
    SHORT = "short"

class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"

class Team(BaseModel):
    id: str
    name: str
    logo_url: Optional[str]

class MatchData(BaseModel):
    match_id: str
    home_team: Team
    away_team: Team
    start_time: datetime
    status: MatchStatus
    current_minute: Optional[int] = 0
    score_home: int = 0
    score_away: int = 0
    
class MomentumData(BaseModel):
    timestamp: datetime
    momentum_index: int  # 0-100
    possession: float
    shots_home: int
    shots_away: int
    xg_home: float
    xg_away: float
    field_tilt: float  # -100 to 100
    danger_home: float
    danger_away: float

class TradingPosition(BaseModel):
    position_id: str
    user_wallet: str
    match_id: str
    position_type: PositionType
    amount: float
    entry_index: int
    entry_time: datetime
    window_duration: int  # seconds
    is_settled: bool = False
    pnl: Optional[float] = None

class OpenPositionRequest(BaseModel):
    match_id: str
    position_type: PositionType
    amount: float
    wallet_address: str
    window_duration: int = 300  # 5 minutes default

# ==================== Momentum Calculator ====================

class MomentumCalculator:
    """
    Calculates match momentum index based on multiple factors
    """
    
    @staticmethod
    def calculate_momentum(
        possession: float,
        shots_home: int,
        shots_away: int,
        xg_home: float,
        xg_away: float,
        field_tilt: float,
        recent_events: List[Dict] = []
    ) -> int:
        """
        Calculate momentum index (0-100) based on match statistics
        Higher values favor home team, lower values favor away team
        50 is neutral
        """
        
        # Possession weight (20%)
        possession_score = possession * 0.2
        
        # Shots weight (20%)
        total_shots = shots_home + shots_away
        if total_shots > 0:
            shots_score = (shots_home / total_shots) * 20
        else:
            shots_score = 10
        
        # xG weight (30%)
        total_xg = xg_home + xg_away
        if total_xg > 0:
            xg_score = (xg_home / total_xg) * 30
        else:
            xg_score = 15
        
        # Field tilt weight (20%)
        # Convert from -100 to 100 scale to 0-20
        field_tilt_score = ((field_tilt + 100) / 200) * 20
        
        # Recent events weight (10%)
        event_score = 5  # Default neutral
        if recent_events:
            # Analyze last 5 minutes of events
            recent_danger = sum(1 for e in recent_events[-10:] 
                              if e.get('team') == 'home' and 
                              e.get('type') in ['shot', 'corner', 'dangerous_attack'])
            recent_danger -= sum(1 for e in recent_events[-10:] 
                               if e.get('team') == 'away' and 
                               e.get('type') in ['shot', 'corner', 'dangerous_attack'])
            event_score = max(0, min(10, 5 + recent_danger))
        
        # Calculate final momentum
        momentum = (possession_score + shots_score + xg_score + 
                   field_tilt_score + event_score)
        
        # Add some volatility for realism
        volatility = random.gauss(0, 2)
        momentum += volatility
        
        # Ensure within bounds
        return max(0, min(100, int(momentum)))

# ==================== Mock Data Generator ====================

class MockDataGenerator:
    """
    Generates realistic mock match data for demo purposes
    """
    
    @staticmethod
    def generate_live_matches() -> List[MatchData]:
        """Generate mock live matches"""
        matches = [
            MatchData(
                match_id="match_001",
                home_team=Team(id="arsenal", name="Arsenal", logo_url="/logos/arsenal.png"),
                away_team=Team(id="tottenham", name="Tottenham", logo_url="/logos/tottenham.png"),
                start_time=datetime.now() - timedelta(minutes=35),
                status=MatchStatus.LIVE,
                current_minute=35,
                score_home=2,
                score_away=1
            ),
            MatchData(
                match_id="match_002",
                home_team=Team(id="liverpool", name="Liverpool", logo_url="/logos/liverpool.png"),
                away_team=Team(id="mancity", name="Man City", logo_url="/logos/mancity.png"),
                start_time=datetime.now() - timedelta(minutes=67),
                status=MatchStatus.LIVE,
                current_minute=67,
                score_home=1,
                score_away=2
            ),
            MatchData(
                match_id="match_003",
                home_team=Team(id="barcelona", name="Barcelona", logo_url="/logos/barcelona.png"),
                away_team=Team(id="realmadrid", name="Real Madrid", logo_url="/logos/realmadrid.png"),
                start_time=datetime.now() - timedelta(minutes=22),
                status=MatchStatus.LIVE,
                current_minute=22,
                score_home=0,
                score_away=0
            )
        ]
        return matches
    
    @staticmethod
    def generate_momentum_data(match_id: str, minute: int) -> MomentumData:
        """Generate realistic momentum data for a specific match minute"""
        
        # Simulate match flow patterns
        base_possession = 50 + random.gauss(0, 10)
        
        # Add match-specific patterns
        if "arsenal" in match_id:
            base_possession += 5  # Arsenal typically dominates possession
        elif "mancity" in match_id:
            base_possession -= 8  # City away might have less possession
        
        # Generate correlated stats
        possession = max(30, min(70, base_possession))
        
        # Shots correlate with possession but with randomness
        shots_home = max(0, int(random.gauss(minute * 0.15 * (possession/50), 2)))
        shots_away = max(0, int(random.gauss(minute * 0.15 * ((100-possession)/50), 2)))
        
        # xG calculation
        xg_home = shots_home * random.uniform(0.08, 0.18)
        xg_away = shots_away * random.uniform(0.08, 0.18)
        
        # Field tilt
        field_tilt = (possession - 50) * 2 + random.gauss(0, 10)
        
        # Danger metrics
        danger_home = possession / 100 * random.uniform(0.3, 1.0)
        danger_away = (100 - possession) / 100 * random.uniform(0.3, 1.0)
        
        # Calculate momentum index
        momentum_index = MomentumCalculator.calculate_momentum(
            possession=possession,
            shots_home=shots_home,
            shots_away=shots_away,
            xg_home=xg_home,
            xg_away=xg_away,
            field_tilt=field_tilt
        )
        
        return MomentumData(
            timestamp=datetime.now(),
            momentum_index=momentum_index,
            possession=possession,
            shots_home=shots_home,
            shots_away=shots_away,
            xg_home=round(xg_home, 2),
            xg_away=round(xg_away, 2),
            field_tilt=round(field_tilt, 1),
            danger_home=round(danger_home, 2),
            danger_away=round(danger_away, 2)
        )

# ==================== In-Memory Storage ====================

class DataStore:
    """Simple in-memory storage for demo purposes"""
    
    def __init__(self):
        self.matches: Dict[str, MatchData] = {}
        self.momentum_history: Dict[str, List[MomentumData]] = {}
        self.positions: Dict[str, TradingPosition] = {}
        self.user_positions: Dict[str, List[str]] = {}
        
    def initialize_mock_data(self):
        """Initialize with mock data"""
        matches = MockDataGenerator.generate_live_matches()
        for match in matches:
            self.matches[match.match_id] = match
            self.momentum_history[match.match_id] = []

# Initialize data store
data_store = DataStore()
data_store.initialize_mock_data()

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "active",
        "name": "Futstar Momentum Trading API",
        "version": "1.0.0",
        "blockchain": "Solana"
    }

@app.get("/api/matches", response_model=List[MatchData])
async def get_live_matches():
    """Get all live matches"""
    return list(data_store.matches.values())

@app.get("/api/matches/{match_id}", response_model=MatchData)
async def get_match(match_id: str):
    """Get specific match details"""
    if match_id not in data_store.matches:
        raise HTTPException(status_code=404, detail="Match not found")
    return data_store.matches[match_id]

@app.get("/api/matches/{match_id}/momentum", response_model=MomentumData)
async def get_current_momentum(match_id: str):
    """Get current momentum for a match"""
    if match_id not in data_store.matches:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match = data_store.matches[match_id]
    momentum = MockDataGenerator.generate_momentum_data(match_id, match.current_minute)
    
    # Store in history
    data_store.momentum_history[match_id].append(momentum)
    
    return momentum

@app.get("/api/matches/{match_id}/momentum/history")
async def get_momentum_history(match_id: str, limit: int = 100):
    """Get momentum history for a match"""
    if match_id not in data_store.matches:
        raise HTTPException(status_code=404, detail="Match not found")
    
    history = data_store.momentum_history.get(match_id, [])
    return history[-limit:] if history else []

@app.post("/api/positions/open", response_model=TradingPosition)
async def open_position(request: OpenPositionRequest):
    """Open a new trading position"""
    
    if request.match_id not in data_store.matches:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get current momentum
    match = data_store.matches[request.match_id]
    current_momentum = MockDataGenerator.generate_momentum_data(
        request.match_id, 
        match.current_minute
    )
    
    # Create position
    position = TradingPosition(
        position_id=f"pos_{datetime.now().timestamp()}",
        user_wallet=request.wallet_address,
        match_id=request.match_id,
        position_type=request.position_type,
        amount=request.amount,
        entry_index=current_momentum.momentum_index,
        entry_time=datetime.now(),
        window_duration=request.window_duration
    )
    
    # Store position
    data_store.positions[position.position_id] = position
    
    # Track user positions
    if request.wallet_address not in data_store.user_positions:
        data_store.user_positions[request.wallet_address] = []
    data_store.user_positions[request.wallet_address].append(position.position_id)
    
    return position

@app.get("/api/positions/{position_id}", response_model=TradingPosition)
async def get_position(position_id: str):
    """Get position details"""
    if position_id not in data_store.positions:
        raise HTTPException(status_code=404, detail="Position not found")
    return data_store.positions[position_id]

@app.post("/api/positions/{position_id}/settle")
async def settle_position(position_id: str):
    """Settle a position"""
    if position_id not in data_store.positions:
        raise HTTPException(status_code=404, detail="Position not found")
    
    position = data_store.positions[position_id]
    if position.is_settled:
        raise HTTPException(status_code=400, detail="Position already settled")
    
    # Check if window has ended
    window_end = position.entry_time + timedelta(seconds=position.window_duration)
    if datetime.now() < window_end:
        raise HTTPException(status_code=400, detail="Trading window not ended")
    
    # Get current momentum
    match = data_store.matches[position.match_id]
    current_momentum = MockDataGenerator.generate_momentum_data(
        position.match_id,
        match.current_minute
    )
    
    # Calculate PnL
    momentum_change = current_momentum.momentum_index - position.entry_index
    
    if position.position_type == PositionType.LONG:
        # Long wins if momentum increased
        if momentum_change > 0:
            profit_multiplier = abs(momentum_change) / 100
            pnl = position.amount * profit_multiplier
            # Apply 2% fee
            pnl = pnl * 0.98
        else:
            pnl = -position.amount
    else:
        # Short wins if momentum decreased
        if momentum_change < 0:
            profit_multiplier = abs(momentum_change) / 100
            pnl = position.amount * profit_multiplier
            # Apply 2% fee
            pnl = pnl * 0.98
        else:
            pnl = -position.amount
    
    position.is_settled = True
    position.pnl = round(pnl, 4)
    
    return {
        "position_id": position_id,
        "pnl": position.pnl,
        "entry_index": position.entry_index,
        "exit_index": current_momentum.momentum_index,
        "momentum_change": momentum_change
    }

@app.get("/api/users/{wallet_address}/positions")
async def get_user_positions(wallet_address: str):
    """Get all positions for a user"""
    position_ids = data_store.user_positions.get(wallet_address, [])
    positions = [data_store.positions[pid] for pid in position_ids 
                if pid in data_store.positions]
    return positions

# ==================== WebSocket for Real-time Updates ====================

@app.websocket("/ws/momentum/{match_id}")
async def momentum_websocket(websocket: WebSocket, match_id: str):
    """WebSocket endpoint for real-time momentum updates"""
    await websocket.accept()
    
    try:
        while True:
            # Generate and send momentum data every second
            if match_id in data_store.matches:
                match = data_store.matches[match_id]
                momentum = MockDataGenerator.generate_momentum_data(
                    match_id, 
                    match.current_minute
                )
                
                # Update minute (simulate match progression)
                match.current_minute += 1/60  # 1 second = 1/60 minute
                
                await websocket.send_json({
                    "type": "momentum_update",
                    "data": momentum.dict()
                })
            
            await asyncio.sleep(1)  # Update every second
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# ==================== Startup Event ====================

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 Futstar Momentum Trading API Started")
    print("📊 Mock data initialized")
    print("⚡ Ready for trading on Solana")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
