# n8n REST API Deep Reference

## Table of Contents
1. [Authentication Methods](#authentication)
2. [Workflow Endpoints](#workflows)
3. [Execution Endpoints](#executions)
4. [Credential Endpoints](#credentials)
5. [Tags & Organization](#tags)
6. [Source Control](#source-control)
7. [Error Responses](#errors)
8. [Rate Limits & Pagination](#pagination)
9. [Webhook URLs](#webhooks)

---

## Authentication

### API Key (Recommended for Automation)
```
X-N8N-API-KEY: your-api-key-here
```
Generate in: Settings → API → Create API Key

### Bearer Token (OAuth)
```
Authorization: Bearer <token>
```

### Base URLs
- Cloud: `https://<instance>.app.n8n.cloud/api/v1`
- Self-hosted: `https://your-domain.com/api/v1`

---

## Workflows

### List Workflows
```
GET /workflows?limit=100&cursor=<nextCursor>&tags=tagId&active=true
```
Response:
```json
{
  "data": [
    {
      "id": "workflow-id",
      "name": "My Workflow",
      "active": true,
      "createdAt": "2024-01-01T00:00:00.000Z",
      "updatedAt": "2024-01-02T00:00:00.000Z",
      "tags": [{ "id": "tag-id", "name": "production" }]
    }
  ],
  "nextCursor": "cursor-string-or-null"
}
```

### Get Workflow
```
GET /workflows/:id
```
Returns full workflow JSON including nodes, connections, settings.

### Create Workflow
```
POST /workflows
Content-Type: application/json

{
  "name": "New Workflow",
  "nodes": [...],
  "connections": {...},
  "settings": {
    "executionOrder": "v1"
  }
}
```

**IMPORTANT**: The `executionOrder: "v1"` setting is required for modern n8n. Without it,
node execution order may be unpredictable.

### Update Workflow (Full Replace)
```
PUT /workflows/:id
Content-Type: application/json

{ ... full workflow object ... }
```

### Update Workflow (Partial)
```
PATCH /workflows/:id
Content-Type: application/json

{
  "name": "Updated Name",
  "active": true
}
```

### Delete Workflow
```
DELETE /workflows/:id
```

### Activate / Deactivate
```
POST /workflows/:id/activate
POST /workflows/:id/deactivate
```

### Transfer Workflow
```
POST /workflows/:id/transfer
Content-Type: application/json

{
  "destinationProjectId": "project-id"
}
```

---

## Executions

### List Executions
```
GET /executions?workflowId=wf-id&status=success&limit=20
```

Status values: `error`, `success`, `waiting`, `running`, `new`

### Get Execution
```
GET /executions/:id
```
Returns full execution data including input/output for each node.

### Delete Execution
```
DELETE /executions/:id
```

### Run Workflow Manually
```
POST /workflows/:id/run
Content-Type: application/json

{
  "data": {
    "key": "value"
  }
}
```

This triggers the workflow as if its trigger fired, passing the data payload.

---

## Credentials

### List Credentials
```
GET /credentials?type=slackApi
```

### Create Credential
```
POST /credentials
Content-Type: application/json

{
  "name": "My Slack Bot",
  "type": "slackApi",
  "data": {
    "accessToken": "xoxb-..."
  }
}
```

### Get Credential Schema
```
GET /credentials/schema/:credentialTypeName
```
Returns the expected fields for a credential type.

### Delete Credential
```
DELETE /credentials/:id
```

**NOTE**: Credentials data is encrypted at rest. The API never returns raw secrets
in GET responses — only metadata (name, type, id).

---

## Tags

### List Tags
```
GET /tags?limit=50
```

### Create Tag
```
POST /tags
Content-Type: application/json

{ "name": "production" }
```

### Update Tag
```
PATCH /tags/:id
Content-Type: application/json

{ "name": "renamed-tag" }
```

### Delete Tag
```
DELETE /tags/:id
```

---

## Source Control

### Pull from Remote
```
POST /source-control/pull
Content-Type: application/json

{ "force": false }
```

### Push to Remote
```
POST /source-control/push
Content-Type: application/json

{
  "commitMessage": "Update workflow",
  "force": false
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "code": 404,
  "message": "Workflow not found",
  "hint": "Check the workflow ID"
}
```

### Common Error Codes
| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid JSON, missing required fields |
| 401 | Unauthorized | Invalid/missing API key |
| 403 | Forbidden | API key lacks permission |
| 404 | Not Found | Wrong workflow/execution ID |
| 409 | Conflict | Workflow name already exists (when enforced) |
| 422 | Unprocessable | Valid JSON but invalid workflow structure |
| 429 | Too Many Requests | Rate limited |
| 500 | Server Error | n8n internal error |

---

## Pagination

All list endpoints support cursor-based pagination:
```
GET /workflows?limit=50&cursor=eyJsYXN0SWQi...
```

Response includes `nextCursor` — pass it as `cursor` for next page.
When `nextCursor` is `null`, you've reached the end.

### Pagination Loop Pattern
```javascript
let allWorkflows = [];
let cursor = null;

do {
  const url = `/api/v1/workflows?limit=100${cursor ? `&cursor=${cursor}` : ''}`;
  const response = await fetch(url, { headers });
  const data = await response.json();
  allWorkflows.push(...data.data);
  cursor = data.nextCursor;
} while (cursor);
```

---

## Webhook URLs

### Production vs Test URLs
- **Test**: `https://instance/webhook-test/path` (only works during manual testing)
- **Production**: `https://instance/webhook/path` (works when workflow is active)

### Webhook Path Configuration
The path you set in the Webhook node becomes the URL suffix:
- Node path: `my-endpoint`
- Full URL: `https://instance/webhook/my-endpoint`

### Webhook Response Modes
| Mode | Behavior |
|------|----------|
| `lastNode` | Returns output of last node |
| `responseNode` | Returns output of Respond to Webhook node |
| `immediately` | Returns 200 OK immediately, continues processing |

### Custom Webhook Response Headers
Set in the Respond to Webhook node or via Webhook node options:
```json
{
  "options": {
    "responseHeaders": {
      "entries": [
        { "name": "X-Custom-Header", "value": "custom-value" }
      ]
    }
  }
}
```
