# -*- coding: utf-8 -*-
# test_startup.py
import httpx
import asyncio
import jwt
import sqlalchemy
import psycopg
import sys
print("Testing imports...")

sys.stdout.reconfigure(encoding="utf-8")
print("Testing imports done")


try:
    from app.api.endpoints import router
    print(f"✓ Successfully imported videos router {router}")
except Exception as e:
    print(f"✗ Failed to import videos router: {e}")
    import traceback
    traceback.print_exc()

try:
    from app.db.database import Base, engine
    print(f"✓ Successfully imported database modules engine {
          engine} and Base {Base}")
except Exception as e:
    print(f"✗ Failed to import database modules: {e}")
    import traceback
    traceback.print_exc()


def main():
    print("Hello, world! The main function is running.")
    print("Printing emoji: Hello World! \U0001f600")
    print("Printing emoji: Hello World! 🔍 \U0001f50d")

    print(f"psycopg version: {psycopg.__version__}")
    print(f"jwt version: {jwt.__version__}")
    print(f"sqlalchemy version: {sqlalchemy.__version__}")
    print('Sys Paths: \n'.join(sys.path))

    connected: bool = asyncio.run(check_backend_connection())
    print(f"check_backend_connection: {connected}")
    asyncio.run(test_login())


async def check_backend_connection():
    try:
        health_url: str = "http://127.0.0.1:8000/api/v1/health"
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(health_url)
            print(f"\nDEBUG: Health check from url={
                  health_url} with return value={response}")
            print(f"DEBUG: Backend URL: {
                  health_url}, Connectivity Status: ✓ (HTTP {response.status_code})")
            if response.status_code == 200:
                return True
            else:
                return False
    except Exception as e:
        print(f"DEBUG: Backend connectivity: ✗ ({
              type(e).__name__}: {str(e)}) from uri={health_url}")
        return False


async def test_login():
    auth_url: str = "http://127.0.0.1:8000/api/v1/auth/login"
    # data = {"username": username, "password": password}
    data = {
        "username": "test",
        "password": "test",
        "grant_type": "password",
        "scope": "",
        "client_id": "",
        "client_secret": ""
    }
    headers = {
        'User-Agent': 'Image2Video-Mobile/1.0',
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print(f"Mobile_ApiClient Attempting login to: {
          auth_url}, Data: {data}, Headers: {headers}")
    try:
        r = await httpx.AsyncClient().post(auth_url, data=data, headers=headers)
        # Debug: Print response details
        print(f"Status Code: {r.status_code}")
        print(f"Response Headers: {dict(r.headers)}")
        print(f"Response Text (first 500 chars): {r.text[:500]}")

        # Check if response is valid JSON
        if r.status_code == 200:
            return {"success": True, "status_code": f"HTTP {r.status_code}"}
        else:
            print(f"Mobile_ApiClient Error: Received status {r.status_code}")
            # Try to parse as JSON if possible, otherwise use text
            try:
                error_data = r.json()
                print(f"Mobile_ApiClient Error JSON: {error_data}")
            except:
                print(f"Mobile_ApiClient Error Text: {r.text}")
            return {"success": False, "error": f"HTTP {r.status_code}"}

    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    # This block executes when the script is run directly
    main()  # -*- coding: utf-8 -*-
