from fastmcp import Client

import asyncio

client = Client("http://localhost:8080/mcp")

async def main():
    async with client:
        result = await client.read_resource("topics://catalog")
        print(result[0].text)

asyncio.run(main())