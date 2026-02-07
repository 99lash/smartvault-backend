# SMRTVLT API

Backend API for SMRTVLT, built with FastAPI, PostgreSQL, Redis, and Docker. Designed using clean architecture (domain → application → infrastructure → API) with migration-driven schema management.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure-simplified)
- [Getting Started (Local Dev)](#getting-started-local-dev)
  - [Prerequisites](#prerequisites)
  - [Start everything](#start-everything)
- [Common Commands (Makefile)](#common-commands-makefile)
  - [API / Docker](#api--docker)
  - [Database (Postgres + Alembic)](#database-postgres--alembic)
  - [Cache (Redis)](#cache-redis)
- [Migrations](#migrations)
- [All command cheat sheets](#all-command-cheat-sheets)
- [Current Features](#current-features)
  - [Authentication & Users](#authentication--users)
  - [Vault Management](#vault-management)
  - [Vault Membership](#vault-membership)
  - [Vault Unlocking](#vault-unlocking)
  - [Security Features](#security-features)
  - [Quality Assurance](#quality-assurance)
- [Future Features](#future-features)
- [Development Notes](#development-notes)
- [Environment Variables](#environment-variables)
- [License](#license)

## Tech Stack

- **API:** FastAPI
- **Database:** PostgreSQL 16
- **Cache / Rate-limit:** Redis 7
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Auth:** Password hashing (PBKDF2), JWT tokens, OTP tickets
- **WebSockets:** FastAPI native WebSocket support
- **Biometrics:** Face recognition integration
- **Infra:** Docker + Docker Compose
- **DX:** Makefile helpers

## Project Structure (Simplified)

```
app/
├── api/            # FastAPI routers & deps
├── application/    # Use cases, ports, services
├── domain/         # Domain models & value objects
├── infrastructure/ # DB, cache, messaging, security
├── schemas/        # Pydantic request/response models
├── tests/          # Unit & API tests
└── main.py         # App bootstrap
```

## Getting Started (Local Dev)

### Prerequisites

- Docker + Docker Compose
- Make

### Start everything
- requirements: `git bash`, install `make` or `wsl` 
- [`wsl setup instructions`](Docs/wsl.md)
- if you don't like make commands here's the [`Default Docker Commands`](Docs/docker-commands.md)
```bash
make dev
```

This will:
- Build images
- Start API, Postgres, Redis
- Apply DB migrations
- Print DB + Redis status

API will be available at:

```
http://localhost:8000
```

## Common Commands (Makefile)
Cheat sheet available in [`docker-commands.md`](Docs/docker-commands.md)

### API / Docker

```bash
make up        # build & start services
make logs      # tail API logs
make stop      # stop services
make down      # remove containers
make test      # run pytest
```

### Database (Postgres + Alembic)
Cheat sheet available in [`Postgres`](Docs/postgres.md) and [`Alembic`](Docs/alembic.md)

```bash
make migrate               # apply migrations
make migration msg="..."   # create new migration
make rollback              # downgrade last migration
make psql                  # open psql shell
make db-reset              # DEV ONLY: reset DB
```

### Cache (Redis)
Cheat sheet available in [`redis`](Docs/redis.md)

```bash
make redis         # open Redis CLI
make redis-info    # Redis server info
make redis-flush   # DEV ONLY: flush Redis DB
```

## Migrations

- Alembic is the source of truth for schema changes
- Never edit tables manually in production
- Always commit migrations with the feature that introduced them


## All command cheat sheets
- [`Docker`](Docs/docker-commands.md)
- [`Postgres`](Docs/postgres.md)
- [`Alembic`](Docs/alembic.md)
- [`Redis`](Docs/redis.md)
- [`Test`](Docs/test.md)

## Current Features

### Authentication & Users
- ✅ User creation (email + password)
- ✅ Password hashing (PBKDF2)
- ✅ DB-level uniqueness on users.email
- ⚠️ JWT token authentication (access + refresh) - partial integration
- ⚠️ OTP verification (email) - infrastructure exists, needs endpoint integration

### Vault Management
- ✅ Provision vault (register vault with hardware UUID)
- ⚠️ Get vault status - access control added, may need refinement

### Vault Membership
- ✅ Add vault members (ADMIN, MEMBER, VIEWER roles)
- ✅ Remove vault members
- ✅ List vault members
- ✅ Check vault access permissions

### Vault Unlocking
- ⚠️ Unlock command dispatch via WebSocket - code exists, needs vault device integration
- ⚠️ HMAC-SHA256 signed commands - code exists, needs full integration
- ⚠️ Role-based unlock permissions - logic exists in use case

### Security Features
- ✅ Rate limiting via Redis
- ⚠️ Biometric enrollment (face recognition) - service exists, needs endpoint integration
- ⚠️ Activity logging - domain events exist, needs full implementation

### Quality Assurance
- ✅ API & application tests
- ✅ In-memory repositories for fast testing

## Future Features
- ❌ WebSocket vault command streaming
- ❌ Push notifications
- ❌ Refresh token store integration

## Development Notes

- This repo favors small vertical slices
- Infrastructure & DX changes are kept separate from business features
- All changes should be:
  - migration-safe
  - test-covered
  - reversible (where applicable)

## Environment Variables

Loaded via `.env` (see `.env.example` when added):

```bash
DATABASE_URL=postgresql+psycopg://...
REDIS_URL=redis://redis:6379/0
```
---

## License

MIT License - See [LICENSE](LICENSE) file.
