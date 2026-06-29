# 📈 Stock Alert

> A production-inspired cloud-native stock market monitoring platform built using a microservices architecture, Kubernetes, GitOps, and modern DevOps practices.

---

## Overview

Stock Alert is a full-stack microservices application designed to demonstrate production-grade application deployment and platform engineering practices.

Unlike traditional CRUD applications, Stock Alert focuses on cloud-native architecture, continuous delivery, GitOps, container orchestration, scalable microservices, secure authentication, and operational readiness.

The application enables users to:

* Create secure accounts
* Build investment portfolios
* Maintain multiple watchlists
* Configure price alerts
* Run technical analysis
* Perform stock scans
* View market trends
* Receive notifications

The entire platform is deployed on Kubernetes using Helm and ArgoCD, with automated CI/CD pipelines publishing Docker images to GitHub Container Registry (GHCR).

---

# Architecture

```
                         GitHub
                            │
                            │
                  GitHub Actions CI
                            │
                            ▼
                  Build Docker Images
                            │
                            ▼
                        GHCR Images
                            │
                            ▼
                   GitOps Repository
                            │
                       (Image Update)
                            │
                            ▼
                        ArgoCD Sync
                            │
                            ▼
                    Kubernetes Cluster
                            │
        ┌────────────────────────────────────┐
        │                                    │
        ▼                                    ▼
   React Frontend                     API Gateway
                                             │
      ┌──────────────────────────────────────┴─────────────────────────────────────┐
      │              │             │             │             │                   │
      ▼              ▼             ▼             ▼             ▼                   ▼
 Auth Service   User Service  Analyzer   Scanner   Market Service   Notifier Service
```

---

# Repository Structure

```
stock-alert/

├── frontend/
│
├── api-gateway/
│
├── backend/
│   ├── auth-service/
│   ├── user-service/
│   ├── analyzer-service/
│   ├── scanner-service/
│   ├── notifier-service/
│   └── market-service/
│
├── .github/
│   └── workflows/
│
└── README.md
```

---

# Microservices

## API Gateway

Acts as the Backend-for-Frontend (BFF).

Responsibilities

* JWT validation
* Authentication
* Request routing
* Request logging
* Rate limiting
* Security boundary

---

## Auth Service

Responsible for authentication.

Features

* User Registration
* Login
* Password hashing
* JWT generation

---

## User Service

Responsible for user data.

Features

* Portfolio Management
* Watchlists
* Alerts
* Notifications

---

## Analyzer Service

Performs market analysis.

Features

* Historical price retrieval
* Technical indicators
* Market trend analysis
* Yahoo Finance integration

---

## Scanner Service

Runs stock scans.

Features

* Real-time scanner
* Scheduled scans
* APScheduler integration
* SSE (Server Sent Events)

---

## Market Service

Provides market information.

Features

* Market snapshot
* Index information
* Public APIs

---

## Notifier Service

Notification engine.

Supports

* Alert delivery
* Event processing
* Notification history

---

# Frontend

Built using

* React
* Axios
* Modern Component Architecture

Features

* Authentication
* Portfolio Management
* Watchlists
* Scanner
* Alerts
* Notifications
* Market Dashboard

---

# Technology Stack

## Backend

* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* JWT
* APScheduler

## Frontend

* React
* Axios
* JavaScript

## Infrastructure

* Docker
* Kubernetes
* Helm
* NGINX Ingress
* ConfigMaps
* Secrets

## CI/CD

* GitHub Actions
* GitHub Container Registry
* ArgoCD
* GitOps

---

# Continuous Integration

Every push to the main branch automatically:

* Detects changed services
* Builds only modified Docker images
* Pushes images to GHCR
* Updates Helm values inside GitOps repository
* Triggers ArgoCD deployment

This significantly reduces build time by avoiding unnecessary image builds.

---

# Deployment Flow

```
Developer

    │

    ▼

Git Push

    │

    ▼

GitHub Actions

    │

    ▼

Build Changed Services

    │

    ▼

Push Images to GHCR

    │

    ▼

Update GitOps Repository

    │

    ▼

ArgoCD Detects Change

    │

    ▼

Deploy to Kubernetes
```

---

# Security

* JWT Authentication
* Password hashing
* API Gateway authentication
* Internal service communication
* Kubernetes Secrets
* Rate limiting
* Request validation

---

# Features

### Authentication

* User Registration
* Login
* JWT Authentication

### Portfolio

* Add holdings
* View portfolio

### Watchlists

* Multiple watchlists
* Add/remove symbols

### Alerts

* Create alerts
* Enable/Disable alerts

### Scanner

* Live scanning
* Scheduled scanning

### Notifications

* Unread count
* Mark read
* Notification history

### Market

* Market snapshot
* Historical prices

---

# Local Development

Clone the repository

```
git clone https://github.com/<username>/stock-alert.git
```

Start the application using the platform infrastructure and GitOps repositories.

---

# Related Repositories

| Repository        | Purpose                      |
| ----------------- | ---------------------------- |
| my-platform-infra | Infrastructure provisioning  |
| my-gitops         | GitOps deployment repository |
| stock-alert       | Application source code      |

---

# Future Enhancements

* OpenTelemetry
* Prometheus
* Grafana
* Loki
* Tempo
* Distributed Tracing
* Horizontal Pod Autoscaler
* External Secrets
* RBAC
* Network Policies
* KEDA
* Multi-environment GitOps
* Canary Deployments

---

# Project Status

Current Status

✅ Production-inspired Kubernetes deployment

✅ GitOps enabled

✅ Automated CI/CD

✅ Microservices architecture

🚧 Observability stack (In Progress)

---

# Author

**Rakesh H**

Platform Engineer | DevOps | Cloud | Kubernetes | Observability

This project is built for continuous learning and to demonstrate production-grade cloud-native engineering practices.
