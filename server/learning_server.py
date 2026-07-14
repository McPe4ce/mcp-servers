from fastmcp import FastMCP
import json

mcp = FastMCP("Python Decorators")

@mcp.tool
def search_topics(query: str) -> list[dict]:
    """Search programming topics by title or keyword."""
    with open("data/topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)

    if query.lower() in topics["title"].lower() or query.lower() in topics["summary"].lower():
        return [topics]
    return []