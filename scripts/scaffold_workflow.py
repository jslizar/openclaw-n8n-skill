#!/usr/bin/env python3
"""
n8n Workflow Scaffold Generator v2.0
=====================================
Generates structurally valid n8n workflow JSON from a simple specification.
Eliminates prefix errors, missing fields, and connection mistakes.

Usage:
    python scaffold_workflow.py --name "My API" --trigger webhook --nodes code,slack
    python scaffold_workflow.py --name "Daily Report" --trigger schedule --nodes httpRequest,code,gmail
    python scaffold_workflow.py --name "AI Agent" --trigger chat --ai-agent --tools httpRequest,code
    python scaffold_workflow.py --spec spec.json

Spec JSON format:
{
    "name": "Workflow Name",
    "trigger": "webhook|schedule|form|manual|chat|error|executeWorkflow",
    "nodes": ["code", "httpRequest", "slack", "gmail", ...],
    "ai_agent": false,
    "ai_tools": ["httpRequest", "code"],
    "ai_model": "openai",
    "ai_memory": "bufferWindow",
    "config_node": true,
    "error_handling": true
}
"""

import json
import sys
import uuid
import argparse

# ============================================================================
# NODE TEMPLATES
# ============================================================================

def uid():
    return str(uuid.uuid4())

X_START = 250
X_STEP = 250
Y_CENTER = 300
Y_AI_OFFSET = 150

# Trigger templates
TRIGGERS = {
    "webhook": {
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "parameters": {
            "path": "={{$workflow.id}}",
            "httpMethod": "POST",
            "responseMode": "responseNode",
            "options": {}
        },
        "webhookId": None  # Auto-generated
    },
    "webhook_simple": {
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "parameters": {
            "path": "={{$workflow.id}}",
            "httpMethod": "POST",
            "responseMode": "lastNode",
            "options": {}
        },
        "webhookId": None
    },
    "schedule": {
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.2,
        "parameters": {
            "rule": {
                "interval": [{"field": "hours", "hoursInterval": 1}]
            }
        }
    },
    "form": {
        "type": "n8n-nodes-base.formTrigger",
        "typeVersion": 2.2,
        "parameters": {
            "path": "={{$workflow.id}}",
            "formTitle": "Form",
            "formFields": {
                "values": [
                    {"fieldLabel": "Name", "fieldType": "text", "requiredField": True},
                    {"fieldLabel": "Email", "fieldType": "email", "requiredField": True}
                ]
            },
            "options": {}
        },
        "webhookId": None
    },
    "manual": {
        "type": "n8n-nodes-base.manualTrigger",
        "typeVersion": 1,
        "parameters": {}
    },
    "chat": {
        "type": "@n8n/n8n-nodes-langchain.chatTrigger",
        "typeVersion": 1.1,
        "parameters": {
            "options": {}
        },
        "webhookId": None
    },
    "error": {
        "type": "n8n-nodes-base.errorTrigger",
        "typeVersion": 1,
        "parameters": {}
    },
    "executeWorkflow": {
        "type": "n8n-nodes-base.executeWorkflowTrigger",
        "typeVersion": 1.1,
        "parameters": {}
    }
}

# Processing node templates
NODE_TEMPLATES = {
    "code": {
        "type": "n8n-nodes-base.code",
        "typeVersion": 2,
        "parameters": {
            "jsCode": "// Process each item\nconst items = $input.all();\nconst results = [];\n\nfor (const item of items) {\n  results.push({\n    json: {\n      ...item.json,\n      processed: true,\n      timestamp: new Date().toISOString()\n    }\n  });\n}\n\nreturn results;"
        }
    },
    "httpRequest": {
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "GET",
            "options": {}
        }
    },
    "set": {
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "parameters": {
            "mode": "manual",
            "duplicateItem": False,
            "assignments": {
                "assignments": [
                    {"id": uid(), "name": "field_name", "value": "={{ $json.input_field }}", "type": "string"}
                ]
            },
            "options": {}
        }
    },
    "if": {
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": ""},
                "conditions": [
                    {
                        "id": uid(),
                        "leftValue": "={{ $json.field }}",
                        "rightValue": "",
                        "operator": {"type": "string", "operation": "isNotEmpty"}
                    }
                ],
                "combinator": "and"
            },
            "options": {}
        }
    },
    "switch": {
        "type": "n8n-nodes-base.switch",
        "typeVersion": 3.2,
        "parameters": {
            "rules": {
                "values": [
                    {"outputKey": "case1", "conditions": {"conditions": [{"leftValue": "={{ $json.type }}", "rightValue": "typeA", "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"}},
                    {"outputKey": "case2", "conditions": {"conditions": [{"leftValue": "={{ $json.type }}", "rightValue": "typeB", "operator": {"type": "string", "operation": "equals"}}], "combinator": "and"}}
                ]
            },
            "options": {}
        }
    },
    "merge": {
        "type": "n8n-nodes-base.merge",
        "typeVersion": 3,
        "parameters": {"mode": "combine", "combinationMode": "mergeByPosition"}
    },
    "slack": {
        "type": "n8n-nodes-base.slack",
        "typeVersion": 2.2,
        "parameters": {
            "resource": "message",
            "operation": "send",
            "channel": {"__rl": True, "value": "#general", "mode": "name"},
            "text": "={{ $json.message }}",
            "otherOptions": {}
        },
        "credentials": {"slackApi": {"id": "CREDENTIAL_ID", "name": "Slack"}}
    },
    "gmail": {
        "type": "n8n-nodes-base.gmail",
        "typeVersion": 2.1,
        "parameters": {
            "resource": "message",
            "operation": "send",
            "sendTo": "recipient@example.com",
            "subject": "Notification",
            "message": "={{ $json.body }}",
            "options": {}
        },
        "credentials": {"gmailOAuth2": {"id": "CREDENTIAL_ID", "name": "Gmail"}}
    },
    "googleSheets": {
        "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.5,
        "parameters": {
            "operation": "appendOrUpdate",
            "documentId": {"__rl": True, "value": "SHEET_ID", "mode": "id"},
            "sheetName": {"__rl": True, "value": "Sheet1", "mode": "name"},
            "options": {}
        },
        "credentials": {"googleSheetsOAuth2Api": {"id": "CREDENTIAL_ID", "name": "Google Sheets"}}
    },
    "postgres": {
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "parameters": {
            "operation": "executeQuery",
            "query": "SELECT * FROM table_name LIMIT 100",
            "options": {}
        },
        "credentials": {"postgres": {"id": "CREDENTIAL_ID", "name": "Postgres"}}
    },
    "respondToWebhook": {
        "type": "n8n-nodes-base.respondToWebhook",
        "typeVersion": 1.1,
        "parameters": {
            "respondWith": "json",
            "responseBody": "={{ JSON.stringify({ success: true, data: $json }) }}",
            "options": {}
        }
    },
    "filter": {
        "type": "n8n-nodes-base.filter",
        "typeVersion": 2,
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True},
                "conditions": [
                    {"leftValue": "={{ $json.field }}", "rightValue": "", "operator": {"type": "string", "operation": "isNotEmpty"}}
                ],
                "combinator": "and"
            },
            "options": {}
        }
    },
    "wait": {
        "type": "n8n-nodes-base.wait",
        "typeVersion": 1.1,
        "parameters": {"amount": 1, "unit": "seconds"},
        "webhookId": None
    },
    "noOp": {
        "type": "n8n-nodes-base.noOp",
        "typeVersion": 1,
        "parameters": {}
    },
    "executeWorkflow": {
        "type": "n8n-nodes-base.executeWorkflow",
        "typeVersion": 1.2,
        "parameters": {
            "source": "database",
            "workflowId": "={{ $workflow.id }}",
            "options": {}
        }
    },
    "aggregate": {
        "type": "n8n-nodes-base.aggregate",
        "typeVersion": 1,
        "parameters": {
            "aggregate": "aggregateAllItemData",
            "options": {}
        }
    }
}

# AI node templates
AI_TEMPLATES = {
    "agent": {
        "type": "@n8n/n8n-nodes-langchain.agent",
        "typeVersion": 1.7,
        "parameters": {
            "options": {
                "maxIterations": 10,
                "returnIntermediateSteps": False
            }
        }
    },
    "openai": {
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1.2,
        "parameters": {
            "model": "gpt-4o",
            "options": {"temperature": 0.7}
        },
        "credentials": {"openAiApi": {"id": "CREDENTIAL_ID", "name": "OpenAI"}}
    },
    "anthropic": {
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "parameters": {
            "model": "claude-sonnet-4-20250514",
            "options": {"temperature": 0.7}
        },
        "credentials": {"anthropicApi": {"id": "CREDENTIAL_ID", "name": "Anthropic"}}
    },
    "httpTool": {
        "type": "@n8n/n8n-nodes-langchain.toolHttpRequest",
        "typeVersion": 1.1,
        "parameters": {
            "url": "https://api.example.com/data",
            "method": "GET",
            "description": "Fetches data from the API",
            "options": {}
        }
    },
    "codeTool": {
        "type": "@n8n/n8n-nodes-langchain.toolCode",
        "typeVersion": 1.1,
        "parameters": {
            "name": "custom_tool",
            "description": "Custom tool description",
            "jsCode": "// Tool code\nreturn { result: 'data' };"
        }
    },
    "workflowTool": {
        "type": "@n8n/n8n-nodes-langchain.toolWorkflow",
        "typeVersion": 2,
        "parameters": {
            "name": "sub_workflow",
            "description": "Executes a sub-workflow",
            "source": "database",
            "workflowId": "={{ $workflow.id }}"
        }
    },
    "bufferWindow": {
        "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
        "typeVersion": 1.3,
        "parameters": {"sessionIdType": "customKey", "sessionKey": "={{ $json.sessionId }}"}
    },
    "postgresMemory": {
        "type": "@n8n/n8n-nodes-langchain.memoryPostgresChat",
        "typeVersion": 1.3,
        "parameters": {"sessionIdType": "customKey", "sessionKey": "={{ $json.sessionId }}"},
        "credentials": {"postgres": {"id": "CREDENTIAL_ID", "name": "Postgres"}}
    },
    "structuredOutput": {
        "type": "@n8n/n8n-nodes-langchain.outputParserStructured",
        "typeVersion": 1.2,
        "parameters": {
            "schemaType": "fromJson",
            "jsonSchemaExample": "{\n  \"result\": \"string\",\n  \"confidence\": 0.95\n}"
        }
    },
    "thinkTool": {
        "type": "@n8n/n8n-nodes-langchain.toolThink",
        "typeVersion": 1,
        "parameters": {}
    }
}

# Config node for production workflows
CONFIG_NODE = {
    "type": "n8n-nodes-base.set",
    "typeVersion": 3.4,
    "parameters": {
        "mode": "manual",
        "duplicateItem": False,
        "assignments": {
            "assignments": [
                {"id": uid(), "name": "config.env", "value": "production", "type": "string"},
                {"id": uid(), "name": "config.batchSize", "value": "100", "type": "number"},
                {"id": uid(), "name": "config.retryAttempts", "value": "3", "type": "number"},
                {"id": uid(), "name": "config.dryRun", "value": "false", "type": "boolean"},
                {"id": uid(), "name": "config.alertChannel", "value": "#ops-alerts", "type": "string"}
            ]
        },
        "options": {}
    }
}


# ============================================================================
# SCAFFOLD BUILDER
# ============================================================================

def build_workflow(spec: dict) -> dict:
    """Build a complete workflow from a specification."""
    name = spec.get("name", "New Workflow")
    trigger_type = spec.get("trigger", "manual")
    node_list = spec.get("nodes", [])
    has_ai = spec.get("ai_agent", False)
    ai_tools = spec.get("ai_tools", [])
    ai_model = spec.get("ai_model", "openai")
    ai_memory = spec.get("ai_memory", None)
    add_config = spec.get("config_node", False)
    add_error = spec.get("error_handling", False)

    nodes = []
    connections = {}
    x_pos = X_START
    prev_node_name = None

    # 1. Trigger node
    trigger_name = _trigger_display_name(trigger_type)
    trigger_template = TRIGGERS.get(trigger_type, TRIGGERS["manual"])
    trigger_node = _make_node(trigger_name, trigger_template, x_pos, Y_CENTER)
    nodes.append(trigger_node)
    prev_node_name = trigger_name
    x_pos += X_STEP

    # 2. Config node (optional)
    if add_config:
        config_name = "Config"
        config_node = _make_node(config_name, CONFIG_NODE, x_pos, Y_CENTER)
        nodes.append(config_node)
        _connect(connections, prev_node_name, config_name)
        prev_node_name = config_name
        x_pos += X_STEP

    # 3. AI Agent path
    if has_ai:
        # Agent node
        agent_name = "AI Agent"
        agent_node = _make_node(agent_name, AI_TEMPLATES["agent"], x_pos, Y_CENTER)
        nodes.append(agent_node)
        _connect(connections, prev_node_name, agent_name)
        prev_node_name = agent_name

        # Model (connected via ai_languageModel)
        model_name = f"{ai_model.title()} Model"
        model_template = AI_TEMPLATES.get(ai_model, AI_TEMPLATES["openai"])
        model_node = _make_node(model_name, model_template, x_pos - 100, Y_CENTER + Y_AI_OFFSET)
        nodes.append(model_node)
        _connect_ai(connections, model_name, agent_name, "ai_languageModel")

        # Memory (connected via ai_memory)
        if ai_memory:
            mem_name = "Memory"
            mem_template = AI_TEMPLATES.get(ai_memory, AI_TEMPLATES["bufferWindow"])
            mem_node = _make_node(mem_name, mem_template, x_pos, Y_CENTER + Y_AI_OFFSET)
            nodes.append(mem_node)
            _connect_ai(connections, mem_name, agent_name, "ai_memory")

        # AI Tools (connected via ai_tool)
        tool_x = x_pos + 100
        for i, tool_name_key in enumerate(ai_tools):
            t_name = f"Tool: {tool_name_key.title()}"
            t_key = f"{tool_name_key}Tool" if f"{tool_name_key}Tool" in AI_TEMPLATES else tool_name_key
            t_template = AI_TEMPLATES.get(t_key, AI_TEMPLATES.get("httpTool"))
            if t_template:
                t_node = _make_node(t_name, t_template, tool_x + (i * 180), Y_CENTER + Y_AI_OFFSET)
                nodes.append(t_node)
                _connect_ai(connections, t_name, agent_name, "ai_tool")

        x_pos += X_STEP

    # 4. Processing nodes
    for node_key in node_list:
        template = NODE_TEMPLATES.get(node_key)
        if not template:
            continue
        display_name = _display_name(node_key)
        # Avoid duplicate names
        existing_names = {n["name"] for n in nodes}
        if display_name in existing_names:
            display_name = f"{display_name} {len([n for n in existing_names if display_name in n]) + 1}"

        node = _make_node(display_name, template, x_pos, Y_CENTER)
        nodes.append(node)
        _connect(connections, prev_node_name, display_name)
        prev_node_name = display_name
        x_pos += X_STEP

    # 5. Respond to Webhook (if webhook trigger with responseNode)
    if trigger_type == "webhook":
        respond_name = "Respond to Webhook"
        respond_node = _make_node(respond_name, NODE_TEMPLATES["respondToWebhook"], x_pos, Y_CENTER)
        nodes.append(respond_node)
        _connect(connections, prev_node_name, respond_name)
        x_pos += X_STEP

    # 6. Error handling (separate error workflow nodes)
    if add_error:
        error_note = {
            "id": uid(),
            "name": "Error Handling Note",
            "type": "n8n-nodes-base.stickyNote",
            "typeVersion": 1,
            "position": [X_START, Y_CENTER + 250],
            "parameters": {
                "content": "## Error Handling\n\nSet this workflow as the Error Workflow in your main workflow's settings.\n\nOr enable 'Retry On Fail' on individual nodes:\n- retryOnFail: true\n- maxTries: 3\n- waitBetweenTries: 1000"
            }
        }
        nodes.append(error_note)

    workflow = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1"
        }
    }

    return workflow


def _make_node(name: str, template: dict, x: int, y: int) -> dict:
    node = {
        "id": uid(),
        "name": name,
        "type": template["type"],
        "typeVersion": template["typeVersion"],
        "position": [x, y],
        "parameters": template.get("parameters", {})
    }
    if "credentials" in template:
        node["credentials"] = template["credentials"]
    if "webhookId" in template:
        node["webhookId"] = uid()
    return node


def _connect(connections: dict, source: str, target: str, source_output: int = 0, target_input: int = 0):
    """Create a standard 'main' connection."""
    if source not in connections:
        connections[source] = {}
    if "main" not in connections[source]:
        connections[source]["main"] = []
    while len(connections[source]["main"]) <= source_output:
        connections[source]["main"].append([])
    connections[source]["main"][source_output].append({
        "node": target,
        "type": "main",
        "index": target_input
    })


def _connect_ai(connections: dict, source: str, target: str, conn_type: str):
    """Create an AI connection (ai_languageModel, ai_tool, ai_memory, etc.)."""
    if source not in connections:
        connections[source] = {}
    if conn_type not in connections[source]:
        connections[source][conn_type] = []
    if not connections[source][conn_type]:
        connections[source][conn_type].append([])
    connections[source][conn_type][0].append({
        "node": target,
        "type": conn_type,
        "index": 0
    })


def _trigger_display_name(trigger_type: str) -> str:
    names = {
        "webhook": "Webhook",
        "webhook_simple": "Webhook",
        "schedule": "Schedule Trigger",
        "form": "Form Trigger",
        "manual": "Manual Trigger",
        "chat": "Chat Trigger",
        "error": "Error Trigger",
        "executeWorkflow": "Execute Workflow Trigger"
    }
    return names.get(trigger_type, "Trigger")


def _display_name(node_key: str) -> str:
    names = {
        "code": "Transform Data",
        "httpRequest": "HTTP Request",
        "set": "Edit Fields",
        "if": "IF",
        "switch": "Switch",
        "merge": "Merge",
        "slack": "Slack",
        "gmail": "Gmail",
        "googleSheets": "Google Sheets",
        "postgres": "Postgres",
        "respondToWebhook": "Respond to Webhook",
        "filter": "Filter",
        "wait": "Wait",
        "noOp": "No Operation",
        "executeWorkflow": "Execute Sub-workflow",
        "aggregate": "Aggregate"
    }
    return names.get(node_key, node_key.title())


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate n8n workflow scaffold")
    parser.add_argument("--name", default="New Workflow", help="Workflow name")
    parser.add_argument("--trigger", default="manual",
                       choices=list(TRIGGERS.keys()), help="Trigger type")
    parser.add_argument("--nodes", default="", help="Comma-separated node types")
    parser.add_argument("--ai-agent", action="store_true", help="Include AI Agent")
    parser.add_argument("--ai-model", default="openai", choices=["openai", "anthropic"], help="AI model")
    parser.add_argument("--ai-tools", default="", help="Comma-separated AI tools")
    parser.add_argument("--ai-memory", default=None, help="Memory type")
    parser.add_argument("--config", action="store_true", help="Add config node")
    parser.add_argument("--error-handling", action="store_true", help="Add error handling")
    parser.add_argument("--spec", help="Path to spec JSON file")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    if args.spec:
        with open(args.spec) as f:
            spec = json.load(f)
    else:
        spec = {
            "name": args.name,
            "trigger": args.trigger,
            "nodes": [n.strip() for n in args.nodes.split(",") if n.strip()],
            "ai_agent": args.ai_agent,
            "ai_tools": [t.strip() for t in args.ai_tools.split(",") if t.strip()],
            "ai_model": args.ai_model,
            "ai_memory": args.ai_memory,
            "config_node": args.config,
            "error_handling": args.error_handling,
        }

    workflow = build_workflow(spec)
    output = json.dumps(workflow, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Workflow written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
