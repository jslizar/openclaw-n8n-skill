# n8n Error Recovery Playbooks

Decision-tree troubleshooting for every common failure mode.
Follow the tree → apply the fix → re-validate → re-deploy.

---

## Playbook 1: HTTP Request Failures

```
HTTP Request Failed
├─ 401 Unauthorized
│   ├─ Is credential attached? → No → Attach credential in node config
│   ├─ Is token expired? → OAuth2: re-auth in UI. API Key: regenerate + update credential
│   └─ Wrong auth type? → Try Header Auth: "Authorization: Bearer {token}"
├─ 403 Forbidden
│   ├─ API key permissions/scopes correct?
│   ├─ IP whitelisted? (common with self-hosted n8n)
│   └─ Endpoint path correct? (some APIs return 403 for wrong paths)
├─ 404 Not Found
│   ├─ URL correct? Debug: log {{ $json.url }} before request
│   ├─ Dynamic resource ID exists? Check previous node output
│   └─ API version in URL: /v1/ vs /v2/ matters
├─ 429 Rate Limited
│   ├─ Add Wait node: {"amount": 1, "unit": "seconds"}
│   ├─ Enable retryOnFail: true, maxTries: 3, waitBetweenTries: 2000
│   ├─ Batch processing: Loop Over Items, batch=10, wait between
│   └─ Exponential backoff in Code:
│       const delay = Math.pow(2, $runIndex) * 1000;
│       await new Promise(r => setTimeout(r, delay));
├─ 500/502/503 Server Error
│   └─ Their problem → enable retryOnFail (transient errors clear on retry)
├─ ECONNREFUSED
│   ├─ URL reachable from n8n server?
│   ├─ Docker: use container name, not localhost
│   └─ Firewall/security group allows outbound?
└─ SSL Error
    ├─ URL using https:// correctly?
    ├─ Self-signed cert → "Ignore SSL Issues" in node options
    └─ Expired cert → contact API provider
```

---

## Playbook 2: Webhook Issues

```
Webhook Not Working
├─ Not receiving data
│   ├─ Test URL vs Production URL:
│   │   TEST: only active when you click "Listen for Test Event"
│   │   PRODUCTION: only active when workflow is ACTIVATED
│   ├─ Path conflicts: each path must be unique across ALL active workflows
│   │   Fix: use path: "={{$workflow.id}}" for auto-unique paths
│   └─ Method mismatch: sender using POST but webhook set to GET?
├─ Data not accessible
│   ├─ CRITICAL: POST body is at $json.body, NOT $json
│   │   ✅ {{ $json.body.email }}
│   │   ❌ {{ $json.email }}
│   ├─ Query params: $json.query.paramName
│   ├─ Headers: $json.headers.headerName (all lowercase!)
│   └─ Debug: Code node → console.log(JSON.stringify($input.first().json))
├─ Wrong response returned
│   ├─ responseMode: "onReceived" → 200 immediately, processes async
│   ├─ responseMode: "lastNode" → returns output of final node
│   ├─ responseMode: "responseNode" → returns Respond to Webhook output
│   └─ Need custom response → use "responseNode" + Respond to Webhook node
└─ Webhook security
    ├─ HMAC verification: see Pattern E in SKILL.md
    ├─ IP whitelisting: use IF node to check $json.headers['x-forwarded-for']
    └─ Rate limiting: Code node counter → IF threshold → reject with 429
```

---

## Playbook 3: Code Node Failures

```
Code Node Error
├─ "Cannot read properties of undefined"
│   ├─ Use optional chaining: $json.body?.email
│   ├─ Null check: if ($json.body && $json.body.email)
│   └─ Debug first line: console.log(JSON.stringify($input.item.json, null, 2))
├─ Return format wrong
│   ├─ MUST return: [{ json: { key: value } }]
│   ├─ ❌ return { result: "data" }          → Not an array
│   ├─ ❌ return [{ result: "data" }]         → Missing json wrapper
│   └─ ✅ return [{ json: { result: "data" } }]
├─ $input errors
│   ├─ "All Items" mode: $input.all() returns array, loop it
│   ├─ "Each Item" mode: $input.item.json for single item
│   └─ Mismatch = error. Check mode matches your code.
├─ Expressions inside code
│   ├─ ❌ const x = {{ $json.name }}      → syntax error
│   ├─ ✅ const x = $input.item.json.name → direct JS access
│   └─ ✅ const x = $json.name            → shorthand in Each Item mode
├─ HTTP inside code
│   ├─ ❌ fetch(), axios, require('axios') → NOT available
│   └─ ✅ await $helpers.httpRequest({url, method, headers, body})
├─ Python specific
│   ├─ ❌ import requests/pandas/numpy → standard library ONLY
│   ├─ ❌ $input → use _input
│   └─ ❌ $env → use _env
└─ Timeout
    ├─ Code running too long → optimize loops, reduce data size
    └─ HTTP request in code → add timeout option to $helpers.httpRequest
```

---

## Playbook 4: AI Agent Failures

```
AI Agent Error
├─ "No language model connected"
│   └─ Connect model to agent via ai_languageModel type (NOT "main")
│       Model → ai_languageModel → Agent
├─ Agent loops infinitely
│   ├─ Set maxIterations: 5-10 in agent options
│   ├─ Add Think tool (gives agent scratchpad for reasoning)
│   ├─ Improve tool descriptions (make them mutually exclusive)
│   └─ Add system message: "Complete the task in as few steps as possible."
├─ Agent picks wrong tool
│   ├─ Bad descriptions: "Gets data" / "Retrieves info" (too similar)
│   ├─ Good: "Search customers by email" / "Get order by ID" (specific)
│   └─ Reduce to 5-10 tools max per agent
├─ Empty/generic response
│   ├─ Add clear system message with specific instructions
│   ├─ Use Structured Output Parser for enforced format
│   └─ Lower temperature: 0-0.3 for task-oriented agents
├─ Memory not persisting
│   ├─ Session ID passing correctly? sessionKey: "={{ $json.sessionId }}"
│   ├─ BufferWindow = ephemeral (resets per execution)
│   ├─ Use Postgres/Redis memory for persistence
│   └─ Memory node connected via ai_memory type?
├─ Tool execution fails
│   ├─ Check execution logs → which tool call failed
│   ├─ Tool credentials configured?
│   ├─ Tool URL accessible from n8n server?
│   └─ Test tool independently before connecting to agent
├─ MCP Client "Invalid Request"
│   ├─ Known bug: complex schemas → z.any() → wrong input
│   ├─ Fix: simplify MCP tool input schemas (flat objects only)
│   └─ Workaround: wrapper tool that translates simple → complex
└─ Token limit exceeded
    ├─ Reduce BufferWindow size (5-10 messages)
    ├─ Use smaller model for routing, larger for generation
    └─ Break into sub-agents with focused contexts
```

---

## Playbook 5: Connection & Flow Errors

```
Data Flow Problems
├─ "No items" reaching a node
│   ├─ Previous node output empty? Check its execution data
│   ├─ IF/Switch/Filter sending down wrong branch?
│   ├─ Connection name typo? (connections use exact NAME match)
│   └─ Debug: pin test data → execute step by step
├─ Data shape unexpected
│   ├─ Previous node returns different fields per input?
│   ├─ Fix: Set node to normalize shape
│   └─ Fix: optional chaining in expressions: {{ $json.field?.sub ?? 'default' }}
├─ Merge combines wrong items
│   ├─ "Combine by Position" → items paired 1:1 (must be same count)
│   ├─ "Merge By Fields" → matched by key field value
│   └─ "Append" → just concatenates both inputs
├─ Sub-workflow data passing
│   ├─ Define input schema on Execute Workflow Trigger
│   ├─ Parent: data passed via Execute Workflow node params
│   ├─ Child: access via trigger node output
│   └─ Child output returns to parent's Execute Workflow node
└─ Duplicate items
    ├─ Use removeDuplicates node before processing
    └─ Or idempotency check in Code node (see Pattern B in SKILL.md)
```

---

## Playbook 6: Deployment Failures

```
Won't Activate / Deploy Fails
├─ Credential errors
│   ├─ Each node with external service needs credential attached
│   ├─ OAuth tokens may need re-authentication in UI
│   └─ Check credential permissions match required scopes
├─ "Additional properties not allowed" (API error)
│   ├─ Extra properties in settings object
│   ├─ Fix: only include: executionOrder, callerPolicy, errorWorkflow
│   ├─ Remove: mcpValidation, requestId, or any custom properties
│   └─ Workaround: delete + recreate workflow
├─ Works in test, fails in production
│   ├─ Test URL ≠ Production URL (different execution paths)
│   ├─ Environment variables set for production?
│   ├─ Credential tokens valid in production context?
│   └─ Rate limits (production gets more traffic)
└─ Webhook path conflict
    ├─ Another active workflow using same path
    └─ Fix: unique paths per workflow (use {{$workflow.id}})
```

---

## Playbook 7: Performance

```
Slow or Timing Out
├─ Too many items at once
│   ├─ Batch with Loop Over Items: batch size 50-100
│   ├─ Add pagination for API calls
│   └─ Process in chunks, aggregate results after
├─ Sub-workflows too slow
│   ├─ Run in parallel (multiple Execute Workflow → Merge)
│   └─ Reduce nodes per sub-workflow (target 5-15)
├─ Memory issues
│   ├─ Large JSON payloads → extract only needed fields with Set node
│   ├─ Binary data → process in batches, don't load all at once
│   └─ Execution history → disable saving for high-volume workflows
├─ External API slow
│   ├─ Set timeout in HTTP Request options
│   ├─ Add Wait + retry instead of waiting indefinitely
│   └─ Cache responses (store in Redis/Postgres, check before calling)
└─ Workflow too complex (>30 nodes)
    ├─ Break into sub-workflows
    ├─ Each sub-workflow: single responsibility
    └─ Target: 5-15 nodes per workflow, 30 max
```

---

## Quick Diagnostic Commands

### Check workflow validity
```bash
python scripts/validate_workflow.py workflow.json
```

### Check execution logs
```bash
curl -s -H "X-N8N-API-KEY: $KEY" \
  "https://n8n.example.com/api/v1/executions?workflowId=$WF_ID&limit=5" | python -m json.tool
```

### Get failed execution details
```bash
curl -s -H "X-N8N-API-KEY: $KEY" \
  "https://n8n.example.com/api/v1/executions/$EXEC_ID" | python -m json.tool
```

### List all active workflows
```bash
curl -s -H "X-N8N-API-KEY: $KEY" \
  "https://n8n.example.com/api/v1/workflows?active=true" | python -m json.tool
```

### Deactivate a failing workflow
```bash
curl -X POST -H "X-N8N-API-KEY: $KEY" \
  "https://n8n.example.com/api/v1/workflows/$WF_ID/deactivate"
```
