#!/usr/bin/python3

import asyncio
import os
import openai
import sys
from pathlib import Path
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams


MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/mcp")
APP_NAME = "mcp_servers"
USER_ID = "student"

mcp_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,

    ),
    tool_filter=[
        "search_topics",
        "get_topic_details",
    ],
)

if len(sys.argv) > 1:
    topic = sys.argv[1]
else:
    raise ValueError("Topic cant be empty")

explainer_agent = Agent (
    name ="explainer_agent",
    model="ollama_chat/gemma4",
    description="You are a programming study assistant.",
    instruction="When the user asks about a topic, first use the MCP tools to search for a matching topic and retrieve its details."
                "Use the returned MCP data to answer. Include prerequisites, key concepts, common mistakes, and one practice idea when available."
                "Do not invent topic details that were not provided by the MCP server."
                "If no topic matches, explain that clearly.",
    tools=[mcp_tools],
)

async def run_agent(agent, prompt:str) -> str:
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    if runner is None:
        raise ValueError("Cant run the agent")
    
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )
    if session is None:
        raise ValueError("Session failed to create")
    
    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    collected = ""

    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        collected += part.text
    except openai.APIConnectionError as err:
        raise RuntimeError(
            f"Could not reach the model for agent '{agent.name}'. "
            f"Is Ollama running? Details: {err}"
        ) from err
    
    except openai.APIError as err:
        raise RuntimeError(
            f"The model call failed for agent '{agent.name}': {err}"
        ) from err

    if not collected:
        raise RuntimeError(f"Agent '{agent.name}' returned no text.")
    return collected


def run_explainer_agent(topic: str):
    return run_agent(explainer_agent, topic)


def main():
    answer = asyncio.run(run_explainer_agent(topic))
    print(answer)

    output_path = Path(__file__).resolve().parent.parent / "output" / "sample_agent_response.md"
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(answer, encoding="utf-8")
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()
