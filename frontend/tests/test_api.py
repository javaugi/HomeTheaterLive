# test_api.py
import asyncio
import httpx

async def test_login():
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Check if server is reachable
            print("Testing server connection...")
            response = await client.get("http://localhost:8000/")
            print(f"Server response: {response.status_code}")
            print(f"Response text: {response.text[:100]}")
            
            # Test 2: Test login endpoint
            print("\nTesting login endpoint...")
            login_data = {
                "username": "test",
                "password": "test"
            }
            
            # Try both JSON and form data
            print("Trying with JSON...")
            json_response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json=login_data
            )
            print(f"JSON response status: {json_response.status_code}")
            print(f"JSON response: {json_response.text[:200]}")
            
            print("\nTrying with form data...")
            form_response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                data=login_data
            )
            print(f"Form response status: {form_response.status_code}")
            print(f"Form response: {form_response.text[:200]}")
            
            # Try to parse as JSON
            try:
                data = form_response.json()
                print(f"Parsed JSON: {data}")
            except Exception as e:
                print(f"Failed to parse JSON: {e}")
                
        except httpx.RequestError as e:
            print(f"Connection error: {e}")
            print("Make sure your FastAPI server is running on http://localhost:8000")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())