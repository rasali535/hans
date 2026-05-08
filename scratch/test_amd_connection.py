import httpx
import asyncio
import json

AMD_URL = "http://165.245.137.80"
AMD_TOKEN = "DiPipPSZoxb96rcrP7X+B0N5mTTEzxU/ziesgI/Z2NPo9xPKM"

async def test():
    headers = {"Authorization": f"Bearer {AMD_TOKEN}"}
    
    print(f"Testing connectivity to {AMD_URL}...")
    
    # 1. Test port 80 / proxy
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{AMD_URL}/v1/models", headers=headers)
            print(f"Port 80 /v1/models: {r.status_code}")
            if r.status_code == 200:
                print("SUCCESS: vLLM is alive on Port 80!")
                print(r.json())
                return
    except Exception as e:
        print(f"Port 80 /v1/models failed: {e}")

    # 2. Test /proxy/8000
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{AMD_URL}/proxy/8000/v1/models", headers=headers)
            print(f"Port 80 /proxy/8000/v1/models: {r.status_code}")
            if r.status_code == 200:
                print("SUCCESS: vLLM is alive on /proxy/8000!")
                print(r.json())
                return
    except Exception as e:
        print(f"/proxy/8000 failed: {e}")

    # 3. Test port 8000 directly
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"http://165.245.137.80:8000/v1/models", headers=headers)
            print(f"Port 8000 /v1/models: {r.status_code}")
            if r.status_code == 200:
                print("SUCCESS: vLLM is alive on Port 8000!")
                print(r.json())
                return
    except Exception as e:
        print(f"Port 8000 failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
