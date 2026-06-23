# Stock Alert App - Full Stack Microservices

A comprehensive stock market scanning and alerting platform with real-time technical analysis, user authentication, portfolio management, and automated notifications.

## Architecture Overview

### Microservices
- **edge**: Traefik edge router (port 80) - Routes all incoming traffic
- **api-gateway**: FastAPI BFF (Backend for Frontend) - Service orchestration layer
- **scanner-service**: FastAPI - Real-time stock scanning with technical analysis
- **market-service**: FastAPI + PostgreSQL - Bhavcopy ingestion & price history API ⭐ **NEW**
- **auth-service**: FastAPI + PostgreSQL + Alembic - User authentication & JWT
- **user-service**: FastAPI + PostgreSQL + Alembic - Portfolios, watchlists, alerts & notification history
- **analyzer-service**: FastAPI - Stock analysis with market-service integration
- **notifier-service**: FastAPI + Kafka consumer - Durable in-app alert notifications
- **db**: PostgreSQL - Persistent data storage (multi-database per service)
- **redpanda**: Kafka broker - Async message queue for inter-service communication
- **frontend**: React + Vite + Tailwind CSS - Modern responsive UI

## Features

### 🆕 Market Service
Local stock market data ingestion and API for Indian stocks (NSE Bhavcopy data).

#### Capabilities
- **Bhavcopy Ingestion**: Automated daily ingestion of NSE OHLCV data
- **Price History API**: Fast local queries - no external API calls or rate limits
- **Index Constituents**: Fetch & cache NSE index membership (Nifty 50, Nifty 100)
- **Manual Backfill**: Historical data ingestion for analysis without waiting for daily runs
- **DB-backed Storage**: PostgreSQL for reliability and complex queries

### Stock Scanner Service
Real-time technical analysis engine for Indian stocks (NSE).

#### Capabilities
- **Automatic Stock Screening**: Scan Nifty 50 or Nifty 100 stocks simultaneously
- **Market-Service Integration**: All price data from local Bhavcopy DB (no external APIs)
- **Technical Indicators**:
  - RSI (Relative Strength Index) - Momentum oscillator
  - MACD (Moving Average Convergence Divergence) - Trend following
  - Moving Averages (50-day & 20-day) - Trend identification
  - Volume Spike Detection - Abnormal trading activity
  - 20-day Breakout Detection - Support/resistance breaks
  - 5-day Momentum - Short-term price movement

#### Recommendation Engine
Automated scoring system (0-10 scale) generating recommendations:
- **STRONG BUY** (score ≥ 6): Multiple bullish indicators aligned
- **BUY** (score ≥ 3): Net positive technical signals
- **HOLD** (score ≥ 0): Mixed or neutral signals
- **SELL** (score < 0): Net negative technical signals

#### Features
- ✅ Real-time SSE streaming - See results as they complete
- ✅ User watchlist integration - Highlights your tracked stocks
- ✅ Result persistence - Access historical scan data
- ✅ Concurrent processing - Scans 50-100 stocks in ~30-60 seconds
- ✅ Dynamic symbol loading - Index constituents from market-service

#### Scoring Criteria
```
RSI < 30          → +3 points (oversold, buying opportunity)
RSI 30-50         → +1 point
RSI > 70          → -2 points (overbought, caution)
MACD bullish      → +2 points
MA trend bullish  → +2 points
5-day momentum>2% → +1 point
Volume spike      → +1 point
20-day breakout   → +1 point
```

### Authentication & User Management
- JWT-based authentication
- User registration and login
- Session management with refresh tokens

### Portfolio & Watchlist Management
- Create and manage multiple watchlists
- Track personal investment portfolios
- Real-time watchlist integration with scanner

### Database Strategy
- **Per-service databases** for independence and scalability
- Alembic migrations for schema versioning
- Cross-service data access via APIs (not direct DB queries)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Linux/macOS (or WSL on Windows)

### Launch Application
```bash
docker compose up --build
```

### Access Points
| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost | Main web UI |
| **API Gateway** | http://localhost/api | REST API base |
| **Scanner** | http://localhost/api/scan/stream | Real-time scan results |
| **Traefik Dashboard** | http://localhost:8080 | Infrastructure monitoring |

---

## Usage Guide

### Scanner Feature Walkthrough

#### 1. Access Scanner UI
Navigate to **Scanner** tab in the web application.

#### 2. Start a Scan
```
Select scope: Nifty 50 (default) or Nifty 100
Click "Start Scan"
```

#### 3. Real-Time Results
Results stream in as they complete (SSE technology):
- See score and recommendation for each stock
- Stocks in your watchlist highlighted
- Color-coded badges (green for BUY, red for SELL)

#### 4. View Details
Click any stock row to open the detail drawer:
- Full technical analysis breakdown
- RSI, MACD trends
- Volume metrics
- Momentum analysis
- Price history

### API Endpoints

#### Market Data API
```bash
# Get index constituents (e.g., Nifty 50)
curl "http://localhost/api/market/constituents/nifty50"

# Refresh index constituents cache
curl -X POST "http://localhost/api/market/constituents/refresh"

# Get OHLCV history for a symbol (last 130 days)
curl -H "X-User-Id: 1" \
  "http://localhost/api/market/history/RELIANCE"

# Get ingestion status
curl "http://localhost/api/market/ingest/status"

# Manually trigger Bhavcopy ingestion
curl -X POST "http://localhost/api/market/ingest/manual?trade_date=2026-05-28"
```

#### Scan via API
```bash
# Start real-time scan with SSE streaming
curl -H "X-User-Id: 1" \
  "http://localhost/api/scan/stream?scope=nifty50"

# Get latest scan results (JSON)
curl -H "X-User-Id: 1" \
  "http://localhost/api/scan/results"
```

#### Internal Service APIs
```bash
# Market Service (port 8006)
curl "http://localhost:8006/docs"

# Scanner Service (port 8005)
curl "http://localhost:8005/docs"
```

---

## Development

### Project Structure
```
├── backend/
│   ├── market-service/            # ⭐ NEW: Bhavcopy ingestion & price API
│   ├── scanner-service/           # Real-time stock analysis
│   ├── auth-service/              # User authentication & JWT
│   ├── user-service/              # Portfolios & watchlists
│   ├── analyzer-service/          # Stock analysis with market data
│   └── notifier-service/          # Placeholder for notifications
├── api-gateway/                   # FastAPI BFF layer
├── frontend/                      # React + Vite UI
├── edge/                          # Traefik configuration
└── docker-compose.yml             # Full stack orchestration
```

### Scanner Service Architecture

#### Data Flow
```
1. Frontend → API Gateway (/api/scan/stream)
2. Gateway → Scanner Service
3. Scanner fetches index constituents from Market Service
4. For each symbol:
   - Fetch 200 days of OHLCV from Market Service (local DB, no external calls)
   - Compute technical indicators (RSI, MACD, MA50, etc.)
   - Generate recommendation score
5. Streams results via SSE to frontend
6. Persists results to scanner-service database
7. Matches watchlist via user-service API
```

#### Threading Model
- **Thread Pool**: 8 concurrent workers for stock analysis
- **Async/Await**: Non-blocking SSE streaming
- **Data Sources**: Market-service only (local DB - no external APIs)
- **Symbol Resolution**: Dynamic fetching from market-service constituents API

#### Data Sources
- **Stock Data**: NSE Bhavcopy via market-service local PostgreSQL
- **Price Period**: 200 days of daily OHLCV data per stock
- **Symbols**: Bare NSE tickers (RELIANCE, INFY, TCS, etc.)
- **Rate Limiting**: None - all data local

### Environment Configuration

#### Key Environment Variables
```env
# Database
POSTGRES_USER=stock
POSTGRES_PASSWORD=stockpass
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Authentication
JWT_SECRET=your-secret-key
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Service URLs (internal Docker network)
ANALYZER_URL=http://analyzer-service:8002
NOTIFIER_URL=http://notifier-service:8001
AUTH_URL=http://auth-service:8003
USER_URL=http://user-service:8004
SCANNER_URL=http://scanner-service:8005
MARKET_URL=http://market-service:8006
MARKET_SERVICE_URL=http://market-service:8006
KAFKA_BROKER=redpanda:9092
```

### Running Tests

#### Health Checks
```bash
# Check all services
docker compose ps

# Gateway health
curl http://localhost/api/health

# Scanner service health
docker compose exec scanner-service curl http://localhost:8005/health
```

#### Manual Scanner Test
```bash
# With authentication
TOKEN=$(curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost/api/scan/stream?scope=nifty50"
```

---

## Known Limitations & Future Enhancements

### Current Limitations
1. **Bhavcopy Data Lag**
   - Bhavcopy data is published daily after market close
   - Scan results reflect previous trading day data
   - Future: Real-time data ingestion for intraday scans

2. **Market-Service Availability**
   - All scanner and analyzer functions depend on market-service
   - Data freshness depends on daily ingestion schedule
   - Future: Scheduled background jobs for automated daily ingestion

3. **Notification Channels**
   - In-app notifications are implemented through Redpanda/Kafka
   - Email and push delivery remain optional future channels

### Planned Enhancements
- [ ] Scheduled background jobs for daily Bhavcopy ingestion (APScheduler integration)
- [ ] Redis caching for constitutent updates (6-hour TTL)
- [ ] Real-time market data integration
- [ ] Advanced filtering on scanner results
- [ ] Alert creation from scan recommendations
- [ ] Email/push notifications for watchlist stocks
- [ ] Portfolio performance tracking
- [ ] Historical scan result comparisons
- [ ] Price alerts at support/resistance levels

---

## Troubleshooting

### Scanner Returns No Data
**Problem**: "No data returned for {symbol}" in logs

**Solutions**:
1. Check market-service is running: `docker compose ps market-service`
2. Verify Bhavcopy data was ingested: `docker compose logs market-service | grep "Ingested"`
3. Check database connectivity: `docker compose exec market-service curl http://localhost:8006/health`
4. Restart service: `docker compose restart scanner-service market-service`
5. Check logs: `docker compose logs -f scanner-service`

### Market-Service Symbols Not Found
**Problem**: "404 No data for {symbol}" when querying market history

**Solutions**:
1. Run backfill script: `./backend/market-service/backfill.sh <token> <days>`
2. Verify symbol spelling: Use bare NSE tickers (RELIANCE, not RELIANCE.NS)
3. Check constituents cache: `curl http://localhost/api/market/constituents/nifty50`
4. Refresh constituents: `curl -X POST http://localhost/api/market/constituents/refresh`

### SSE Stream Not Updating
**Problem**: Frontend shows "Connecting..." indefinitely

**Solutions**:
1. Verify API Gateway is running: `docker compose ps api-gateway`
2. Check CORS headers: `curl -i http://localhost/api/scan/stream`
3. Restart gateway: `docker compose restart api-gateway`
4. Browser console logs: Check for EventSource errors
5. Verify market-service availability: `docker compose logs market-service`

### Database Connection Issues
**Problem**: Service fails to connect to PostgreSQL

**Solutions**:
1. Check DB is running: `docker compose ps db`
2. Verify credentials in `.env`
3. Check network: `docker compose exec db psql -U stock -d stockdb -c "SELECT 1"`
4. Run migrations: `docker compose exec market-service alembic upgrade head`

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python web framework)
- **Server**: Uvicorn (ASGI server)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Data Processing**: Pandas, NumPy
- **Market Data**: NSE Bhavcopy CSV ingestion (local PostgreSQL storage)
- **Task Scheduling**: APScheduler (background jobs)
- **Async**: httpx, asyncio
- **Task Queue**: Redpanda (Kafka API compatible)

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Fetch API
- **State**: React hooks

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Routing**: Traefik v3
- **Authentication**: JWT (PyJWT)
- **API Documentation**: Swagger/OpenAPI

---

## Contributing

### Code Style
- Python: Follow PEP 8 with Black formatter
- Frontend: ESLint + Prettier configuration

### Git Workflow
```bash
git checkout -b feature/your-feature
# Make changes and commit with meaningful messages
git push origin feature/your-feature
# Create pull request
```

---

## License

This project is open source and available under the MIT License.

---

## Contact & Support

For issues, feature requests, or questions:
- Check existing issues on GitHub
- Create a new issue with reproduction steps
- Include relevant logs and environment details
