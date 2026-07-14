from fastmcp import Client

import asyncio

client = Client("http://localhost:8080/mcp")

async def main():
    async with client:
        result = await client.call_tool("get_topic_details", {"topic_id": "python-decorators"})
        print(result.data)

asyncio.run(main())