# SMRTVLT API

Backend API for SMRTVLT, built with FastAPI, PostgreSQL, Redis, and Docker. Designed using clean architecture (domain → application → infrastructure → API) with migration-driven schema management.

## Tech Stack

- **API:** FastAPI
- **Database:** PostgreSQL 16
- **Cache / OTP / Rate-limit:** Redis 7
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Auth:** Password hashing (PBKDF2), OTP (planned)
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
Cheat sheet available in [`docker-commands.md`](docker-commands.md)

### API / Docker

```bash
make up        # build & start services
make logs      # tail API logs
make stop      # stop services
make down      # remove containers
make test      # run pytest
```

### Database (Postgres + Alembic)
Cheat sheet available in [`/app/infrastructure/README.md`](/app/infrastructure/README.md)

```bash
make migrate               # apply migrations
make migration msg="..."   # create new migration
make rollback              # downgrade last migration
make psql                  # open psql shell
make db-reset              # DEV ONLY: reset DB
```

### Cache (Redis)
Cheat sheet available in [`/app/infrastructure/README.md`](/app/infrastructure/README.md)

```bash
make redis         # open Redis CLI
make redis-info    # Redis server info
make redis-flush   # DEV ONLY: flush Redis DB
```

## Migrations

- Alembic is the source of truth for schema changes
- Never edit tables manually in production
- Always commit migrations with the feature that introduced them

Cheat sheet available in [`/app/alembic/README.md`](/app/alembic/README.md)

## Current Features

- ✅ User creation (email + password)
- ✅ Password hashing (PBKDF2)
- ✅ DB-level uniqueness on users.email
- ✅ API & application tests
- 🔜 SMTP OTP email verification
- 🔜 Rate limiting via Redis

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

---

## License

MIT License - See [LICENSE](LICENSE) file.