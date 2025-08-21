# Stock Alert App (Starter Full Stack)

Services:
- **edge**: Traefik edge router (port 80 -> frontend and API Gateway)
- **api-gateway**: FastAPI BFF proxying to backend services
- **auth-service**: FastAPI + Postgres + Alembic (users + JWT)
- **user-service**: FastAPI + Postgres + Alembic (portfolios & watchlists)
- **analyzer-service**: FastAPI (dummy analysis stub)
- **notifier-service**: FastAPI (dummy notifier stub)
- **db**: Postgres
- **redpanda**: Kafka-compatible broker
- **frontend**: React (Vite)

## Quick start
```bash
docker compose up --build
```
- App UI: http://localhost
- API Gateway: http://localhost/api/health
- Auth service: http://localhost/auth/health (via Traefik routes) or internal http://auth-service:8003/health
