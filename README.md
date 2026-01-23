# SmartVault API

**Purpose**: Transform a working prototype into a stable, secure, evolvable system.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn app.main:app --reload

# Access API at http://localhost:8000
```

---

## Current Features (MVP)

**Endpoints**:
- `GET /api/v1/health` - Service health check
- `GET /api/v1/vaults/{vault_id}/status` - Vault status
- `POST /api/v1/vaults/provision` - Vault provisioning

**Architecture**:
- Clean Architecture (domain, application, infrastructure layers)
- Versioned REST API (`/api/v1`)
- In-memory repositories (fast iteration)
- CI-protected workflow

---

## Project Structure

```
app/
├── main.py                  # FastAPI entry point
├── api/                     # HTTP request handling
│   ├── deps.py              # Dependency injection
│   ├── router.py            # Routing logic
│   └── v1/                  # API endpoints (auth, users, vaults, etc.)
├── domain/                  # Business entities and logic
│   ├── models/              # Core entities (user, vault, access_log)
│   ├── value_objects/       # Immutable values (vault_status, biometric_result)
│   └── events/              # Domain events
├── application/             # Use cases and services
│   ├── use_cases/           # Business workflows
│   └── services/            # Shared utilities (tokens, auth, liveness)
├── infrastructure/          # External integrations
│   ├── db/                  # Database (sessions, repositories, ORM)
│   ├── cache/               # Redis caching
│   ├── messaging/           # WebSocket, event bus
│   ├── notifications/       # Push notifications
│   ├── security/            # Password hashing, rate limiting
│   └── biometrics/          # Face recognition
├── schemas/                 # Pydantic validation models
├── websocket/               # WebSocket handlers
├── core/                    # Config, settings, logging
├── tests/                   # Test suites (api, application, domain)
└── alembic/                 # Database migrations
```

---

## Planned Features

- PostgreSQL persistence
- Vault heartbeat tracking
- WebSocket device connections
- Biometric verification with liveness detection
- PIN-based fallback
- Ownership transfer

---

## Documentation

Detailed component docs: [`app/*/README.md`](app/)

---

## License

MIT License - See [LICENSE](LICENSE) file.