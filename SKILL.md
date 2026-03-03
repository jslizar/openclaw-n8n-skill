---
name: n8n-workflow-mastery
description: >
  Comprehensive n8n workflow automation skill for creating, modifying, debugging,
  and executing n8n workflows programmatically via the REST API or MCP tools.
  ALWAYS use this skill when the user mentions n8n, workflow automation, n8n workflows,
  n8n nodes, n8n API, webhook workflows, n8n expressions, n8n Code nodes,
  AI agent workflows in n8n, n8n credentials, n8n triggers, or any task involving
  building/editing/debugging/deploying automation workflows. Also trigger when the user
  asks to "automate", "connect apps", "build a workflow", "set up a trigger",
  "integrate APIs", or references any n8n-specific concepts like nodes, connections,
  executions, or the n8n editor. This skill covers the FULL lifecycle: design → build →
  validate → deploy → monitor → debug.
---

# n8n Workflow Mastery Skill

You are an expert n8n workflow architect. You design, build, validate, deploy, and debug
n8n workflows programmatically. You ALWAYS follow the Build Loop Protocol below.

---

## Reference Files

Read these as needed for deep-dives:
- `references/API_REFERENCE.md` — Full REST API endpoints, auth, pagination, webhooks
- `references/NODE_CATALOG.md` — Complete node types, configs, property dependencies
- `references/PATTERNS_LIBRARY.md` — 20+ copy-paste-ready workflow JSON patterns
- `references/TROUBLESHOOTING.md` — Error recovery playbooks (decision-tree format)
- `references/MCP_INTEGRATION.md` — MCP server/client setup, multi-agent patterns, external tools
- `references/EXPRESSION_COOKBOOK.md` — 80+ copy-paste expressions: dates, strings, arrays, JSON, Slack formatting
- `references/CREDENTIAL_TYPES.md` — Every service's exact credential type string + required fields

## Scripts (in `scripts/` directory)

- `scripts/validate_workflow.py` — Validates workflow JSON. Run BEFORE every deployment.
- `scripts/scaffold_workflow.py` — Generates valid base JSON from a spec. Use to start every workflow.
- `scripts/deploy_workflow.py` — Full pipeline: validate → create → test → activate.

---

## 0. BUILD LOOP PROTOCOL ⚡

**NEVER skip this. EVERY workflow you create or modify follows these steps:**

```
Step 1: SCAFFOLD — Generate base JSON using scaffold_workflow.py or manually
         python scripts/scaffold_workflow.py --name "Name" --trigger webhook --nodes code,slack

Step 2: CUSTOMIZE — Add business logic, expressions, credentials to the scaffold

Step 3: VALIDATE — Run validation BEFORE any API call
         python scripts/validate_workflow.py workflow.json
         Fix ALL errors. Warnings are OK.

Step 4: DEPLOY INACTIVE — Create via API in inactive state
         POST /api/v1/workflows → returns workflow ID

Step 5: TEST — Execute manually or via webhook test URL
         POST /api/v1/workflows/{id}/run  (for manual triggers)
         GET execution logs to verify

Step 6: FIX — If errors found, fix → re-validate → re-deploy
         PUT /api/v1/workflows/{id} with corrected JSON

Step 7: ACTIVATE — Only after successful test
         POST /api/v1/workflows/{id}/activate
```

**Full pipeline in one command:**
```bash
python scripts/deploy_workflow.py --url https://n8n.example.com --api-key KEY workflow.json --activate
```

**For modifications to existing workflows:**
```
1. GET /api/v1/workflows/{id} → download current JSON
2. Modify the JSON
3. VALIDATE (step 3)
4. PUT /api/v1/workflows/{id} → update
5. TEST (step 5)
```

---

## 1. Core Architecture

### How n8n Works

n8n is a node-based workflow automation platform. Every workflow is a directed graph:
```
[Trigger Node] → [Config] → [Processing] → [Action]
                                  ↓
                          [Branch / Conditional]
                          ↙              ↘
                  [Path A]              [Path B]
```

**Key concepts:**
- **Workflows** = JSON objects containing nodes + connections + settings
- **Nodes** = Individual operations (1,000+ types including community)
- **Connections** = Links between nodes defining data flow (by NAME not ID)
- **Executions** = Runtime instances of a workflow
- **Credentials** = Stored authentication for external services

### Data Flow Model

Data flows as **arrays of items**. Each item:
```json
{ "json": { "key": "value" }, "binary": { "data": { ... } } }
```
When a node outputs 5 items, the next node runs 5 times (once per item)
unless configured for batch processing.

### Two Prefixes — NEVER Mix Them

| Context | Prefix | Example |
|---------|--------|---------|
| Workflow JSON (create, update) | `n8n-nodes-base.` | `n8n-nodes-base.slack` |
| Workflow JSON (AI/LangChain) | `@n8n/n8n-nodes-langchain.` | `@n8n/n8n-nodes-langchain.agent` |
| MCP tools (search, validate) | `nodes-base.` | `nodes-base.slack` |
| MCP tools (AI nodes) | `nodes-langchain.` | `nodes-langchain.agent` |

**Getting this wrong is the #1 cause of workflow creation failures.**
The validator script catches these automatically.

---

## 2. n8n REST API Reference

### Authentication
- **API Key**: `X-N8N-API-KEY: <key>` header
- Base URL: `https://<instance>/api/v1`

### Essential Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/workflows` | List all workflows |
| `GET` | `/workflows/:id` | Get workflow by ID |
| `POST` | `/workflows` | Create workflow (inactive) |
| `PUT` | `/workflows/:id` | Full update |
| `DELETE` | `/workflows/:id` | Delete |
| `POST` | `/workflows/:id/activate` | Activate |
| `POST` | `/workflows/:id/deactivate` | Deactivate |
| `POST` | `/workflows/:id/run` | Manual execute |
| `GET` | `/executions` | List executions |
| `GET` | `/executions/:id` | Execution details + logs |
| `GET` | `/credentials` | List credentials |
| `GET` | `/credentials/schema/:type` | Get credential schema |
| `POST` | `/credentials` | Create credential |

### Standard API Call Pattern

```javascript
const response = await fetch('https://n8n.example.com/api/v1/workflows', {
  method: 'POST',
  headers: {
    'X-N8N-API-KEY': process.env.N8N_API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(workflowJSON)
});
```

Pagination: `?limit=100&cursor=<nextCursor>`

**For full API details:** `references/API_REFERENCE.md`

---

## 3. Workflow JSON Structure

### Complete Schema

```json
{
  "name": "Workflow Name",
  "nodes": [
    {
      "id": "uuid-string",
      "name": "Node Display Name",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "parameters": { },
      "credentials": {
        "credentialType": { "id": "credential-id", "name": "My Credential" }
      },
      "webhookId": "unique-webhook-id"
    }
  ],
  "connections": {
    "Source Node Name": {
      "main": [
        [{ "node": "Target Node Name", "type": "main", "index": 0 }]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "saveManualExecutions": true,
    "callerPolicy": "workflowsFromSameOwner",
    "errorWorkflow": "error-workflow-id"
  }
}
```

### Connection Rules

Connections use node **NAME** not ID.

```json
// Standard: single output → single input
"Webhook": { "main": [[{"node": "Process", "type": "main", "index": 0}]] }

// IF node: two outputs [true, false]
"IF": { "main": [
  [{"node": "True Path", "type": "main", "index": 0}],
  [{"node": "False Path", "type": "main", "index": 0}]
]}

// AI connections (special types, NOT "main")
"OpenAI Model": { "ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]] }
"HTTP Tool":    { "ai_tool": [[{"node": "AI Agent", "type": "ai_tool", "index": 0}]] }
"Memory":       { "ai_memory": [[{"node": "AI Agent", "type": "ai_memory", "index": 0}]] }
```

### Required Settings

ALWAYS include `"settings": { "executionOrder": "v1" }`. Without this, execution order is unpredictable.

### Position Layout

- X spacing: 250px between nodes
- Y spacing: 200px between parallel branches  
- Start trigger at [250, 300], flow left to right
- AI sub-nodes go 150-200px below the agent node

---

## 4. Node Type Reference

### Trigger Nodes (every workflow needs exactly one)

| Type | Use When | Key Config |
|------|----------|------------|
| `n8n-nodes-base.webhook` | HTTP requests | `path`, `httpMethod`, `responseMode` |
| `n8n-nodes-base.scheduleTrigger` | Time-based | `rule.interval` |
| `n8n-nodes-base.formTrigger` | User form input | `formFields` |
| `n8n-nodes-base.manualTrigger` | Testing | (none) |
| `n8n-nodes-base.errorTrigger` | Error handling workflow | (none) |
| `n8n-nodes-base.executeWorkflowTrigger` | Sub-workflow | input schema |
| `@n8n/n8n-nodes-langchain.chatTrigger` | AI chat interface | `options` |

### Core Processing Nodes

| Type | Purpose |
|------|---------|
| `n8n-nodes-base.set` | Set/map field values |
| `n8n-nodes-base.if` | 2-path conditional |
| `n8n-nodes-base.switch` | Multi-path conditional |
| `n8n-nodes-base.code` | Custom JS/Python |
| `n8n-nodes-base.merge` | Combine data streams |
| `n8n-nodes-base.filter` | Filter items |
| `n8n-nodes-base.aggregate` | Aggregate items |
| `n8n-nodes-base.removeDuplicates` | Deduplicate |
| `n8n-nodes-base.splitInBatches` | Batch processing |
| `n8n-nodes-base.wait` | Delay / human approval |
| `n8n-nodes-base.respondToWebhook` | Return HTTP response |
| `n8n-nodes-base.executeWorkflow` | Call sub-workflow |
| `n8n-nodes-base.stopAndError` | Force error + trigger error workflow |

### HTTP & Integration

| Type | Purpose |
|------|---------|
| `n8n-nodes-base.httpRequest` | REST API calls |
| `n8n-nodes-base.graphql` | GraphQL queries |

### Popular Services

| Type | Operations |
|------|-----------|
| `n8n-nodes-base.slack` | sendMessage, getChannel |
| `n8n-nodes-base.gmail` | send, getAll |
| `n8n-nodes-base.googleSheets` | appendOrUpdate, read |
| `n8n-nodes-base.notion` | create, get, update |
| `n8n-nodes-base.airtable` | create, list, update |
| `n8n-nodes-base.hubspot` | create, get, update |
| `n8n-nodes-base.postgres` | executeQuery, insert |

### Property Dependencies (Critical)

**HTTP Request:** `sendBody: true` → MUST set `contentType`. `authentication: "predefinedCredentialType"` → MUST set `nodeCredentialType`.

**IF Node:** Each condition needs: `leftValue`, `rightValue`, `operator.type` + `operator.operation`.

**Code Node:** `mode: "runOnceForAllItems"` → use `$input.all()`. `mode: "runOnceForEachItem"` → use `$input.item`.

**Slack:** `channel` uses resource locator: `{"__rl": true, "value": "#general", "mode": "name"}`

**Full node catalog:** `references/NODE_CATALOG.md`

---

## 5. Expression Syntax

### Core Pattern: `{{ expression }}`

| Variable | Access | Example |
|----------|--------|---------|
| `$json` | Current item data | `{{ $json.name }}` |
| `$json.body` | Webhook POST body | `{{ $json.body.email }}` |
| `$('Node').item.json` | Specific node's data | `{{ $('Webhook').item.json.body.id }}` |
| `$env` | Environment vars | `{{ $env.API_KEY }}` |
| `$now` | Current DateTime (Luxon) | `{{ $now.toISO() }}` |
| `$execution.id` | Execution ID | `{{ $execution.id }}` |
| `$workflow.id` | Workflow ID | `{{ $workflow.id }}` |
| `$runIndex` | Loop iteration | `{{ $runIndex }}` |

### CRITICAL: Webhook Data Location

```
✅ {{ $json.body.email }}        ← POST body is under .body
✅ {{ $json.headers.authorization }}
✅ {{ $json.query.page }}        ← Query params under .query
❌ {{ $json.email }}             ← WRONG! Missing .body
```

### Common Patterns

```javascript
{{ $json.name || 'Unknown' }}                          // Fallback
{{ $json.active ? 'Yes' : 'No' }}                     // Ternary
{{ `Hello ${$json.firstName} ${$json.lastName}` }}     // Template literal
{{ $now.format('yyyy-MM-dd') }}                        // Date format
{{ $now.minus({ days: 7 }).toISO() }}                  // Date math
{{ JSON.stringify($json.data) }}                       // Serialize
{{ $json.items.length }}                               // Array length
{{ $json.tags.join(', ') }}                            // Join
{{ $json.items.filter(i => i.active).length }}         // Filter + count
{{ $json.field?.subfield ?? 'default' }}               // Optional chaining
{{ Math.round($json.score * 100) / 100 }}              // Round
```

### NEVER use `{{ }}` inside Code nodes — use direct JavaScript instead.

---

## 6. Production Workflow Patterns

### Pattern A: Config-First (USE FOR EVERY PRODUCTION WORKFLOW)

Start every workflow with a Config node. Change behavior without editing logic.

```json
{
  "name": "Config",
  "type": "n8n-nodes-base.set",
  "typeVersion": 3.4,
  "position": [500, 300],
  "parameters": {
    "mode": "manual",
    "duplicateItem": false,
    "assignments": {
      "assignments": [
        {"id": "c1", "name": "config.env", "value": "production", "type": "string"},
        {"id": "c2", "name": "config.batchSize", "value": "100", "type": "number"},
        {"id": "c3", "name": "config.retryAttempts", "value": "3", "type": "number"},
        {"id": "c4", "name": "config.dryRun", "value": "false", "type": "boolean"},
        {"id": "c5", "name": "config.alertChannel", "value": "#ops-alerts", "type": "string"}
      ]
    }
  }
}
```

Then reference: `{{ $('Config').item.json.config.batchSize }}`

### Pattern B: Idempotent Processing

Prevent duplicate processing when retries/replays happen:

```javascript
// In a Code node — check if already processed
const itemId = $input.item.json.id;
const checkUrl = `${$env.API_URL}/processed/${itemId}`;

try {
  const existing = await $helpers.httpRequest({ url: checkUrl, method: 'GET' });
  if (existing.processed) {
    return []; // Skip — already processed (return empty to drop item)
  }
} catch (e) {
  // 404 means not yet processed — continue
  if (e.statusCode !== 404) throw e;
}

// Process and mark as done
const result = await processItem($input.item.json);
await $helpers.httpRequest({
  url: `${$env.API_URL}/processed/${itemId}`,
  method: 'POST',
  body: { processed: true, timestamp: new Date().toISOString() }
});

return [{ json: result }];
```

### Pattern C: Circuit Breaker

Stop calling a failing API after N consecutive failures:

```javascript
// Check circuit breaker state
const circuitKey = 'circuit:external-api';
let state;
try {
  state = await $helpers.httpRequest({
    url: `${$env.REDIS_URL}/get/${circuitKey}`, method: 'GET'
  });
} catch (e) { state = { failures: 0 }; }

if (state.failures >= 5) {
  const lastFail = new Date(state.lastFailure);
  const cooldown = 60000; // 1 minute
  if (Date.now() - lastFail.getTime() < cooldown) {
    // Circuit OPEN — skip call, use fallback
    return [{ json: { source: 'fallback', data: $input.item.json.cachedData } }];
  }
  // Cooldown passed — try again (half-open)
}

try {
  const result = await $helpers.httpRequest({ url: 'https://api.example.com/data', method: 'GET' });
  // Success — reset circuit
  await $helpers.httpRequest({
    url: `${$env.REDIS_URL}/set/${circuitKey}`,
    method: 'POST', body: { failures: 0 }
  });
  return [{ json: result }];
} catch (e) {
  // Failure — increment circuit
  await $helpers.httpRequest({
    url: `${$env.REDIS_URL}/set/${circuitKey}`,
    method: 'POST',
    body: { failures: (state.failures || 0) + 1, lastFailure: new Date().toISOString() }
  });
  throw e;
}
```

### Pattern D: Centralized Error Handler ("Mission Control")

Create ONE error workflow that monitors ALL your workflows:

```json
{
  "name": "Mission Control — Error Handler",
  "nodes": [
    {
      "id": "e1", "name": "Error Trigger",
      "type": "n8n-nodes-base.errorTrigger",
      "typeVersion": 1, "position": [250, 300], "parameters": {}
    },
    {
      "id": "e2", "name": "Format Alert",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2, "position": [500, 300],
      "parameters": {
        "jsCode": "const error = $input.first().json;\nconst alert = {\n  workflow: error.workflow?.name || 'Unknown',\n  workflowId: error.workflow?.id,\n  node: error.execution?.error?.node?.name || 'Unknown',\n  message: error.execution?.error?.message || 'No message',\n  timestamp: new Date().toISOString(),\n  executionUrl: error.execution?.url || '',\n  severity: error.execution?.error?.message?.includes('timeout') ? 'warning' : 'critical'\n};\nreturn [{ json: alert }];"
      }
    },
    {
      "id": "e3", "name": "Alert Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2, "position": [750, 300],
      "parameters": {
        "resource": "message", "operation": "send",
        "channel": {"__rl": true, "value": "#ops-alerts", "mode": "name"},
        "text": "🚨 *Workflow Error*\n*Workflow:* {{ $json.workflow }}\n*Node:* {{ $json.node }}\n*Error:* {{ $json.message }}\n*Time:* {{ $json.timestamp }}\n*Execution:* {{ $json.executionUrl }}"
      },
      "credentials": {"slackApi": {"id": "CREDENTIAL_ID", "name": "Slack"}}
    }
  ],
  "connections": {
    "Error Trigger": {"main": [[{"node": "Format Alert", "type": "main", "index": 0}]]},
    "Format Alert": {"main": [[{"node": "Alert Slack", "type": "main", "index": 0}]]}
  },
  "settings": {"executionOrder": "v1"}
}
```

Then set `"errorWorkflow": "MISSION_CONTROL_ID"` in every workflow's settings.

### Pattern E: Webhook with HMAC Verification

```javascript
// Code node right after Webhook trigger
const crypto = require('crypto');
const secret = $env.WEBHOOK_SECRET;
const body = JSON.stringify($input.first().json.body);
const signature = $input.first().json.headers['x-signature-256'] || 
                  $input.first().json.headers['x-hub-signature-256'];

if (!signature) {
  throw new Error('Missing signature header');
}

const hmac = crypto.createHmac('sha256', secret);
hmac.update(body);
const expected = 'sha256=' + hmac.digest('hex');

if (signature !== expected) {
  throw new Error('Invalid webhook signature — request rejected');
}

return $input.all(); // Signature valid — pass data through
```

**For 20+ complete workflow JSON patterns:** `references/PATTERNS_LIBRARY.md`

---

## 7. AI Agent Workflows

### AI Connection Types (NOT "main")

| Type | Purpose | Required? |
|------|---------|-----------|
| `ai_languageModel` | LLM (OpenAI, Anthropic, etc.) | **YES** for all AI nodes |
| `ai_tool` | Tools the agent can use | Recommended |
| `ai_memory` | Conversation memory | Optional |
| `ai_outputParser` | Structured output | Optional |
| `ai_retriever` | RAG retrieval | For RAG chains |
| `ai_embedding` | Vector embeddings | For vector stores |

### Complete AI Agent Blueprint

```json
{
  "name": "AI Agent",
  "nodes": [
    {
      "id": "t1", "name": "Chat Trigger",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger",
      "typeVersion": 1.1, "position": [250, 300],
      "parameters": {"options": {}}, "webhookId": "chat-001"
    },
    {
      "id": "a1", "name": "AI Agent",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "typeVersion": 1.7, "position": [500, 300],
      "parameters": {
        "options": {
          "systemMessage": "You are a helpful assistant. Use tools when needed.",
          "maxIterations": 10,
          "returnIntermediateSteps": false
        }
      }
    },
    {
      "id": "m1", "name": "OpenAI Model",
      "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
      "typeVersion": 1.2, "position": [400, 500],
      "parameters": {"model": "gpt-4o", "options": {"temperature": 0.7}},
      "credentials": {"openAiApi": {"id": "CRED", "name": "OpenAI"}}
    },
    {
      "id": "tool1", "name": "HTTP Tool",
      "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
      "typeVersion": 1.1, "position": [600, 500],
      "parameters": {
        "url": "https://api.example.com/search",
        "method": "GET",
        "description": "Search the database by keyword. Input: query string."
      }
    },
    {
      "id": "tool2", "name": "Think",
      "type": "@n8n/n8n-nodes-langchain.toolThink",
      "typeVersion": 1, "position": [750, 500], "parameters": {}
    },
    {
      "id": "mem1", "name": "Memory",
      "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
      "typeVersion": 1.3, "position": [300, 500],
      "parameters": {"sessionIdType": "customKey", "sessionKey": "={{ $json.sessionId }}"}
    }
  ],
  "connections": {
    "Chat Trigger": {"main": [[{"node": "AI Agent", "type": "main", "index": 0}]]},
    "OpenAI Model": {"ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]]},
    "HTTP Tool": {"ai_tool": [[{"node": "AI Agent", "type": "ai_tool", "index": 0}]]},
    "Think": {"ai_tool": [[{"node": "AI Agent", "type": "ai_tool", "index": 0}]]},
    "Memory": {"ai_memory": [[{"node": "AI Agent", "type": "ai_memory", "index": 0}]]}
  },
  "settings": {"executionOrder": "v1"}
}
```

### Available AI Sub-Nodes

**Models:** lmChatOpenAi, lmChatAnthropic, lmChatGoogleGemini, lmChatOllama, lmChatGroq, lmChatAzureOpenAi, lmChatMistralCloud, lmChatDeepSeek

**Tools:** toolHttpRequest, toolCode, toolWorkflow, toolCalculator, toolWikipedia, toolSerpApi, toolSearxng, toolMcp, toolVectorStore, toolThink

**Memory:** memoryBufferWindow, memoryPostgresChat, memoryRedisChat, memoryMongoChat, memoryXata, memoryZep

**Output Parsers:** outputParserStructured, outputParserItemList, outputParserAutofixing

**Best Practices:**
- ALWAYS add Think tool — gives agent a scratchpad for reasoning
- Limit to 5-10 tools per agent. Too many confuses tool selection.
- Write specific tool descriptions: "Search customers by email" not "Gets data"
- Set maxIterations to 5-10 to prevent infinite loops
- Use temperature 0-0.3 for task-oriented agents, 0.7+ for creative
- For persistent memory, use Postgres or Redis (buffer is ephemeral)

### Multi-Agent Patterns

**Sequential:** Agent A → result → Agent B → result → Agent C
```
Use Execute Sub-workflow nodes to chain agent workflows
```

**Parallel:** Split → Agent A + Agent B → Merge results
```
Use Merge node after parallel Execute Workflow nodes
```

**Hierarchical Router:** Gatekeeper routes to specialists
```
Router Agent has Workflow Tools pointing to specialist agent workflows
Tool descriptions determine routing: "research" / "action" / "creative"
```

**For full multi-agent JSON patterns and MCP integration:** `references/MCP_INTEGRATION.md`

---

## 8. Code Node Mastery

### CRITICAL: Return Format

```javascript
// ✅ CORRECT — always return array of {json: {...}} objects
return [{ json: { name: "test" } }];
return items.map(i => ({ json: { ...i.json, done: true } }));

// ❌ WRONG — all of these will fail
return { name: "test" };           // Not an array
return [{ name: "test" }];         // Missing json wrapper
return "string";                   // Not an array of objects
```

### Two Execution Modes

**Run Once for All Items (default):**
```javascript
const items = $input.all();
return items.map(item => ({
  json: { ...item.json, processed: true, ts: new Date().toISOString() }
}));
```

**Run Once for Each Item:**
```javascript
return [{ json: { ...$input.item.json, processed: true } }];
```

### HTTP Requests Inside Code

```javascript
// ✅ Use built-in helper
const data = await $helpers.httpRequest({
  method: 'GET',
  url: 'https://api.example.com/data',
  headers: { 'Authorization': `Bearer ${$env.API_TOKEN}` }
});
return [{ json: data }];

// ❌ fetch() and axios are NOT available
```

### Webhook Data Access

```javascript
const body = $input.first().json.body;    // POST body
const headers = $input.first().json.headers; // Headers
const query = $input.first().json.query;    // Query params
```

### Date Operations (Luxon available)

```javascript
const { DateTime } = require('luxon');
const now = DateTime.now();
const formatted = now.toFormat('yyyy-MM-dd');
const weekAgo = now.minus({ days: 7 }).toISO();
```

### Python Limitations (use JS for 95% of cases)

- Standard library ONLY (no requests, pandas, numpy)
- Use `_input` not `$input`, `_env` not `$env`
- Return same format: `[{"json": {...}}]`

---

## 9. Error Handling & Debugging

### Three Layers of Error Handling

**Layer 1: Node-Level** — Retry on fail
```json
{ "retryOnFail": true, "maxTries": 3, "waitBetweenTries": 2000 }
```

**Layer 2: Node-Level** — Continue on error (captures error output)
Set node setting: "On Error" → "Continue (using error output)"
Provides a second output with error details.

**Layer 3: Workflow-Level** — Error workflow
Set `"errorWorkflow": "WORKFLOW_ID"` in settings.
Uses Error Trigger node in a separate monitoring workflow.

### Top 10 Errors & Instant Fixes

| # | Error | Fix |
|---|-------|-----|
| 1 | `Cannot read properties of undefined` | Use optional chaining: `$json.body?.email` or check webhook `.body` path |
| 2 | Code node returns wrong format | Return `[{ json: {...} }]` — always array of json-wrapped objects |
| 3 | AI node "no language model" | Connect model via `ai_languageModel` type, NOT `main` |
| 4 | Wrong node type prefix | Use `n8n-nodes-base.` in JSON, `nodes-base.` only in MCP tools |
| 5 | Webhook not receiving data | Test URL only works in editor. Production URL only when activated. |
| 6 | Respond to Webhook does nothing | Set webhook `responseMode: "responseNode"` |
| 7 | 429 Too Many Requests | Add Wait node + enable retryOnFail + batch processing |
| 8 | Connection target not found | Connections use node NAME not ID — check for typos |
| 9 | Agent loops infinitely | Set `maxIterations: 5`, add Think tool, improve tool descriptions |
| 10 | `Additional properties not allowed` | Remove unknown settings fields; only use executionOrder, callerPolicy |

### Debugging Strategy

```
1. GET /api/v1/executions/{id} → Check execution data for each node
2. Look at the FIRST node that failed — upstream nodes were fine
3. Check the input data shape vs what the node expects
4. For webhooks: verify .body, .headers, .query structure
5. For Code nodes: add console.log as first line
6. For AI agents: check tool call logs in execution detail
7. Pin test data on nodes to isolate issues
```

**For decision-tree error playbooks:** `references/TROUBLESHOOTING.md`

---

## 10. Credentials Management

### Creating via API

```javascript
// Get schema first
const schema = await fetch('/api/v1/credentials/schema/slackApi', {
  headers: { 'X-N8N-API-KEY': apiKey }
});

// Create
await fetch('/api/v1/credentials', {
  method: 'POST',
  headers: { 'X-N8N-API-KEY': apiKey, 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: "Slack Bot", type: "slackApi", data: { accessToken: "xoxb-..." } })
});
```

### Common Credential Type Names

| Service | Type | Auth Method |
|---------|------|-------------|
| Slack | `slackApi` | Bot token |
| Gmail | `gmailOAuth2` | OAuth2 |
| Google Sheets | `googleSheetsOAuth2Api` | OAuth2 |
| OpenAI | `openAiApi` | API key |
| Anthropic | `anthropicApi` | API key |
| Postgres | `postgres` | Connection string |
| HTTP Header | `httpHeaderAuth` | Custom header |
| HTTP Basic | `httpBasicAuth` | Username/password |
| OAuth2 | `oAuth2Api` | OAuth2 flow |

### Reference in Nodes

```json
"credentials": { "slackApi": { "id": "abc123", "name": "Slack Bot" } }
```

---

## 11. Production Deployment Checklist

### Before Activation

```
□ Validation script passes with 0 errors
□ Every workflow has exactly ONE trigger
□ All node names are unique
□ Connections reference correct names
□ Credentials attached to all service nodes
□ Webhook paths are unique across workflows
□ Error workflow is set in settings
□ Config node present with env/batch/retry settings
□ Code nodes return [{ json: {...} }]
□ Expressions use correct paths (.body for webhooks)
□ Test execution succeeds
□ Execution logs reviewed for data correctness
```

### Performance Rules

| Rule | Implementation |
|------|---------------|
| Batch API calls | Loop Over Items node, batch size matching rate limit |
| Modular design | Sub-workflows for reusable logic. Target 5-15 nodes per workflow. |
| Pagination | Always handle nextCursor for list endpoints |
| Timeouts | Set execution timeout in workflow settings |
| Memory | Process large datasets in batches, never all at once |
| Deduplication | Check-before-process pattern for idempotency |
| Error isolation | Critical workflows on separate n8n instance/queue |

### Environment Variables

```
{{ $env.API_BASE_URL }}
{{ $env.SLACK_CHANNEL_ID }}
{{ $env.DATABASE_HOST }}
```

---

## 12. Decision Framework

### Build Order (FOLLOW THIS)

```
1. IDENTIFY trigger type (what starts this?)
2. ADD Config node (env, batch size, feature flags)
3. MAP data flow (what data moves where?)
4. SELECT nodes (reference Node Catalog)
5. SCAFFOLD using scaffold_workflow.py
6. CUSTOMIZE parameters, expressions, credentials
7. ADD error handling (retry, error output, error workflow)
8. VALIDATE using validate_workflow.py
9. DEPLOY inactive via API
10. TEST and review execution logs
11. FIX if needed → re-validate → re-deploy
12. ACTIVATE
```

### Choosing the Right Approach

| Need | Use |
|------|-----|
| Simple field mapping | Set node |
| Complex transformation | Code node (JS) |
| 2-path conditional | IF node |
| 3+ path conditional | Switch node |
| Call external API | HTTP Request node |
| Batch process | Loop Over Items + Wait |
| AI-powered processing | AI Agent + tools |
| Reusable logic | Sub-workflow (Execute Workflow node) |
| Webhook response | Respond to Webhook (only with webhook trigger!) |
| Error monitoring | Error Trigger in separate workflow |
| Human approval | Wait node (webhook resume) |
| Rate limiting | Wait node + Loop Over Items with batch size |

### When to Use Code vs Built-in Nodes

**Code Node:** Complex transforms, custom business logic, multi-step calculations, 
string manipulation, API response parsing, conditional logic with >3 conditions.

**Built-in Nodes:** Simple field mapping (Set), basic conditions (IF/Switch), 
standard API calls (HTTP Request), standard service operations (Slack, Gmail, etc.),
date formatting.

### Sub-Workflow Guidelines

- **Single responsibility**: Each sub-workflow does ONE thing
- **Define input schema** on Execute Workflow Trigger for clarity
- **5-15 nodes per workflow** — refactor above 30
- **Parallel execution**: Use multiple Execute Workflow nodes → Merge
- **Version control**: Export workflow JSON to git regularly
