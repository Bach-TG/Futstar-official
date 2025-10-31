"""
Futstar Oracle Service
Updates momentum index on-chain from off-chain data sources
"""

import asyncio
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.keypair import Keypair
from solana.transaction import Transaction
from solana.system_program import TransferParams, transfer
from anchorpy import Provider, Program, Idl, Wallet
import base58
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('FutstarOracle')

# Configuration
SOLANA_RPC_URL = "https://api.devnet.solana.com"
PROGRAM_ID = "FuTsTar11111111111111111111111111111111111"
ORACLE_UPDATE_INTERVAL = 5  # seconds
DATA_API_URL = "http://localhost:8000"

@dataclass
class MatchMomentum:
    """Match momentum data structure"""
    match_id: str
    momentum_index: int
    possession: float
    shots_home: int
    shots_away: int
    xg_home: float
    xg_away: float
    timestamp: datetime

class MomentumOracle:
    """
    Oracle service that fetches match data and updates on-chain momentum
    """
    
    def __init__(self, keypair_path: str):
        """Initialize oracle with keypair"""
        self.keypair = self._load_keypair(keypair_path)
        self.client = AsyncClient(SOLANA_RPC_URL)
        self.active_matches: Dict[str, MatchMomentum] = {}
        self.update_history: List[Dict] = []
        logger.info(f"Oracle initialized with pubkey: {self.keypair.public_key}")
    
    def _load_keypair(self, path: str) -> Keypair:
        """Load keypair from JSON file"""
        try:
            with open(path, 'r') as f:
                secret = json.load(f)
            return Keypair.from_secret_key(bytes(secret))
        except Exception as e:
            logger.error(f"Failed to load keypair: {e}")
            # Return a generated keypair for demo
            return Keypair.generate()
    
    async def fetch_match_data(self, match_id: str) -> Optional[MatchMomentum]:
        """Fetch current match momentum from data API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DATA_API_URL}/api/matches/{match_id}/momentum"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return MatchMomentum(
                            match_id=match_id,
                            momentum_index=data['momentum_index'],
                            possession=data['possession'],
                            shots_home=data['shots_home'],
                            shots_away=data['shots_away'],
                            xg_home=data['xg_home'],
                            xg_away=data['xg_away'],
                            timestamp=datetime.fromisoformat(data['timestamp'])
                        )
        except Exception as e:
            logger.error(f"Error fetching match data: {e}")
        return None
    
    async def update_momentum_on_chain(self, match_id: str, momentum_index: int) -> bool:
        """
        Update momentum index on-chain for a specific match
        
        This would call the update_momentum_index instruction in the smart contract
        """
        try:
            # In production, this would create and send a transaction
            # to update the on-chain momentum index
            
            logger.info(f"Updating on-chain momentum for {match_id}: {momentum_index}")
            
            # Simulate transaction creation
            tx_signature = base58.b58encode(bytes(range(64))).decode('utf-8')
            
            # Record update
            self.update_history.append({
                'match_id': match_id,
                'momentum_index': momentum_index,
                'timestamp': datetime.now().isoformat(),
                'tx_signature': tx_signature
            })
            
            # Keep only last 100 updates in memory
            if len(self.update_history) > 100:
                self.update_history = self.update_history[-100:]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update on-chain momentum: {e}")
            return False
    
    async def validate_momentum_change(self, 
                                      old_index: int, 
                                      new_index: int,
                                      max_change: int = 20) -> bool:
        """
        Validate momentum change is within acceptable bounds
        Prevents extreme/suspicious changes
        """
        change = abs(new_index - old_index)
        if change > max_change:
            logger.warning(f"Momentum change {change} exceeds max {max_change}")
            return False
        return True
    
    async def monitor_match(self, match_id: str):
        """Monitor a specific match and update momentum"""
        logger.info(f"Starting monitoring for match {match_id}")
        
        last_momentum = 50  # Default starting momentum
        consecutive_failures = 0
        max_failures = 5
        
        while consecutive_failures < max_failures:
            try:
                # Fetch current momentum
                momentum_data = await self.fetch_match_data(match_id)
                
                if momentum_data:
                    # Validate the change
                    if await self.validate_momentum_change(
                        last_momentum, 
                        momentum_data.momentum_index
                    ):
                        # Update on-chain
                        success = await self.update_momentum_on_chain(
                            match_id,
                            momentum_data.momentum_index
                        )
                        
                        if success:
                            last_momentum = momentum_data.momentum_index
                            self.active_matches[match_id] = momentum_data
                            consecutive_failures = 0
                            logger.info(
                                f"Updated {match_id}: momentum={momentum_data.momentum_index}"
                            )
                        else:
                            consecutive_failures += 1
                    else:
                        logger.warning(f"Invalid momentum change for {match_id}")
                else:
                    consecutive_failures += 1
                    
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                consecutive_failures += 1
            
            # Wait before next update
            await asyncio.sleep(ORACLE_UPDATE_INTERVAL)
        
        logger.warning(f"Stopping monitor for {match_id} due to failures")
        if match_id in self.active_matches:
            del self.active_matches[match_id]
    
    async def fetch_live_matches(self) -> List[str]:
        """Fetch list of live matches from API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{DATA_API_URL}/api/matches") as response:
                    if response.status == 200:
                        matches = await response.json()
                        return [m['match_id'] for m in matches if m['status'] == 'live']
        except Exception as e:
            logger.error(f"Error fetching live matches: {e}")
        return []
    
    async def run(self):
        """Main oracle loop"""
        logger.info("Starting Futstar Oracle Service")
        
        while True:
            try:
                # Get list of live matches
                live_matches = await self.fetch_live_matches()
                
                # Start monitoring new matches
                for match_id in live_matches:
                    if match_id not in self.active_matches:
                        # Start monitoring in background
                        asyncio.create_task(self.monitor_match(match_id))
                
                # Log status
                logger.info(f"Monitoring {len(self.active_matches)} matches")
                
                # Wait before checking for new matches
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
    
    async def get_status(self) -> Dict:
        """Get current oracle status"""
        return {
            'oracle_pubkey': str(self.keypair.public_key),
            'active_matches': len(self.active_matches),
            'matches': {
                match_id: {
                    'momentum_index': data.momentum_index,
                    'last_update': data.timestamp.isoformat()
                }
                for match_id, data in self.active_matches.items()
            },
            'recent_updates': self.update_history[-10:],
            'uptime': time.time()
        }
    
    async def close(self):
        """Clean up resources"""
        await self.client.close()
        logger.info("Oracle service closed")

# Health check endpoint using FastAPI
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Futstar Oracle Service")
oracle: Optional[MomentumOracle] = None

@app.on_event("startup")
async def startup_event():
    """Initialize oracle on startup"""
    global oracle
    oracle = MomentumOracle("./oracle_keypair.json")
    asyncio.create_task(oracle.run())
    logger.info("Oracle API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if oracle:
        await oracle.close()

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Futstar Oracle"}

@app.get("/status")
async def get_status():
    """Get oracle status"""
    if oracle:
        status = await oracle.get_status()
        return JSONResponse(content=status)
    return {"error": "Oracle not initialized"}

@app.get("/history")
async def get_history():
    """Get recent update history"""
    if oracle:
        return {"updates": oracle.update_history}
    return {"error": "Oracle not initialized"}

if __name__ == "__main__":
    # For standalone testing
    async def main():
        oracle_service = MomentumOracle("./oracle_keypair.json")
        try:
            await oracle_service.run()
        except KeyboardInterrupt:
            logger.info("Shutting down oracle...")
            await oracle_service.close()
    
    asyncio.run(main())
