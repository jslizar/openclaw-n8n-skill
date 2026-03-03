# n8n MCP Integration Reference

Complete guide to using MCP (Model Context Protocol) with n8n — both as a tool consumer and tool provider.

---

## Two MCP Approaches in n8n

| Approach | Node | Purpose |
|----------|------|---------|
| **Instance-level MCP** | Settings → MCP | Expose entire workflows as tools to external AI agents |
| **MCP Server Trigger** | MCP Server Trigger node | Expose specific tools from ONE workflow |
| **MCP Client Tool** | MCP Client Tool node | Connect n8n AI agents to external MCP servers |

---

## 1. Exposing n8n Workflows via Instance-Level MCP

Enable at: **Settings → Instance-level MCP → Enable MCP access**

### Requirements for Exposed Workflows
- Must have a supported trigger (Webhook, Form, Chat, Manual, Schedule)
- Must be published (not draft)
- Must be explicitly enabled per-workflow
- 5-minute execution timeout (overrides workflow settings)
- Only first trigger is usable if multiple exist

### Setup Steps
```
1. Settings → Instance-level MCP → Enable toggle (requires admin)
2. Enable each workflow: Workflow menu → "Available in MCP" toggle
3. Add descriptions to help MCP clients understand the workflow
4. Copy connection URL (SSE endpoint)
5. Configure MCP client with URL + auth (Bearer token or API key)
```

### Authentication Options
- **Bearer Token**: Standard OAuth-style token
- **API Key**: n8n API key as header

### Client Configuration (Claude Desktop example)
```json
{
  "mcpServers": {
    "my-n8n": {
      "command": "npx",
      "args": ["mcp-remote", "https://n8n.example.com/mcp/sse"],
      "env": {
        "HEADERS": "Authorization: Bearer YOUR_TOKEN"
      }
    }
  }
}
```

Note: Claude Desktop uses stdio transport. n8n uses SSE. Use `mcp-remote` proxy to bridge them.

---

## 2. MCP Server Trigger Node (Per-Workflow)

Exposes tools from a single workflow to external MCP clients.

### Node JSON
```json
{
  "id": "mcp-trigger-1",
  "name": "MCP Server",
  "type": "@n8n/n8n-nodes-langchain.mcpTrigger",
  "typeVersion": 1,
  "position": [250, 300],
  "parameters": {},
  "webhookId": "UNIQUE_ID"
}
```

### How It Works
- Does NOT pass output to next node like normal triggers
- Instead, connects to **tool nodes** which clients can discover and call individually
- Each connected tool becomes a callable MCP tool

### Connecting Tools to MCP Server
```json
{
  "MCP Server": {
    "ai_tool": [
      [
        {"node": "HTTP Tool", "type": "ai_tool", "index": 0},
        {"node": "Code Tool", "type": "ai_tool", "index": 0},
        {"node": "Sub-Workflow Tool", "type": "ai_tool", "index": 0}
      ]
    ]
  }
}
```

### Compatible Tool Nodes
- `@n8n/n8n-nodes-langchain.toolHttpRequest` — HTTP API calls
- `@n8n/n8n-nodes-langchain.toolCode` — Custom JavaScript
- `@n8n/n8n-nodes-langchain.toolWorkflow` — Execute sub-workflows
- `@n8n/n8n-nodes-langchain.toolCalculator` — Math operations
- `@n8n/n8n-nodes-langchain.toolWikipedia` — Wikipedia lookup
- `@n8n/n8n-nodes-langchain.toolSerpApi` — Web search

### Complete MCP Server Workflow Pattern
```json
{
  "name": "MCP Tool Server",
  "nodes": [
    {
      "id": "mcp-1",
      "name": "MCP Server",
      "type": "@n8n/n8n-nodes-langchain.mcpTrigger",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {},
      "webhookId": "mcp-webhook-001"
    },
    {
      "id": "tool-1",
      "name": "Search API",
      "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
      "typeVersion": 1.1,
      "position": [500, 200],
      "parameters": {
        "url": "https://api.example.com/search",
        "method": "GET",
        "description": "Search for records by keyword. Input: {query: string}",
        "placeholderDefinitions": {
          "values": [
            {"name": "query", "description": "Search keyword", "type": "string"}
          ]
        }
      }
    },
    {
      "id": "tool-2",
      "name": "Create Record",
      "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
      "typeVersion": 1.1,
      "position": [500, 400],
      "parameters": {
        "url": "https://api.example.com/records",
        "method": "POST",
        "description": "Create a new record. Input: {name: string, email: string}",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($fromAI('body', 'JSON object with name and email', 'object')) }}"
      }
    }
  ],
  "connections": {
    "MCP Server": {
      "ai_tool": [
        [
          {"node": "Search API", "type": "ai_tool", "index": 0},
          {"node": "Create Record", "type": "ai_tool", "index": 0}
        ]
      ]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```

---

## 3. MCP Client Tool Node (Consuming External MCP)

Connects n8n AI agents to external MCP servers.

### Node JSON
```json
{
  "id": "mcp-client-1",
  "name": "External MCP",
  "type": "@n8n/n8n-nodes-langchain.mcpClientTool",
  "typeVersion": 1,
  "position": [500, 450],
  "parameters": {
    "sseEndpoint": "https://external-mcp-server.com/sse"
  }
}
```

### Connection to AI Agent
```json
{
  "External MCP": {
    "ai_tool": [
      [{"node": "AI Agent", "type": "ai_tool", "index": 0}]
    ]
  }
}
```

### Known Issue: JSON Schema Conversion Bug
n8n's `convertJsonSchemaToZod` can silently fail on complex schemas, producing `z.any()` 
which makes the AI Agent think any input is valid while the MCP server rejects it.

**Workaround**: Keep MCP tool input schemas simple — avoid deeply nested objects, `$ref`, 
or `oneOf`/`anyOf` patterns. Prefer flat parameter objects.

---

## 4. External MCP Tools for Managing n8n

### czlonkowski/n8n-mcp (Recommended)
The gold-standard external MCP server for AI-assisted n8n workflow building.

**Key tools:**
| Tool | Purpose |
|------|---------|
| `search_nodes` | Find nodes by name/category |
| `get_node` | Get essential properties for a node |
| `validate_workflow` | Validate workflow JSON |
| `validate_ai_workflow` | AI-specific validation |
| `search_templates` | Search 2,600+ community templates |

**Install:**
```bash
npx @anthropic/create-mcp -s czlonkowski/n8n-mcp
```

**CRITICAL PREFIX NOTE**: This MCP uses SHORT prefixes:
| MCP Tool Context | Workflow JSON Context |
|-----------------|----------------------|
| `nodes-base.slack` | `n8n-nodes-base.slack` |
| `nodes-langchain.agent` | `@n8n/n8n-nodes-langchain.agent` |

Always convert when moving between MCP results and workflow JSON!

### n8n-mcp.com (Hosted)
Commercial hosted MCP server with additional capabilities:
- `n8n_create_workflow` — Create workflows directly
- `n8n_update_partial_workflow` — 17 operation types for surgical edits
- `n8n_validate_workflow` — Comprehensive validation + auto-fix
- `n8n_test_workflow` — Trigger and test workflows
- `n8n_executions` — Execution management

### Partial Update Operations
```javascript
// Available operations for n8n_update_partial_workflow:
{
  "id": "workflow-id",
  "intent": "Description of changes",
  "operations": [
    {"type": "addNode", "node": {...}},
    {"type": "removeNode", "nodeName": "Old Node"},
    {"type": "updateNode", "nodeName": "HTTP Request", "updates": {"parameters.url": "https://new.api"}},
    {"type": "addConnection", "source": "Node A", "target": "Node B"},
    {"type": "addConnection", "source": "Model", "target": "Agent", "sourceOutput": "ai_languageModel"},
    {"type": "removeConnection", "source": "Node A", "target": "Node B"},
    {"type": "updateName", "name": "New Workflow Name"},
    {"type": "activateWorkflow"},
    {"type": "deactivateWorkflow"}
  ]
}
```

---

## 5. Multi-Agent Patterns with MCP

### Sequential Agents (Pipeline)
```
Agent A → completes task → passes results → Agent B → Agent C
```
Use case: Data validation → Analysis → Report generation

### Parallel Agents
```
        ┌→ Agent A (sentiment) ─┐
Input ──┤                        ├→ Merge → Output
        └→ Agent B (entities)  ──┘
```
Use case: Parallel analysis of same data

### Hierarchical (Router)
```
Input → Gatekeeper Agent ──┬→ Specialist A
                           ├→ Specialist B
                           └→ Handle directly (simple cases)
```
Use case: Customer support routing by complexity

### MCP Hub-and-Spoke
```
                    ┌→ MCP Server: GitHub
AI Agent ──MCP──→   ├→ MCP Server: Slack
                    ├→ MCP Server: Database
                    └→ MCP Server: n8n (meta!)
```

### Workflow JSON for Hierarchical Agent Pattern
```json
{
  "name": "Agent Router",
  "nodes": [
    {
      "id": "t1",
      "name": "Chat Trigger",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "typeVersion": 1.1,
      "position": [250, 300],
      "parameters": {"options": {}},
      "webhookId": "chat-001"
    },
    {
      "id": "a1",
      "name": "Router Agent",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 1.7,
      "position": [500, 300],
      "parameters": {
        "options": {
          "systemMessage": "You are a routing agent. Analyze the user's request and use the appropriate specialist tool. Use 'research' for information gathering, 'action' for taking actions, and respond directly for simple questions."
        }
      }
    },
    {
      "id": "m1",
      "name": "Router Model",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1.2,
      "position": [400, 500],
      "parameters": {"model": "gpt-4o-mini", "options": {"temperature": 0}},
      "credentials": {"openAiApi": {"id": "CREDENTIAL_ID", "name": "OpenAI"}}
    },
    {
      "id": "st1",
      "name": "Research Specialist",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 2,
      "position": [600, 450],
      "parameters": {
        "name": "research",
        "description": "Use for any information gathering, research, or data retrieval tasks",
        "source": "database",
        "workflowId": "RESEARCH_WORKFLOW_ID"
      }
    },
    {
      "id": "st2",
      "name": "Action Specialist",
      "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
      "typeVersion": 2,
      "position": [750, 450],
      "parameters": {
        "name": "action",
        "description": "Use for executing actions like sending emails, creating records, updating databases",
        "source": "database",
        "workflowId": "ACTION_WORKFLOW_ID"
      }
    },
    {
      "id": "th1",
      "name": "Think",
      "type": "@n8n/n8n-nodes-langchain.toolThink",
      "typeVersion": 1,
      "position": [500, 450],
      "parameters": {}
    }
  ],
  "connections": {
    "Chat Trigger": {
      "main": [[{"node": "Router Agent", "type": "main", "index": 0}]]
    },
    "Router Model": {
      "ai_languageModel": [[{"node": "Router Agent", "type": "ai_languageModel", "index": 0}]]
    },
    "Research Specialist": {
      "ai_tool": [[{"node": "Router Agent", "type": "ai_tool", "index": 0}]]
    },
    "Action Specialist": {
      "ai_tool": [[{"node": "Router Agent", "type": "ai_tool", "index": 0}]]
    },
    "Think": {
      "ai_tool": [[{"node": "Router Agent", "type": "ai_tool", "index": 0}]]
    }
  },
  "settings": {"executionOrder": "v1"}
}
```

---

## 6. MCP Best Practices

### Tool Design
- Keep tool descriptions clear and specific — the AI reads them to decide when to use each tool
- Use simple, flat input schemas (avoid nested objects)
- Add the Think tool to give agents a scratchpad for reasoning
- Limit to 5-10 tools per agent to avoid confusion

### Performance
- MCP uses SSE (Server-Sent Events) for persistent connections
- n8n enforces 5-minute timeout for MCP-triggered executions
- Rate-limit considerations apply to both MCP server and client sides

### Security
- Configure Bearer or Header authentication on MCP Server Trigger
- Never expose MCP servers without authentication
- Audit which workflows are exposed via instance-level MCP
- MCP access is not scoped per-client — all connected clients see all enabled workflows

### Debugging
- Test MCP tools independently before connecting them
- Check n8n execution logs for MCP-triggered runs
- Use the execution history to inspect tool call inputs/outputs
- Common issue: client sends wrong parameters → check tool description clarity
