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


@mcp.tool
def get_topic_details(topic_id: str) -> dict:
    """Return full information for a topic by id."""
    with open("data/topics.json", "r", encoding="utf-8") as f:
        topic = json.load(f)

    if topic_id == topic["id"]:
        return topic
    return {"error": f"No topic found with id '{topic_id}'"}