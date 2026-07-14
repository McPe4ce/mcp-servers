from fastmcp import FastMCP
import json

mcp = FastMCP("Python Decorators")

@mcp.tool
def search_topics(query: str) -> list[dict]:
    """Search programming topics by title or keyword."""
    with open("data/topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)

    q = query.lower()
    results = []
    for topic in topics:
        if q in topic["title"].lower() or q in topic["summary"].lower():
            results.append(topic)
    return results


@mcp.tool
def get_topic_details(topic_id: str) -> dict:
    """Return full information for a topic by id."""
    with open("data/topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)

    for topic in topics:
        if topic["id"] == topic_id:
            return topic
    return {"error": f"No topic found with id '{topic_id}'"}


@mcp.resource("topics://catalog")
def get_topic_catalog() -> str:
    """Return the list of available topic ids and titles."""
    with open("data/topics.json", "r", encoding="utf-8") as f:
        topics = json.load(f)
    
    catalogue = []
    for query in topics:
        catalogue.append({"id":query["id"], "title": query["title"]})
    return json.dumps(catalogue, indent=2)