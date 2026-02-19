# Ngrok Setup Guide

Expose your local SmartVault API to the internet using [ngrok](https://ngrok.com). This is useful for mobile app testing, webhook development, and sharing your dev environment with teammates.

---

## Table of Contents

1. [When to Use Ngrok](#when-to-use-ngrok)
2. [Installation](#installation)
3. [Authentication](#authentication)
4. [Running the Tunnel](#running-the-tunnel)
5. [CORS Configuration](#cors-configuration)
6. [Frontend Configuration](#frontend-configuration)
7. [Using with Simulation Scripts](#using-with-simulation-scripts)
8. [Ngrok Web Inspector](#ngrok-web-inspector)
9. [Troubleshooting](#troubleshooting)

---

## When to Use Ngrok

| Scenario | Why Ngrok Helps |
|----------|----------------|
| **Mobile app testing** | The mobile app can reach your local API over the internet |
| **Webhook development** | External services (e.g., Stripe, SendGrid) can POST to your local API |
| **Team demos** | Share a public URL so teammates can hit your running backend |
| **Frontend on another machine** | Point a remote frontend at your local API |

> **Note:** Ngrok free tier assigns a random URL on each restart. For a stable URL, upgrade to a paid plan or use a custom domain.

---

## Installation

### Linux / WSL2

```bash
# Download and install to ~/bin
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok-v3-stable-linux-amd64.tgz \
  | tar xz -C ~/bin

# Verify
~/bin/ngrok version
```

### macOS (Homebrew)

```bash
brew install ngrok/ngrok/ngrok
ngrok version
```

### Windows

Download the installer from [ngrok.com/download](https://ngrok.com/download) or use:

```powershell
choco install ngrok
ngrok version
```

---

## Authentication

1. Create a free account at [dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup).
2. Copy your auth token from [dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken).
3. Configure ngrok:

```bash
~/bin/ngrok config add-authtoken YOUR_AUTH_TOKEN
```

This saves the token to `~/.config/ngrok/ngrok.yml` (Linux/Mac) or `%APPDATA%\ngrok\ngrok.yml` (Windows).

---

## Running the Tunnel

### Prerequisites

Make sure the backend is running first:

```bash
cd smartvault-backend
make dev    # or: make up
```

Verify the API responds locally:

```bash
curl http://localhost:8000/api/v1/health
```

### Start the Tunnel

```bash
~/bin/ngrok http 8000
```

You'll see output like:

```
Session Status      online
Account             your-email (Plan: Free)
Forwarding          https://abc123-random.ngrok-free.dev -> http://localhost:8000

Web Interface       http://127.0.0.1:4040
```

The `https://...ngrok-free.dev` URL is your public API endpoint. Use it anywhere you'd use `http://localhost:8000`.

### Quick Test

```bash
curl https://YOUR-URL.ngrok-free.dev/api/v1/health \
  -H "ngrok-skip-browser-warning: true"
```

> **Important:** Free tier ngrok shows a browser warning page for non-API requests. Include the `ngrok-skip-browser-warning: true` header in programmatic requests to bypass it.

---

## CORS Configuration

If you're accessing the API from a frontend running on a different origin (e.g., `http://localhost:5173`), CORS is already configured. But if the **frontend itself** is served from a different URL, you need to add the ngrok URL to `CORS_ORIGINS`.

Edit `smartvault-backend/.env`:

```bash
# Add the ngrok URL (no trailing slash)
CORS_ORIGINS=["http://localhost:3001","https://YOUR-URL.ngrok-free.dev"]
```

Then restart the API to pick up the change:

```bash
make down && make up
```

---

## Frontend Configuration

To point the admin web app at your ngrok-exposed API:

Edit `smrtvlt-web-app/.env`:

```bash
VITE_API_BASE_URL=https://YOUR-URL.ngrok-free.dev
```

Then restart the frontend dev server:

```bash
cd smrtvlt-web-app
npm run dev
```

> **Reminder:** Do **not** append `/api` to the URL — the frontend code already prepends `/api` to all request paths.

---

## Using with Simulation Scripts

The simulation scripts default to `localhost:8000`. Pass the ngrok URL as the base when testing remotely.

### Admin Endpoint Tester

```bash
API_BASE_URL=https://YOUR-URL.ngrok-free.dev bash test_admin_endpoints.sh
```

### Wrong PIN Simulator

```bash
API_BASE_URL=https://YOUR-URL.ngrok-free.dev bash simulate_wrong_pins.sh 5
```

### WebSocket Simulator

The WebSocket simulator connects to `ws://localhost:8000` by default. To test through ngrok, edit `BASE_URL` at the top of `simulate_websockets.py`:

```python
BASE_URL = "wss://YOUR-URL.ngrok-free.dev"
```

Then run:

```bash
python3 simulate_websockets.py 3
```

> **Note:** Ngrok supports WebSocket connections automatically — `ws://` upgrades to `wss://` through the tunnel.

---

## Ngrok Web Inspector

While ngrok is running, open [http://127.0.0.1:4040](http://127.0.0.1:4040) in your browser to access the **web inspector**. It shows:

- **All HTTP requests** passing through the tunnel (method, path, status, timing)
- **Request/response bodies** — great for debugging API calls
- **Replay** — resend any request with one click

This is especially useful for debugging mobile app requests or webhook payloads.

---

## Troubleshooting

### Browser shows "Visit Site" warning page

Ngrok free tier displays an interstitial page for browser requests. Solutions:

- **Programmatic requests:** Add header `ngrok-skip-browser-warning: true`
- **Browser access:** Click "Visit Site" to proceed
- **Paid plan:** Upgrade to remove the warning entirely

### URL changed after restart

Free tier URLs are randomly generated on each start. After restarting ngrok:

1. Copy the new URL from the terminal output
2. Update `CORS_ORIGINS` in `smartvault-backend/.env`
3. Update `VITE_API_BASE_URL` in `smrtvlt-web-app/.env`
4. Restart the API (`make down && make up`) and frontend (`npm run dev`)

### Connection refused

```
failed to complete tunnel connection — dial tcp 127.0.0.1:8000: connection refused
```

The backend isn't running. Start it with `make dev` or `make up`.

### 502 Bad Gateway

The API is starting up or crashed. Check the logs:

```bash
make logs
```

### WebSocket connections drop

Ngrok free tier has a connection time limit. If WebSocket connections drop after ~2 hours, reconnect or upgrade to a paid plan.

### Rate limits (free tier)

Free accounts have limits on connections per minute. If you see `ERR_NGROK_108`, wait a moment and try again, or upgrade your plan.

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start tunnel | `~/bin/ngrok http 8000` |
| View traffic | Open `http://127.0.0.1:4040` |
| Test health | `curl https://URL.ngrok-free.dev/api/v1/health -H "ngrok-skip-browser-warning: true"` |
| Stop tunnel | `Ctrl+C` in the ngrok terminal |
| Check version | `~/bin/ngrok version` |

---

## Related Documentation

- [Development Guide](DEVELOPMENT.md) — local dev setup
- [Deployment Guide](DEPLOYMENT.md) — production deployment
- [Troubleshooting](TROUBLESHOOTING.md) — general troubleshooting
