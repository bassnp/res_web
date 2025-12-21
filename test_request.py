import httpx
import asyncio
import json

async def main():
    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST", 
            "http://localhost:8000/api/fit-check/stream",
            json={"query": "Google", "include_thoughts": True}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    print(line)

if __name__ == "__main__":
    asyncio.run(main())
