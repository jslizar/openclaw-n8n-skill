# n8n Node Catalog & Configuration Reference

## Table of Contents
1. [Node Type Naming Convention](#naming)
2. [Trigger Nodes (Complete)](#triggers)
3. [Core Processing Nodes (Complete)](#core)
4. [HTTP & API Nodes](#http)
5. [Database Nodes](#database)
6. [Service Integration Nodes](#services)
7. [AI/LangChain Nodes](#ai-nodes)
8. [Property Dependency Rules](#dependencies)
9. [Node Version Guide](#versions)

---

## Node Type Naming Convention {#naming}

### In Workflow JSON (Creating/Updating Workflows)
```
n8n-nodes-base.<nodeName>           → Standard nodes
@n8n/n8n-nodes-langchain.<nodeName> → AI/LangChain nodes
```

### In MCP Tools (Searching/Validating)
```
nodes-base.<nodeName>               → Standard nodes
nodes-langchain.<nodeName>          → AI/LangChain nodes
```

### Common Node Type Mappings
| Node | Workflow JSON Type | MCP Type |
|------|-------------------|----------|
| Webhook | `n8n-nodes-base.webhook` | `nodes-base.webhook` |
| HTTP Request | `n8n-nodes-base.httpRequest` | `nodes-base.httpRequest` |
| Code | `n8n-nodes-base.code` | `nodes-base.code` |
| Slack | `n8n-nodes-base.slack` | `nodes-base.slack` |
| IF | `n8n-nodes-base.if` | `nodes-base.if` |
| AI Agent | `@n8n/n8n-nodes-langchain.agent` | `nodes-langchain.agent` |
| Chat Trigger | `@n8n/n8n-nodes-langchain.chatTrigger` | `nodes-langchain.chatTrigger` |
| OpenAI Model | `@n8n/n8n-nodes-langchain.lmChatOpenAi` | `nodes-langchain.lmChatOpenAi` |

---

## Trigger Nodes {#triggers}

Every workflow MUST start with exactly one trigger node.

### Webhook Trigger
```json
{
  "type": "n8n-nodes-base.webhook",
  "typeVersion": 2,
  "parameters": {
    "path": "unique-path",
    "httpMethod": "POST",
    "responseMode": "lastNode",
    "options": {
      "responseHeaders": {
        "entries": [{ "name": "X-Custom", "value": "value" }]
      }
    }
  }
}
```
**responseMode options**: `lastNode`, `responseNode`, `immediately`

### Schedule Trigger
```json
{
  "type": "n8n-nodes-base.scheduleTrigger",
  "typeVersion": 1.2,
  "parameters": {
    "rule": {
      "interval": [{
        "field": "cronExpression",
        "expression": "0 9 * * 1-5"
      }]
    }
  }
}
```
**Cron format**: minute hour day-of-month month day-of-week

### Form Trigger
```json
{
  "type": "n8n-nodes-base.formTrigger",
  "typeVersion": 2.2,
  "parameters": {
    "formTitle": "My Form",
    "formDescription": "Please fill in",
    "formFields": {
      "values": [
        {
          "fieldLabel": "Name",
          "fieldType": "text",
          "requiredField": true,
          "placeholder": "Enter name"
        },
        {
          "fieldLabel": "Priority",
          "fieldType": "dropdown",
          "fieldOptions": {
            "values": [
              { "option": "Low" },
              { "option": "Medium" },
              { "option": "High" }
            ]
          }
        }
      ]
    }
  }
}
```
**fieldType options**: `text`, `textarea`, `number`, `email`, `dropdown`, `date`

### Chat Trigger (AI)
```json
{
  "type": "@n8n/n8n-nodes-langchain.chatTrigger",
  "typeVersion": 1.1,
  "parameters": {
    "options": {
      "title": "My AI Chat",
      "subtitle": "Ask me anything",
      "allowedFilesMimeTypes": "image/*,application/pdf"
    }
  }
}
```

### Manual Trigger
```json
{
  "type": "n8n-nodes-base.manualTrigger",
  "typeVersion": 1,
  "parameters": {}
}
```

### Email Trigger (IMAP)
```json
{
  "type": "n8n-nodes-base.emailimap",
  "typeVersion": 2,
  "parameters": {
    "mailbox": "INBOX",
    "options": {
      "customEmailHeaders": true,
      "unseen": true
    }
  }
}
```

---

## Core Processing Nodes {#core}

### Edit Fields (Set)
```json
{
  "type": "n8n-nodes-base.set",
  "typeVersion": 3.4,
  "parameters": {
    "mode": "manual",
    "assignments": {
      "assignments": [
        { "id": "uuid1", "name": "fullName", "value": "={{ $json.firstName }} {{ $json.lastName }}", "type": "string" },
        { "id": "uuid2", "name": "isActive", "value": true, "type": "boolean" },
        { "id": "uuid3", "name": "score", "value": "={{ $json.points * 10 }}", "type": "number" }
      ]
    }
  }
}
```

### IF (Conditional)
```json
{
  "type": "n8n-nodes-base.if",
  "typeVersion": 2.2,
  "parameters": {
    "conditions": {
      "options": { "combinator": "and" },
      "conditions": [
        {
          "id": "uuid",
          "leftValue": "={{ $json.status }}",
          "rightValue": "active",
          "operator": { "type": "string", "operation": "equals" }
        }
      ]
    }
  }
}
```
**Outputs**: index 0 = true, index 1 = false

**Operator types**:
- string: equals, notEquals, contains, notContains, startsWith, endsWith, regex, isEmpty
- number: equals, notEquals, gt, gte, lt, lte
- boolean: true, false
- dateTime: after, before

### Switch (Multi-Branch)
```json
{
  "type": "n8n-nodes-base.switch",
  "typeVersion": 3.2,
  "parameters": {
    "rules": {
      "rules": [
        {
          "conditions": {
            "options": { "combinator": "and" },
            "conditions": [{
              "leftValue": "={{ $json.type }}",
              "rightValue": "email",
              "operator": { "type": "string", "operation": "equals" }
            }]
          },
          "output": 0
        },
        {
          "conditions": {
            "options": { "combinator": "and" },
            "conditions": [{
              "leftValue": "={{ $json.type }}",
              "rightValue": "sms",
              "operator": { "type": "string", "operation": "equals" }
            }]
          },
          "output": 1
        }
      ]
    },
    "options": { "fallbackOutput": "extra" }
  }
}
```

### Merge
```json
{
  "type": "n8n-nodes-base.merge",
  "typeVersion": 3,
  "parameters": {
    "mode": "combine",
    "combineBy": "combineByPosition",
    "options": {}
  }
}
```
**Modes**: `append` (concat), `combine` (merge by position/field), `chooseBranch`

### Filter
```json
{
  "type": "n8n-nodes-base.filter",
  "typeVersion": 2.2,
  "parameters": {
    "conditions": {
      "options": { "combinator": "and" },
      "conditions": [{
        "leftValue": "={{ $json.age }}",
        "rightValue": 18,
        "operator": { "type": "number", "operation": "gte" }
      }]
    }
  }
}
```

---

## HTTP & API Nodes {#http}

### HTTP Request (Full Configuration)
```json
{
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "parameters": {
    "url": "https://api.example.com/endpoint",
    "method": "POST",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "httpHeaderAuth",
    "sendBody": true,
    "contentType": "json",
    "bodyParametersJson": "={{ JSON.stringify({ key: $json.value }) }}",
    "sendQuery": true,
    "queryParameters": {
      "parameters": [
        { "name": "page", "value": "1" },
        { "name": "limit", "value": "100" }
      ]
    },
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        { "name": "Accept", "value": "application/json" }
      ]
    },
    "options": {
      "timeout": 30000,
      "response": { "response": { "fullResponse": true } },
      "redirect": { "redirect": { "followRedirects": true } }
    }
  }
}
```

### Property Dependencies for HTTP Request
- `sendBody: true` → REQUIRES `contentType`
- `contentType: "json"` → Use `bodyParametersJson` or `bodyParameters`
- `contentType: "form-urlencoded"` → Use `bodyParameters`
- `contentType: "raw"` → Use `body`
- `authentication: "predefinedCredentialType"` → REQUIRES `nodeCredentialType`
- `authentication: "genericCredentialType"` → REQUIRES `genericAuthType`

---

## AI/LangChain Nodes {#ai-nodes}

### Connection Type Map
| Sub-Node Category | Connection Type |
|-------------------|----------------|
| Language Models | `ai_languageModel` |
| Chat Models | `ai_languageModel` |
| Tools | `ai_tool` |
| Memory | `ai_memory` |
| Output Parsers | `ai_outputParser` |
| Retrievers | `ai_retriever` |
| Embeddings | `ai_embedding` |
| Document Loaders | `ai_document` |
| Text Splitters | `ai_textSplitter` |

### AI Agent Node
```json
{
  "type": "@n8n/n8n-nodes-langchain.agent",
  "typeVersion": 1.7,
  "parameters": {
    "options": {
      "systemMessage": "You are a helpful assistant.",
      "maxIterations": 10,
      "returnIntermediateSteps": false
    }
  }
}
```
**Required connections**: `ai_languageModel` (exactly 1)
**Optional connections**: `ai_tool` (0+), `ai_memory` (0-1), `ai_outputParser` (0-1)

---

## Property Dependency Rules {#dependencies}

### How Dependencies Work
Many node properties are conditional — they only appear/apply when another
property has a specific value. This is the `displayOptions` system.

### Critical Dependencies by Node

#### HTTP Request
| When You Set | You Must Also Set |
|-------------|-------------------|
| `sendBody: true` | `contentType` |
| `contentType: "json"` | `bodyParametersJson` or `bodyParameters.parameters` |
| `sendQuery: true` | `queryParameters.parameters` |
| `sendHeaders: true` | `headerParameters.parameters` |
| `authentication: "predefinedCredentialType"` | `nodeCredentialType` + credential |

#### IF Node
| When You Set | You Must Also Set |
|-------------|-------------------|
| conditions.conditions[] | `leftValue`, `operator`, and usually `rightValue` |
| operator.type: "string" | operator.operation (equals, contains, etc.) |

#### Code Node
| When You Set | Effect |
|-------------|--------|
| `mode: "runOnceForAllItems"` | Use `$input.all()` |
| `mode: "runOnceForEachItem"` | Use `$input.item` |
| `language: "javaScript"` | Write in `jsCode` parameter |
| `language: "python"` | Write in `pythonCode` parameter |

#### Slack Node
| When You Set | You Must Also Set |
|-------------|-------------------|
| `resource: "message"` | `operation` (sendMessage, etc.) |
| `operation: "sendMessage"` | `channel`, `text` |
| `operation: "update"` | `channel`, `ts`, `text` |

---

## Node Version Guide {#versions}

Always use the latest stable version. Key current versions:

| Node | Recommended Version |
|------|-------------------|
| webhook | 2 |
| httpRequest | 4.2 |
| code | 2 |
| if | 2.2 |
| switch | 3.2 |
| set (Edit Fields) | 3.4 |
| merge | 3 |
| filter | 2.2 |
| scheduleTrigger | 1.2 |
| formTrigger | 2.2 |
| splitInBatches | 3 |
| slack | 2.2 |
| gmail | 2.1 |
| googleSheets | 4.5 |
| agent (AI) | 1.7 |
| chatTrigger | 1.1 |
| lmChatOpenAi | 1.2 |
| lmChatAnthropic | 1.3 |
| memoryBufferWindow | 1.3 |
| respondToWebhook | 1.1 |

**NOTE**: Versions change with n8n updates. When in doubt, check the n8n docs
or use search_nodes MCP tool to find current versions.
