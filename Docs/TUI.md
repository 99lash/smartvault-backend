# SmartVault Admin TUI

The **SmartVault Admin Console** is a terminal-based user interface (TUI) for managing internal operations, monitoring system health, and handling security events. It communicates with the SmartVault backend via the Internal Ops API.

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running the Application](#running-the-application)
4. [Navigation & Keybindings](#navigation--keybindings)
5. [Screens Overview](#screens-overview)
6. [Troubleshooting](#troubleshooting)

---

## Installation

The TUI is included in the `smartvault-backend-dev` repository. Ensure you have the dependencies installed:

```bash
# Install development dependencies (includes TUI requirements)
pip install -r requirements.txt
```

**Requirements:**
- Python 3.10+
- `textual`
- `httpx`
- `tenacity`

---

## Configuration

The TUI is configured via environment variables. Create a `.env` file or set them in your shell:

| Variable | Description | Default |
|----------|-------------|---------|
| `SMARTVAULT_API_URL` | Base URL of the backend API | `http://localhost:8000/api` |
| `ADMIN_API_TOKEN` | Secret token for Admin authentication | *Required* |
| `DASHBOARD_REFRESH_INTERVAL` | Dashboard auto-refresh rate (seconds) | `5` |
| `DIAGNOSTICS_REFRESH_INTERVAL` | Diagnostics auto-refresh rate (seconds) | `10` |

**Security Note:** The `ADMIN_API_TOKEN` must match the token configured in the backend (e.g., `INTERNAL_API_KEY` or similar mechanism).

---

## Running the Application

To launch the Admin Console:

```bash
python -m smartvault_admin_tui.app
```

Or using the Textual CLI (for development mode with live reload):

```bash
textual run smartvault_admin_tui/app.py
```

---

## Navigation & Keybindings

The application supports keyboard-first navigation.

**Global Keybindings:**

| Key | Action |
|-----|--------|
| `Ctrl+D` | Go to **Dashboard** |
| `Ctrl+S` | Go to **Security** Alerts |
| `Ctrl+A` | Go to **Activity** Logs |
| `Ctrl+N` | Go to **Notifications** Status |
| `Ctrl+K` | Manage **API Keys** |
| `Ctrl+R` | Manage **Sessions** |
| `Ctrl+X` | View **Diagnostics** |
| `Ctrl+U` | View **Audit** Logs |
| `Ctrl+Q` | **Quit** Application |
| `?` | Show **Help** Overlay |

**Common Screen Actions:**

| Key | Action |
|-----|--------|
| `R` | Refresh current data |
| `Esc` | Go Back / Unfocus |

---

## Screens Overview

### 1. Dashboard (`Ctrl+D`)
The landing page displaying high-level metrics:
- **System Status**: Global health indicator.
- **Business Metrics**: Total users, active vaults, locked vaults.
- **Recent Activity**: Stream of latest system events.
- **Security Alerts**: Summary of active threats.

### 2. Notifications (`Ctrl+N`)
**Monitor the Email Notification Service.**
- **Status**: Operational status of the SMTP service.
- **Metrics**: Count of emails sent vs. failed today.
- **Last Checked**: Timestamp of the last health check.

### 3. Security (`Ctrl+S`)
Review and resolve security alerts.
- List of flagged suspicious activities (e.g., multiple failed logins).
- Ability to dismiss or investigate alerts.

### 4. Activity (`Ctrl+A`)
Real-time log of user actions (login, vault creation, unlocking).

### 5. Diagnostics (`Ctrl+X`)
Low-level system health checks:
- Database connectivity and latency.
- Redis cache status.
- API response times.

---

## Troubleshooting

**Connection Refused:**
- Ensure the backend API is running (`docker compose up`).
- Verify `SMARTVAULT_API_URL` points to the correct host/port.

**Authentication Failed:**
- Verify `ADMIN_API_TOKEN` matches the backend configuration.
- Check if the token has expired or been revoked.

**UI Rendering Issues:**
- Ensure your terminal supports true color (set `COLORTERM=truecolor`).
- Resize the terminal window if components overlap.
