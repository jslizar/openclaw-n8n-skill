# n8n Workflow Patterns Library

Complete, copy-paste-ready workflow JSON for common automation patterns.

## Table of Contents
1. [Webhook → Process → Respond](#pattern-1)
2. [Schedule → Fetch → Deliver](#pattern-2)
3. [Form → Validate → Branch → Store](#pattern-3)
4. [Error-Resilient API Pipeline](#pattern-4)
5. [Sub-Workflow Architecture](#pattern-5)
6. [AI Agent with Tools](#pattern-6)
7. [Database Sync Pipeline](#pattern-7)
8. [Email Processing Pipeline](#pattern-8)
9. [Batch Processing Loop](#pattern-9)
10. [Multi-Channel Notification](#pattern-10)
11. [RAG (Retrieval-Augmented Generation)](#pattern-11)
12. [CRM Lead Enrichment](#pattern-12)
13. [File Processing Pipeline](#pattern-13)
14. [Rate-Limited API Crawler](#pattern-14)
15. [Approval Workflow](#pattern-15)

---

## Pattern 1: Webhook → Process → Respond {#pattern-1}

**Use case**: API endpoint that processes incoming data and returns a response.

```json
{
  "name": "Webhook API Endpoint",
  "nodes": [
    {
      "id": "trigger-1",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "parameters": {
        "path": "process-data",
        "httpMethod": "POST",
        "responseMode": "responseNode",
        "options": {}
      },
      "webhookId": "webhook-001"
    },
    {
      "id": "process-1",
      "name": "Transform Data",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [500, 300],
      "parameters": {
        "jsCode": "const body = $input.first().json.body;\n\nif (!body.email) {\n  throw new Error('Email is required');\n}\n\nreturn [{\n  json: {\n    success: true,\n    data: {\n      email: body.email.toLowerCase().trim(),\n      name: body.name || 'Unknown',\n      processedAt: new Date().toISOString()\n    }\n  }\n}];"
      }
    },
    {
      "id": "respond-1",
      "name": "Send Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "position": [750, 300],
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}"
      }
    }
  ],
  "connections": {
    "Webhook": { "main": [[{ "node": "Transform Data", "type": "main", "index": 0 }]] },
    "Transform Data": { "main": [[{ "node": "Send Response", "type": "main", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Pattern 2: Schedule → Fetch → Deliver {#pattern-2}

**Use case**: Daily report that pulls data from an API and emails it.

```json
{
  "name": "Daily Report Pipeline",
  "nodes": [
    {
      "id": "schedule-1",
      "name": "Every Morning at 9AM",
      "type": "n8n-nodes-base.scheduleTrigger",
      "typeVersion": 1.2,
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{ "field": "cronExpression", "expression": "0 9 * * *" }]
        }
      }
    },
    {
      "id": "fetch-1",
      "name": "Fetch Analytics",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [500, 300],
      "parameters": {
        "url": "https://api.example.com/analytics/daily",
        "method": "GET",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            { "name": "Accept", "value": "application/json" }
          ]
        }
      }
    },
    {
      "id": "format-1",
      "name": "Format Report",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [750, 300],
      "parameters": {
        "jsCode": "const data = $input.first().json;\nconst report = `# Daily Report - ${new Date().toLocaleDateString()}\\n\\n` +\n  `Total Users: ${data.totalUsers}\\n` +\n  `Revenue: $${data.revenue.toFixed(2)}\\n` +\n  `Active Sessions: ${data.activeSessions}`;\n\nreturn [{ json: { report, subject: `Daily Report - ${new Date().toLocaleDateString()}` } }];"
      }
    },
    {
      "id": "email-1",
      "name": "Send Email",
      "type": "n8n-nodes-base.sendEmail",
      "typeVersion": 2.1,
      "position": [1000, 300],
      "parameters": {
        "fromEmail": "reports@example.com",
        "toEmail": "team@example.com",
        "subject": "={{ $json.subject }}",
        "emailFormat": "text",
        "text": "={{ $json.report }}"
      }
    }
  ],
  "connections": {
    "Every Morning at 9AM": { "main": [[{ "node": "Fetch Analytics", "type": "main", "index": 0 }]] },
    "Fetch Analytics": { "main": [[{ "node": "Format Report", "type": "main", "index": 0 }]] },
    "Format Report": { "main": [[{ "node": "Send Email", "type": "main", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Pattern 3: Form → Validate → Branch → Store {#pattern-3}

**Use case**: User fills a form, data is validated, stored in DB, and routed.

```json
{
  "name": "Form Processing Pipeline",
  "nodes": [
    {
      "id": "form-1",
      "name": "Contact Form",
      "type": "n8n-nodes-base.formTrigger",
      "typeVersion": 2.2,
      "position": [250, 300],
      "parameters": {
        "formTitle": "Contact Us",
        "formFields": {
          "values": [
            { "fieldLabel": "Name", "fieldType": "text", "requiredField": true },
            { "fieldLabel": "Email", "fieldType": "email", "requiredField": true },
            { "fieldLabel": "Type", "fieldType": "dropdown", "fieldOptions": { "values": [{ "option": "Support" }, { "option": "Sales" }, { "option": "Other" }] } },
            { "fieldLabel": "Message", "fieldType": "textarea", "requiredField": true }
          ]
        }
      },
      "webhookId": "form-001"
    },
    {
      "id": "route-1",
      "name": "Route by Type",
      "type": "n8n-nodes-base.switch",
      "typeVersion": 3.2,
      "position": [500, 300],
      "parameters": {
        "rules": {
          "rules": [
            {
              "conditions": {
                "options": { "combinator": "and" },
                "conditions": [{ "leftValue": "={{ $json.Type }}", "rightValue": "Support", "operator": { "type": "string", "operation": "equals" } }]
              },
              "output": 0
            },
            {
              "conditions": {
                "options": { "combinator": "and" },
                "conditions": [{ "leftValue": "={{ $json.Type }}", "rightValue": "Sales", "operator": { "type": "string", "operation": "equals" } }]
              },
              "output": 1
            }
          ]
        },
        "options": { "fallbackOutput": "extra" }
      }
    },
    {
      "id": "support-1",
      "name": "Notify Support Team",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2,
      "position": [750, 200],
      "parameters": {
        "resource": "message",
        "operation": "sendMessage",
        "channel": { "__rl": true, "value": "#support", "mode": "name" },
        "text": "=New support request from {{ $json.Name }} ({{ $json.Email }}):\n{{ $json.Message }}"
      }
    },
    {
      "id": "sales-1",
      "name": "Notify Sales Team",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2,
      "position": [750, 400],
      "parameters": {
        "resource": "message",
        "operation": "sendMessage",
        "channel": { "__rl": true, "value": "#sales", "mode": "name" },
        "text": "=New sales inquiry from {{ $json.Name }} ({{ $json.Email }}):\n{{ $json.Message }}"
      }
    }
  ],
  "connections": {
    "Contact Form": { "main": [[{ "node": "Route by Type", "type": "main", "index": 0 }]] },
    "Route by Type": {
      "main": [
        [{ "node": "Notify Support Team", "type": "main", "index": 0 }],
        [{ "node": "Notify Sales Team", "type": "main", "index": 0 }]
      ]
    }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Pattern 4: Error-Resilient API Pipeline {#pattern-4}

**Use case**: API call with retry logic, error notification, and fallback.

Key additions to any node for resilience:
```json
{
  "onError": "continueRegularOutput",
  "retryOnFail": true,
  "maxTries": 3,
  "waitBetweenTries": 2000
}
```

Pair with an Error Trigger workflow:
```json
{
  "name": "Error Handler",
  "nodes": [
    {
      "name": "Error Trigger",
      "type": "n8n-nodes-base.errorTrigger",
      "typeVersion": 1,
      "position": [250, 300],
      "parameters": {}
    },
    {
      "name": "Alert Slack",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2,
      "position": [500, 300],
      "parameters": {
        "resource": "message",
        "operation": "sendMessage",
        "channel": { "__rl": true, "value": "#alerts", "mode": "name" },
        "text": "=🚨 Workflow Error!\nWorkflow: {{ $json.workflow.name }}\nNode: {{ $json.execution.lastNodeExecuted }}\nError: {{ $json.execution.error.message }}"
      }
    }
  ],
  "connections": {
    "Error Trigger": { "main": [[{ "node": "Alert Slack", "type": "main", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Pattern 6: AI Agent with Tools {#pattern-6}

**Use case**: Conversational AI with HTTP tool access and memory.

Full JSON provided in SKILL.md Section 7. Key architecture:

```
Chat Trigger → AI Agent ← OpenAI Model (ai_languageModel)
                       ← HTTP Tool (ai_tool)
                       ← Code Tool (ai_tool)
                       ← Memory (ai_memory)
```

### Adding a Code Tool to AI Agent

```json
{
  "name": "Code Tool",
  "type": "@n8n/n8n-nodes-langchain.toolCode",
  "typeVersion": 1.1,
  "position": [800, 500],
  "parameters": {
    "name": "calculator",
    "description": "Performs mathematical calculations. Input should be a math expression.",
    "jsCode": "const math = require('mathjs');\nconst result = math.evaluate(query);\nreturn String(result);"
  }
}
```

Connection: `"ai_tool": [[{ "node": "AI Agent", "type": "ai_tool", "index": 0 }]]`

### Adding a Workflow Tool

```json
{
  "name": "Lookup Tool",
  "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
  "typeVersion": 1.2,
  "position": [600, 500],
  "parameters": {
    "name": "lookup_customer",
    "description": "Look up customer information by email address",
    "workflowId": "sub-workflow-id"
  }
}
```

---

## Pattern 9: Batch Processing Loop {#pattern-9}

**Use case**: Process large datasets in batches to avoid rate limits.

```json
{
  "name": "Batch Processor",
  "nodes": [
    {
      "name": "Get All Records",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [250, 300],
      "parameters": {
        "url": "https://api.example.com/records",
        "method": "GET"
      }
    },
    {
      "name": "Loop Over Items",
      "type": "n8n-nodes-base.splitInBatches",
      "typeVersion": 3,
      "position": [500, 300],
      "parameters": {
        "batchSize": 10,
        "options": {}
      }
    },
    {
      "name": "Process Batch",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [750, 300],
      "parameters": {
        "url": "https://api.example.com/process",
        "method": "POST",
        "sendBody": true,
        "contentType": "json",
        "bodyParametersJson": "={{ JSON.stringify($json) }}"
      }
    },
    {
      "name": "Wait",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1.1,
      "position": [1000, 300],
      "parameters": {
        "amount": 1,
        "unit": "seconds"
      }
    }
  ],
  "connections": {
    "Get All Records": { "main": [[{ "node": "Loop Over Items", "type": "main", "index": 0 }]] },
    "Loop Over Items": { "main": [[{ "node": "Process Batch", "type": "main", "index": 0 }]] },
    "Process Batch": { "main": [[{ "node": "Wait", "type": "main", "index": 0 }]] },
    "Wait": { "main": [[{ "node": "Loop Over Items", "type": "main", "index": 0 }]] }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Pattern 15: Approval Workflow {#pattern-15}

**Use case**: Human-in-the-loop approval before executing an action.

```json
{
  "name": "Approval Workflow",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [250, 300],
      "parameters": {
        "path": "request-approval",
        "httpMethod": "POST",
        "responseMode": "responseNode"
      },
      "webhookId": "approval-001"
    },
    {
      "name": "Send Approval Request",
      "type": "n8n-nodes-base.slack",
      "typeVersion": 2.2,
      "position": [500, 300],
      "parameters": {
        "resource": "message",
        "operation": "sendMessage",
        "channel": { "__rl": true, "value": "#approvals", "mode": "name" },
        "text": "=🔔 Approval needed!\nRequest: {{ $json.body.description }}\nApprove: {{ $env.N8N_URL }}/webhook/approve?id={{ $json.body.requestId }}\nDeny: {{ $env.N8N_URL }}/webhook/deny?id={{ $json.body.requestId }}"
      }
    },
    {
      "name": "Wait for Approval",
      "type": "n8n-nodes-base.wait",
      "typeVersion": 1.1,
      "position": [750, 300],
      "parameters": {
        "resume": "webhook",
        "options": {
          "webhookSuffix": "={{ $json.body.requestId }}"
        }
      }
    },
    {
      "name": "Check Decision",
      "type": "n8n-nodes-base.if",
      "typeVersion": 2.2,
      "position": [1000, 300],
      "parameters": {
        "conditions": {
          "options": { "combinator": "and" },
          "conditions": [{
            "leftValue": "={{ $json.query.decision }}",
            "rightValue": "approved",
            "operator": { "type": "string", "operation": "equals" }
          }]
        }
      }
    },
    {
      "name": "Execute Action",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1250, 200],
      "parameters": {
        "jsCode": "return [{ json: { status: 'approved', executedAt: new Date().toISOString() } }];"
      }
    },
    {
      "name": "Notify Denied",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [1250, 400],
      "parameters": {
        "jsCode": "return [{ json: { status: 'denied', deniedAt: new Date().toISOString() } }];"
      }
    }
  ],
  "connections": {
    "Webhook": { "main": [[{ "node": "Send Approval Request", "type": "main", "index": 0 }]] },
    "Send Approval Request": { "main": [[{ "node": "Wait for Approval", "type": "main", "index": 0 }]] },
    "Wait for Approval": { "main": [[{ "node": "Check Decision", "type": "main", "index": 0 }]] },
    "Check Decision": {
      "main": [
        [{ "node": "Execute Action", "type": "main", "index": 0 }],
        [{ "node": "Notify Denied", "type": "main", "index": 0 }]
      ]
    }
  },
  "settings": { "executionOrder": "v1" }
}
```

---

## Workflow Building Checklist

When generating any workflow JSON:

1. ✅ `executionOrder: "v1"` in settings
2. ✅ Exactly one trigger node
3. ✅ All node names are unique strings
4. ✅ All node IDs are unique UUIDs
5. ✅ Connections reference nodes by NAME (not ID)
6. ✅ Use `n8n-nodes-base.` prefix (NOT `nodes-base.`)
7. ✅ Use `@n8n/n8n-nodes-langchain.` for AI nodes
8. ✅ AI connections use correct type (ai_languageModel, ai_tool, etc.)
9. ✅ Webhook data accessed via `.body` in expressions
10. ✅ Code nodes return `[{ json: {...} }]`
11. ✅ Position coordinates prevent node overlap
12. ✅ Credential references include both `id` and `name`
