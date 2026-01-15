# SmartVault API

## Project Purpose

To turn a working prototype into a stable, secure, and evolvable system by fixing architectural shortcuts that will break under real usage.

## Project Structure

The project follows a modular and layered architecture to ensure separation of concerns, maintainability, and scalability. Below is an overview of the key directories and their responsibilities:

```
app/
├── main.py                  # Entry point for the FastAPI application
├── api/                     # API layer for handling HTTP requests and responses
│   ├── deps.py              # Dependency injection and shared utilities
│   ├── router.py            # Centralized routing logic
│   └── v1/                  # Versioned API endpoints
│       ├── auth.py          # Authentication endpoints
│       ├── users.py         # User management endpoints
│       ├── vaults.py        # Vault management endpoints
│       ├── biometrics.py    # Biometric data endpoints
│       ├── access.py        # Access control endpoints
│       └── activity.py      # Activity logging endpoints
│
├── domain/                  # Domain layer for business logic and models
│   ├── models/              # Domain models representing business entities
│   │   ├── user.py          # User model
│   │   ├── vault.py         # Vault model
│   │   └── access_log.py    # Access log model
│   ├── value_objects/       # Immutable value objects
│   │   ├── vault_status.py  # Vault status value object
│   │   └── biometric_result.py # Biometric result value object
│   └── events/              # Domain events
│       ├── vault_events.py  # Vault-related events
│       └── security_events.py # Security-related events
│
├── application/             # Application layer for use cases and services
│   ├── use_cases/           # Business logic and workflows
│   │   ├── authenticate_user.py # User authentication use case
│   │   ├── provision_vault.py # Vault provisioning use case
│   │   ├── unlock_vault.py   # Vault unlocking use case
│   │   ├── enroll_biometrics.py # Biometric enrollment use case
│   │   └── log_activity.py   # Activity logging use case
│   └── services/            # Reusable services and utilities
│       ├── token_service.py # Token management service
│       ├── authorization_service.py # Authorization service
│       └── liveness_service.py # Liveness monitoring service
│
├── infrastructure/          # Infrastructure layer for external integrations
│   ├── db/                  # Database-related utilities
│   │   ├── session.py       # Database session management
│   │   ├── repositories/    # Data access repositories
│   │   │   ├── user_repository.py # User repository
│   │   │   ├── vault_repository.py # Vault repository
│   │   │   └── access_log_repository.py # Access log repository
│   │   └── models/          # ORM models
│   │       ├── user_orm.py  # User ORM model
│   │       ├── vault_orm.py # Vault ORM model
│   │       └── access_log_orm.py # Access log ORM model
│   ├── cache/               # Caching utilities
│   │   └── redis_client.py  # Redis client
│   ├── messaging/           # Messaging utilities
│   │   ├── websocket_manager.py # WebSocket manager
│   │   └── event_bus.py     # Event bus
│   ├── notifications/       # Notification utilities
│   │   └── push_service.py  # Push notification service
│   ├── security/            # Security utilities
│   │   ├── password_hasher.py # Password hashing
│   │   └── rate_limiter.py  # Rate limiting
│   └── biometrics/          # Biometric utilities
│       └── face_recognition_service.py # Face recognition service
│
├── schemas/                 # Data validation and serialization schemas
│   ├── auth.py              # Authentication schemas
│   ├── users.py             # User schemas
│   ├── vaults.py            # Vault schemas
│   ├── biometrics.py        # Biometric schemas
│   └── activity.py          # Activity schemas
│
├── websocket/               # WebSocket-related utilities
│   └── vault_socket.py      # Vault WebSocket handler
│
├── core/                    # Core utilities and configurations
│   ├── config.py            # Configuration management
│   ├── settings.py          # Application settings
│   └── logging.py           # Logging configuration
│
├── tests/                   # Test suites
│   ├── api/                 # API tests
│   ├── application/         # Application tests
│   └── domain/              # Domain tests
│
└── alembic/                # Database migration scripts
    └── versions/            # Migration versions
```

## Architectural Capabilities

- Modular, layered backend architecture (Clean Architecture inspired)
- Versioned REST API (`/api/v1`)
- In-memory repositories for fast iteration and testing
- CI-protected development workflow
- Explicit separation of domain, application, and infrastructure layers

## Implemented Capabilities (MVP)

The following features are fully implemented, tested, and protected by CI:

### Core
- Service health check

### Vault Management
- Vault provisioning (in-memory MVP)
- Vault status retrieval

## Implemented Endpoints (MVP)

- `GET  /api/v1/health`
- `GET  /api/v1/vaults/{vault_id}/status`
- `POST /api/v1/vaults/provision`

## Planned (Not Yet Implemented)

- Persistent storage (PostgreSQL)
- Vault heartbeat / last-seen updates
- WebSocket device connection
- Biometric verification and liveness checks
- PIN-based local fallback
- Ownership transfer

## Getting Started

To get started with the SmartVault API, follow these steps:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the Application**:
   Update the configuration files in `app/core/` to match your environment settings.

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**:
   The API will be available at `http://localhost:8000`.

## Documentation

For detailed documentation on each component, refer to the README files in the respective directories:

- [`app/api/README.md`](app/api/README.md)
- [`app/domain/README.md`](app/domain/README.md)
- [`app/application/README.md`](app/application/README.md)
- [`app/infrastructure/README.md`](app/infrastructure/README.md)
- [`app/schemas/README.md`](app/schemas/README.md)
- [`app/websocket/README.md`](app/websocket/README.md)
- [`app/core/README.md`](app/core/README.md)
- [`app/tests/README.md`](app/tests/README.md)


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


# SmartVault API

## Project Purpose

To turn a working prototype into a stable, secure, and evolvable system by fixing architectural shortcuts that will break under real usage.

## Project Structure

The project follows a modular and layered architecture to ensure separation of concerns, maintainability, and scalability. Below is an overview of the key directories and their responsibilities:

```
app/
├── main.py                  # Entry point for the FastAPI application
├── api/                     # API layer for handling HTTP requests and responses
│   ├── deps.py              # Dependency injection and shared utilities
│   ├── router.py            # Centralized routing logic
│   └── v1/                  # Versioned API endpoints
│       ├── auth.py          # Authentication endpoints
│       ├── users.py         # User management endpoints
│       ├── vaults.py        # Vault management endpoints
│       ├── biometrics.py    # Biometric data endpoints
│       ├── access.py        # Access control endpoints
│       └── activity.py      # Activity logging endpoints
│
├── domain/                  # Domain layer for business logic and models
│   ├── models/              # Domain models representing business entities
│   │   ├── user.py          # User model
│   │   ├── vault.py         # Vault model
│   │   └── access_log.py    # Access log model
│   ├── value_objects/       # Immutable value objects
│   │   ├── vault_status.py  # Vault status value object
│   │   └── biometric_result.py # Biometric result value object
│   └── events/              # Domain events
│       ├── vault_events.py  # Vault-related events
│       └── security_events.py # Security-related events
│
├── application/             # Application layer for use cases and services
│   ├── use_cases/           # Business logic and workflows
│   │   ├── authenticate_user.py # User authentication use case
│   │   ├── provision_vault.py # Vault provisioning use case
│   │   ├── unlock_vault.py   # Vault unlocking use case
│   │   ├── enroll_biometrics.py # Biometric enrollment use case
│   │   └── log_activity.py   # Activity logging use case
│   └── services/            # Reusable services and utilities
│       ├── token_service.py # Token management service
│       ├── authorization_service.py # Authorization service
│       └── liveness_service.py # Liveness monitoring service
│
├── infrastructure/          # Infrastructure layer for external integrations
│   ├── db/                  # Database-related utilities
│   │   ├── session.py       # Database session management
│   │   ├── repositories/    # Data access repositories
│   │   │   ├── user_repository.py # User repository
│   │   │   ├── vault_repository.py # Vault repository
│   │   │   └── access_log_repository.py # Access log repository
│   │   └── models/          # ORM models
│   │       ├── user_orm.py  # User ORM model
│   │       ├── vault_orm.py # Vault ORM model
│   │       └── access_log_orm.py # Access log ORM model
│   ├── cache/               # Caching utilities
│   │   └── redis_client.py  # Redis client
│   ├── messaging/           # Messaging utilities
│   │   ├── websocket_manager.py # WebSocket manager
│   │   └── event_bus.py     # Event bus
│   ├── notifications/       # Notification utilities
│   │   └── push_service.py  # Push notification service
│   ├── security/            # Security utilities
│   │   ├── password_hasher.py # Password hashing
│   │   └── rate_limiter.py  # Rate limiting
│   └── biometrics/          # Biometric utilities
│       └── face_recognition_service.py # Face recognition service
│
├── schemas/                 # Data validation and serialization schemas
│   ├── auth.py              # Authentication schemas
│   ├── users.py             # User schemas
│   ├── vaults.py            # Vault schemas
│   ├── biometrics.py        # Biometric schemas
│   └── activity.py          # Activity schemas
│
├── websocket/               # WebSocket-related utilities
│   └── vault_socket.py      # Vault WebSocket handler
│
├── core/                    # Core utilities and configurations
│   ├── config.py            # Configuration management
│   ├── settings.py          # Application settings
│   └── logging.py           # Logging configuration
│
├── tests/                   # Test suites
│   ├── api/                 # API tests
│   ├── application/         # Application tests
│   └── domain/              # Domain tests
│
└── alembic/                # Database migration scripts
    └── versions/            # Migration versions
```

## Architectural Capabilities

- Modular, layered backend architecture (Clean Architecture inspired)
- Versioned REST API (`/api/v1`)
- In-memory repositories for fast iteration and testing
- CI-protected development workflow
- Explicit separation of domain, application, and infrastructure layers

## Implemented Capabilities (MVP)

The following features are fully implemented, tested, and protected by CI:

### Core
- Service health check

### Vault Management
- Vault provisioning (in-memory MVP)
- Vault status retrieval

## Implemented Endpoints (MVP)

- `GET  /api/v1/health`
- `GET  /api/v1/vaults/{vault_id}/status`
- `POST /api/v1/vaults/provision`

## Planned (Not Yet Implemented)

- Persistent storage (PostgreSQL)
- Vault heartbeat / last-seen updates
- WebSocket device connection
- Biometric verification and liveness checks
- PIN-based local fallback
- Ownership transfer

## Getting Started

To get started with the SmartVault API, follow these steps:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure the Application**:
   Update the configuration files in `app/core/` to match your environment settings.

3. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Access the API**:
   The API will be available at `http://localhost:8000`.

## Documentation

For detailed documentation on each component, refer to the README files in the respective directories:

- [`app/api/README.md`](app/api/README.md)
- [`app/domain/README.md`](app/domain/README.md)
- [`app/application/README.md`](app/application/README.md)
- [`app/infrastructure/README.md`](app/infrastructure/README.md)
- [`app/schemas/README.md`](app/schemas/README.md)
- [`app/websocket/README.md`](app/websocket/README.md)
- [`app/core/README.md`](app/core/README.md)
- [`app/tests/README.md`](app/tests/README.md)


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.


