import asyncio
import logging
import sys
from smartvault_admin_tui.api.client import APIClient
from smartvault_admin_tui.config import config
from dotenv import load_dotenv

load_dotenv()

# Ensure we can import from project root
sys.path.append(".")

logging.basicConfig(level=logging.INFO)

async def debug():
    print(f"Connecting to {config.api_base_url}")
    client = APIClient()
    try:
        print("Creating key 'debug-test'...")
        resp = await client.create_api_key("debug-test", 1)
        print(f"RESPONSE TYPE: {type(resp)}")
        print(f"RESPONSE CONTENT: {resp}")
        
        if "key" in resp:
            print(f"KEY FOUND: {resp['key']}")
        else:
            print("KEY MISSING FROM RESPONSE!")
            
        # Revoke
        key_id = resp.get("id")
        if key_id:
            print(f"Revoking key {key_id}...")
            await client.revoke_api_key(key_id)
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(debug())
