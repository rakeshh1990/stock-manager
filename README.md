# 📈 Stock Momentum Alert (Dockerized)

Analyzes Indian stocks for 15%+ upward momentum in 3 months and sends email alerts for:
- 📉 Stocks to Exit
- 🚀 Stocks to Watch

## 🔧 Setup

1. Update `config.py` with your Gmail & app password
2. Add your current holdings to `invested_stocks.csv`

## 🐳 Run via Docker

```bash
docker-compose up --build
