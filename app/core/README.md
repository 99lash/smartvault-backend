# Core Documentation

Quick reference for `app/core` components.

---

## `config.py` - Configuration Management

**Purpose**: Centralizes environment variables and application settings.

**Features**:
- Manages environment-specific configs (dev, test, prod)
- Ensures consistent settings across the application

**Why It Matters**: Single source for configuration, easily adaptable to different environments.

---

## `settings.py` - Application Settings

**Purpose**: Defines application-wide preferences and feature flags.

**Features**:
- Default values and runtime settings
- Feature flag management

**Why It Matters**: Enables dynamic configuration without code changes.

---

## `logging.py` - Logging Configuration

**Purpose**: Centralizes logging setup and utilities.

**Features**:
- Log levels, formats, and handlers
- Structured logging utilities

**Why It Matters**: Consistent, informative logs for debugging and monitoring.