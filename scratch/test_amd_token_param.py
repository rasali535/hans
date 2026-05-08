import httpx
import asyncio

async def test():
    token = "DiPipPSZoxb96rcrP7X+B0N5mTTEzxU/ziesgI/Z2NPo9xPKM"
    
    urls = [
        f"http://165.245.137.80/proxy/8000/v1/models?token={token}",
        f"http://165.245.137.80/proxy/8001/v1/models?token={token}",
        f"http://165.245.137.80/v1/models?token={token}",
    ]
    
    for url in urls:
        print(f"Testing {url}...")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  SUCCESS!")
                    print(f"  Data: {resp.text[:200]}")
                else:
                    print(f"  Body: {resp.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test())
