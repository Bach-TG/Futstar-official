# Futstar Deployment Guide for Solana Cypherpunk Hackathon

## Quick Start for Judges

### 1. Repository Structure
```
futstar-momentum-trading/
├── README.md                 # Main documentation
├── ARCHITECTURE.md          # System architecture details
├── contracts/               # Solana smart contracts (Rust/Anchor)
│   └── programs/
│       └── momentum-trading/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main API server
│   └── oracle_service.py   # Oracle for momentum updates
├── frontend/               # React Native mobile app
│   └── src/
│       └── screens/
└── docs/                   # Additional documentation
```

### 2. Key Features Demonstrated

✅ **Solana Integration**
- Smart contracts written in Rust using Anchor framework
- On-chain position management and settlement
- Oracle system for momentum updates

✅ **Innovation**
- First-ever football momentum trading platform
- Real-time betting on match dynamics
- 5-minute trading windows with instant settlement

✅ **Technical Excellence**
- Microservices architecture
- WebSocket for real-time updates
- Mobile-first design

## Local Development Setup

### Prerequisites
```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/v1.17.0/install)"

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest
avm use latest

# Install Node.js and Python
# Node.js 18+ and Python 3.10+ required
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Smart Contract Deployment
```bash
cd contracts

# Build contracts
anchor build

# Deploy to devnet
anchor deploy --provider.cluster devnet

# Get program ID
solana address -k target/deploy/futstar_momentum_trading-keypair.json
```

### Frontend Setup
```bash
cd frontend
npm install

# For Expo
npx expo start

# For web preview
npx expo start --web
```

## Testing the Application

### 1. API Testing
```bash
# Check API health
curl http://localhost:8000/

# Get live matches
curl http://localhost:8000/api/matches

# Get momentum data
curl http://localhost:8000/api/matches/match_001/momentum
```

### 2. WebSocket Testing
Connect to `ws://localhost:8000/ws/momentum/match_001` for real-time updates

### 3. Smart Contract Testing
```bash
cd contracts
anchor test
```

## Production Deployment

### Solana Mainnet Deployment
1. Update Anchor.toml with mainnet RPC
2. Ensure sufficient SOL for deployment
3. Run: `anchor deploy --provider.cluster mainnet`
4. Update program ID in frontend/backend

### Backend Deployment (AWS)
```bash
# Build Docker image
docker build -t futstar-backend backend/

# Deploy to ECS/Fargate
# Use provided CloudFormation template
```

### Frontend Deployment
```bash
# Build for production
cd frontend
expo build:android
expo build:ios

# Submit to app stores
```

## Environment Variables

### Backend (.env)
```env
SOLANA_RPC_URL=https://api.devnet.solana.com
PROGRAM_ID=FuTsTar11111111111111111111111111111111111
STATSPERFORM_API_KEY=your_api_key
DATABASE_URL=postgresql://user:pass@localhost/futstar
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_SOLANA_RPC=https://api.devnet.solana.com
```

## Key Innovations for Judges

### 1. **Novel Use Case**
- Bridges traditional sports betting with DeFi
- Introduces momentum-based trading concept
- Targets massive football fan market (3.5B+)

### 2. **Technical Implementation**
- Sub-second momentum calculations
- Real-time WebSocket updates
- Atomic on-chain settlement
- Mobile-optimized for mass adoption

### 3. **Market Fit**
- $2.5B addressable market
- Partnerships with major football influencers
- Clear path to user acquisition

### 4. **Solana Advantages**
- <$0.01 transaction fees enable micro-betting
- Sub-second confirmation for real-time trading
- Scalability for millions of users

## Demo Credentials

### Wallet for Testing
- Use Phantom or Solflare wallet
- Request devnet SOL from: https://solfaucet.com

### Sample Match IDs
- `match_001`: Arsenal vs Tottenham (Live)
- `match_002`: Liverpool vs Man City (Live)
- `match_003`: Barcelona vs Real Madrid (Live)

## Troubleshooting

### Common Issues

1. **Anchor build fails**
```bash
# Clear build cache
anchor clean
rm -rf target/
anchor build
```

2. **Python dependencies error**
```bash
# Use Python 3.10+
python --version
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Frontend won't start**
```bash
# Clear cache
npm cache clean --force
rm -rf node_modules
npm install
```

## Resources

- **Pitch Deck**: See uploaded PDF
- **Demo Video**: See uploaded MP4
- **Live Demo**: https://futstar.fun (coming soon)
- **Twitter**: @Futstarfun
- **Discord**: discord.gg/futstar

## Contact

For technical questions during judging:
- Email: tech@futstar.fun
- Telegram: @futstar_support

---

**Thank you for reviewing Futstar!** 🚀⚽

We're excited to bring millions of football fans to Solana through momentum trading.
