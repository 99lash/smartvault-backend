#!/usr/bin/env python3
"""
SmartVault WebSocket Connection Simulator

Opens N fake user WebSocket connections and subscribes them to vaults,
so the diagnostics page shows live connection data.

Connections stay alive until Ctrl+C.

Usage:
    python simulate_websockets.py          # 3 connections (default)
    python simulate_websockets.py 5        # 5 connections
    python simulate_websockets.py 10       # 10 connections

Requires: backend running (make up), websockets library (pip install websockets)
"""

import asyncio
import json
import signal
import sys

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets")
    sys.exit(1)

BASE_URL = "ws://localhost:8000"
WS_PATH = "/api/v1/ws/user"
NUM_CONNECTIONS = int(sys.argv[1]) if len(sys.argv) > 1 else 3

FAKE_USERS = [
    "sim-user-alpha",
    "sim-user-bravo",
    "sim-user-charlie",
    "sim-user-delta",
    "sim-user-echo",
    "sim-user-foxtrot",
    "sim-user-golf",
    "sim-user-hotel",
    "sim-user-india",
    "sim-user-juliet",
]

GREEN = "\033[0;32m"
CYAN = "\033[0;36m"
YELLOW = "\033[0;33m"
RED = "\033[0;31m"
NC = "\033[0m"


async def connect_user(user_id: str, vault_ids: list[str], index: int):
    """Open a WebSocket connection as a fake user and subscribe to vaults."""
    uri = f"{BASE_URL}{WS_PATH}"
    headers = {"X-Dev-User-Id": user_id}

    try:
        async with websockets.connect(uri, additional_headers=headers) as ws:
            # Read welcome message
            welcome = await ws.recv()
            data = json.loads(welcome)
            print(f"  {GREEN}✓{NC} #{index+1} {CYAN}{user_id}{NC} connected — {data.get('payload', {}).get('message', '')}")

            # Subscribe to vaults
            if vault_ids:
                await ws.send(json.dumps({
                    "type": "SUBSCRIBE",
                    "payload": {"vault_ids": vault_ids}
                }))
                # Read subscription confirmation
                try:
                    sub_response = await asyncio.wait_for(ws.recv(), timeout=3)
                    sub_data = json.loads(sub_response)
                    msg = sub_data.get("payload", {}).get("message", "subscribed")
                    print(f"         subscribed to {len(vault_ids)} vault(s) — {msg}")
                except asyncio.TimeoutError:
                    print(f"         subscribed to {len(vault_ids)} vault(s)")

            # Keep alive — listen for messages until cancelled
            while True:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    print(f"  {YELLOW}←{NC} #{index+1} received: {data.get('type', '?')}")
                except asyncio.TimeoutError:
                    # Send a ping to keep connection alive
                    await ws.ping()

    except websockets.exceptions.ConnectionClosed as e:
        print(f"  {RED}✗{NC} #{index+1} {user_id} disconnected: {e}")
    except ConnectionRefusedError:
        print(f"  {RED}✗{NC} #{index+1} Connection refused — is the backend running?")
    except Exception as e:
        print(f"  {RED}✗{NC} #{index+1} {user_id} error: {e}")


async def get_vault_ids() -> list[str]:
    """Fetch vault IDs from the admin API."""
    try:
        import urllib.request
        admin_token = "sk_TBn8_PzP-CD9BIODfdILDRQqIy_yGAb6kfbvHeanG2g"
        req = urllib.request.Request(
            "http://localhost:8000/api/internal/business/overview",
            headers={"X-Admin-Token": admin_token}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            vaults = data.get("vaults", {})
            # Try to get IDs from the overview, fall back to empty
            vault_ids = vaults.get("vault_ids", [])
            if vault_ids:
                return vault_ids
    except Exception:
        pass

    # Fallback: use the ops summary or just return empty
    # The subscription with empty list still counts as a connection
    return []


async def main():
    count = min(NUM_CONNECTIONS, len(FAKE_USERS))
    vault_ids = await get_vault_ids()

    print()
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f" SmartVault WebSocket Simulator")
    print(f" Connections: {count} | URL: {BASE_URL}{WS_PATH}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n{CYAN}→ Opening {count} WebSocket connections...{NC}\n")

    tasks = []
    for i in range(count):
        user_id = FAKE_USERS[i]
        task = asyncio.create_task(connect_user(user_id, vault_ids, i))
        tasks.append(task)
        await asyncio.sleep(0.2)  # stagger connections

    print(f"\n{GREEN}All connections established.{NC}")
    print(f"Check diagnostics: http://localhost:8000/api/internal/ops/diagnostics/websockets")
    print(f"\nPress {YELLOW}Ctrl+C{NC} to disconnect all.\n")

    # Wait until cancelled
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass


def shutdown(loop):
    """Cancel all running tasks on Ctrl+C."""
    for task in asyncio.all_tasks(loop):
        task.cancel()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.add_signal_handler(signal.SIGINT, shutdown, loop)

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        print(f"\n{CYAN}All connections closed.{NC}")
        loop.close()
