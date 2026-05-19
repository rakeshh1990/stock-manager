# Stock Alert App - Full Stack Microservices

A comprehensive stock market scanning and alerting platform with real-time technical analysis, user authentication, portfolio management, and automated notifications.

## Architecture Overview

### Microservices
- **edge**: Traefik edge router (port 80) - Routes all incoming traffic
- **api-gateway**: FastAPI BFF (Backend for Frontend) - Service orchestration layer
- **scanner-service**: FastAPI - Real-time stock scanning with technical analysis ⭐ **NEW**
- **auth-service**: FastAPI + PostgreSQL + Alembic - User authentication & JWT
- **user-service**: FastAPI + PostgreSQL + Alembic - Portfolios & watchlists
- **analyzer-service**: FastAPI (placeholder) - Advanced stock analysis
- **notifier-service**: FastAPI (placeholder) - Alert notifications
- **db**: PostgreSQL - Persistent data storage (multi-database per service)
- **redpanda**: Kafka broker - Async message queue for inter-service communication
- **frontend**: React + Vite + Tailwind CSS - Modern responsive UI

## Features

### 🆕 Stock Scanner Service
Real-time technical analysis engine for Indian stocks (NSE).

#### Capabilities
- **Automatic Stock Screening**: Scan Nifty 50 or Nifty 100 stocks simultaneously
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
- ✅ Intelligent caching - Request throttling to prevent API rate-limiting

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

#### Scan via API
```bash
# Start real-time scan with SSE streaming
curl -H "X-User-Id: 1" \
  "http://localhost/api/scan/stream?scope=nifty50"

# Get latest scan results (JSON)
curl -H "X-User-Id: 1" \
  "http://localhost/api/scan/results"
```

#### Scanner Service Direct (Internal)
```bash
# Health check
curl http://localhost:8005/docs

# Direct scan endpoint (requires scanner-service access)
curl "http://scanner-service:8005/scan/stream?scope=nifty50"
```

---

## Development

### Project Structure
```
├── backend/
│   ├── scanner-service/          # ⭐ NEW: Real-time stock analysis
│   ├── auth-service/              # User authentication & JWT
│   ├── user-service/              # Portfolios & watchlists
│   ├── analyzer-service/          # Placeholder for advanced analysis
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
3. Scanner fetches 6-month historical OHLCV via yfinance
4. Computes technical indicators (pandas)
5. Generates recommendation score
6. Streams results via SSE
7. Persists to database
```

#### Threading Model
- **Thread Pool**: 5 concurrent workers for stock analysis
- **Async/Await**: Non-blocking SSE streaming
- **Request Throttling**: 1-3 second delays between API calls
- **Smart Retries**: 3-attempt exponential backoff on failures

#### Data Sources
- **Stock Data**: Yahoo Finance via `yfinance` library
- **Period**: 6 months of daily OHLCV data per stock
- **Exchange**: NSE (India) with `.NS` suffix
- **Rate Limiting**: Intelligent backoff to prevent blocks

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
1. **yfinance Rate Limiting**
   - Current solution: Random delays (1-3s) between requests
   - Future: Implement Redis caching layer for 24-hour data freshness

2. **NSE Data Limitations**
   - NSE API lacks official historical data endpoint
   - Using yfinance as workaround (reliable with backoff strategy)
   - Upgrade path: TwelveData or AlphaVantage paid APIs

3. **Placeholder Services**
   - Analyzer Service: Ready for ML-based advanced analysis
   - Notifier Service: Ready for Kafka-driven alerts

### Planned Enhancements
- [ ] Redis caching for stock data (24h TTL)
- [ ] Advanced filtering on scanner results
- [ ] Alert creation from scan recommendations
- [ ] Email/push notifications for watchlist stocks
- [ ] Portfolio performance tracking
- [ ] Historical scan result comparisons
- [ ] Price alerts at support/resistance levels
- [ ] Upgrade to paid stock API (TwelveData/AlphaVantage)

---

## Troubleshooting

### Scanner Returns No Data
**Problem**: "No data returned for {symbol}" in logs

**Solutions**:
1. Check API rate limiting: Add delays between requests
2. Verify network connectivity: `docker compose exec scanner-service curl https://query1.finance.yahoo.com`
3. Restart service: `docker compose restart scanner-service`
4. Check logs: `docker compose logs -f scanner-service`

### SSE Stream Not Updating
**Problem**: Frontend shows "Connecting..." indefinitely

**Solutions**:
1. Verify API Gateway middleware: Check SSE path bypass is configured
2. Check CORS headers: `curl -i http://localhost/api/scan/stream`
3. Restart gateway: `docker compose restart api-gateway`
4. Browser console logs: Check for WebSocket/EventSource errors

### Database Connection Issues
**Problem**: Service fails to connect to PostgreSQL

**Solutions**:
1. Check DB is running: `docker compose ps db`
2. Verify credentials in `.env`
3. Check network: `docker compose exec db psql -U stock -d stockdb -c "SELECT 1"`
4. Run migrations: `docker compose exec scanner-service alembic upgrade head`

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python web framework)
- **Server**: Uvicorn (ASGI server)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Data Processing**: Pandas, NumPy
- **Stock Data**: yfinance
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
