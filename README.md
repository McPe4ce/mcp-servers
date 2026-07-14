# mcp-servers

## Setup

Create a virtual environment and install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> Run every command below with the venv activated (`source venv/bin/activate`).
> If `fastmcp` can't be found, the venv isn't active for that shell.

## Running the server

The server is defined in [server/learning_server.py](server/learning_server.py)
and is started with the `fastmcp` CLI (the file has no `mcp.run()` block, so
`python server/learning_server.py` will not start anything).

**Plain HTTP server** — for clients and agents to connect to:

```bash
fastmcp run server/learning_server.py --transport http --host 127.0.0.1 --port 8080
```

The MCP endpoint is then available at `http://localhost:8080/mcp`.

**Dev preview (for visual `app=True` tools)** — launches a browser UI where you
can call tools by hand and see the rendered Prefab UI:

```bash
fastmcp dev apps server/learning_server.py
```

Open the preview at **http://localhost:8080/** and enter the tool's arguments
(e.g. a `name` for `greet`) to see the card render.

## Running the client

With the server running, call it from Python:

```bash
python3 client/mcp_client.py
```

The client ([client/mcp_client.py](client/mcp_client.py)) connects to the server,
invokes the `greet` tool, and prints the result. UI (`app=True`) tools only
*render* inside a UI-capable host (the dev preview above); a terminal client
receives the view as structured data.

## Testing the server

The server exposes two tools — `search_topics(query)` and
`get_topic_details(topic_id)` — and one resource, `topics://catalog`. There are
three ways to exercise them, from quickest to most realistic.

### 1. Call a tool function directly (no server, no network)

Because `@mcp.tool` leaves the function callable, you can import it and run it.
Fastest way to check the logic:

```bash
venv/bin/python3 -c "from server.learning_server import search_topics; print(search_topics('decorators'))"
venv/bin/python3 -c "from server.learning_server import get_topic_details; print(get_topic_details('python-generators'))"
venv/bin/python3 -c "from server.learning_server import get_topic_catalog; print(get_topic_catalog())"
```

Run these from the repo root so the relative path `data/topics.json` resolves.

### 2. Through an in-memory MCP client (tests it as a real tool, still no port)

Pass the server object straight to a `Client` — no server process needed:

```python
# test_search.py  (in the repo root)
import asyncio
from fastmcp import Client
from server.learning_server import mcp

async def main():
    async with Client(mcp) as client:
        print(await client.call_tool("search_topics", {"query": "decorators"}))
        print(await client.call_tool("get_topic_details", {"topic_id": "python-generators"}))
        print(await client.read_resource("topics://catalog"))

asyncio.run(main())
```

```bash
venv/bin/python3 test_search.py
```

### 3. End-to-end over HTTP (server + client in separate terminals)

Terminal 1 — start the server:

```bash
fastmcp run server/learning_server.py --transport http --host 127.0.0.1 --port 8080
```

Terminal 2 — connect and call it ([client/mcp_client.py](client/mcp_client.py)):

```python
from fastmcp import Client
import asyncio

client = Client("http://localhost:8080/mcp")

async def main():
    async with client:
        # tools are called by name with an args dict
        print(await client.call_tool("search_topics", {"query": "decorators"}))
        print(await client.call_tool("get_topic_details", {"topic_id": "python-generators"}))
        # resources are read by their URI, no arguments
        result = await client.read_resource("topics://catalog")
        print(result[0].text)

asyncio.run(main())
```

Remember: **tools** use `call_tool(name, {args})` and the args keys must match the
parameter names; **resources** use `read_resource(uri)` with no arguments and
return a list of parts (index `result[0].text`).

## MCP Architecture Summary

**What MCP is.**
The Model Context Protocol (MCP) is an open standard that defines how AI
applications connect to external tools and data. It gives a language model a
uniform, structured way to discover what an external system can do and to invoke
it — instead of every integration being hand-wired and one-off. Think of it as a
common "port" that any model-powered application can plug capabilities into.

**What an MCP host does.**
The host is the AI application the user actually interacts with — for example a
chat app, an IDE assistant, or the agent in [client/agent.py](client/agent.py).
It owns the conversation and the model, decides when external capabilities are
needed, and manages one or more MCP clients. The host is the trust boundary: it
enforces permissions, mediates what the model is allowed to reach, and stitches
tool results back into the model's context.

**What an MCP client does.**
A client is the connector that lives inside the host and maintains a one-to-one
connection to a single MCP server (see [client/mcp_client.py](client/mcp_client.py)).
It speaks the MCP wire protocol: it handles the initial handshake, asks the
server what it offers (tools, resources, prompts), forwards the host's calls to
the server, and returns the responses. If the host needs to talk to three
servers, it runs three clients.

**What an MCP server does.**
A server exposes a specific set of capabilities to any connecting client — a
database, a filesystem, an API, or the example in
[server/learning_server.py](server/learning_server.py). It advertises what it
can do, validates incoming requests, executes them, and returns structured
results. Servers are independent and reusable: the same server can serve many
different hosts.

**What tools are.**
Tools are actions a server exposes that the model can choose to invoke — they
*do* something with side effects or computation (query a database, send a
request, write a file). Each tool has a name, a description, and a typed input
schema so the model knows how and when to call it. Tools are model-controlled:
the model decides, and the host approves, when to run them.

**What resources are.**
Resources are readable pieces of context a server exposes — files, records, or
other data the model can load into the conversation. Unlike tools, resources are
about *reading* data rather than performing actions, and they are typically
application- or user-controlled: the host or user selects which resources to
pull in, rather than the model triggering side effects.

**Why a server should expose only the capabilities it really needs.**
Every tool and resource a server exposes widens its attack surface and the set
of actions the model can take. Exposing only what is genuinely needed keeps the
model focused (fewer, clearer choices lead to better and more predictable tool
use), reduces the risk of accidental or malicious misuse, makes permissions
easier to reason about and audit, and limits the blast radius if the model or a
request behaves unexpectedly. Least privilege is both a safety and a reliability
principle: don't grant capabilities you can't justify.
