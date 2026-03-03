# n8n Workflow Mastery — OpenClaw Skill

An open-source AI agent skill for building, deploying, and managing n8n workflows programmatically. Built for [OpenClaw](https://github.com/openclaw/openclaw).

## What This Does

Give your AI agent full control over n8n. It can design, build, validate, deploy, debug, and monitor workflows through the n8n REST API — no manual clicking required.

**Capabilities:**
- 🏗️ **Build** — Scaffold and create complete workflows from natural language descriptions
- ✅ **Validate** — Catch errors before deployment with automated validation
- 🚀 **Deploy** — Push workflows to n8n, test, and activate
- 🔧 **Debug** — Diagnose failed executions and fix broken nodes
- 📊 **Monitor** — Check execution status and performance

## Quick Start

### Install via ClawHub
```bash
clawhub install n8n-workflow-mastery
```

### Manual Install
1. Copy the `SKILL.md`, `references/`, and `scripts/` directories into your OpenClaw skills folder
2. Set your n8n API key:
```bash
mkdir -p ~/.openclaw/credentials
echo "your-n8n-api-key" > ~/.openclaw/credentials/n8n
```

### Usage
Just ask your agent to build n8n workflows:
- "Build an n8n workflow that reads leads from Google Sheets and sends personalized emails"
- "Debug my workflow — execution ID abc123 failed"
- "Add error handling to my existing workflow"

## What's Included

### SKILL.md
The main skill file. Contains the build loop protocol, node configuration patterns, and the complete instruction set for the AI agent.

### references/
Deep-dive reference docs the agent reads as needed:

| File | What It Covers |
|------|---------------|
| `API_REFERENCE.md` | Full REST API — endpoints, auth, pagination, webhooks |
| `NODE_CATALOG.md` | Every node type with configs and property dependencies |
| `PATTERNS_LIBRARY.md` | 20+ copy-paste workflow JSON patterns |
| `TROUBLESHOOTING.md` | Error recovery playbooks in decision-tree format |
| `MCP_INTEGRATION.md` | MCP server/client setup and multi-agent patterns |
| `EXPRESSION_COOKBOOK.md` | 80+ ready-to-use expressions for dates, strings, arrays, JSON |
| `CREDENTIAL_TYPES.md` | Every credential type string and required fields |

### scripts/
Python utilities for the build pipeline:

| Script | Purpose |
|--------|---------|
| `validate_workflow.py` | Validates workflow JSON before deployment |
| `scaffold_workflow.py` | Generates base workflow JSON from a spec |
| `deploy_workflow.py` | Full pipeline: validate → create → test → activate |

## Build Loop Protocol

Every workflow the agent creates follows this loop:

```
1. SCAFFOLD → Generate base JSON
2. CUSTOMIZE → Add business logic, expressions, credentials
3. VALIDATE → Run validation (catches errors before API calls)
4. DEPLOY INACTIVE → Create via API
5. TEST → Execute and verify
6. FIX → If errors, fix → re-validate → re-deploy
7. ACTIVATE → Only after successful test
```

## Requirements

- n8n instance (self-hosted or cloud) with API access
- n8n API key (Settings → API → Create API Key)
- Python 3.8+ (for validation/deploy scripts)
- [OpenClaw](https://github.com/openclaw/openclaw) (or any AI agent platform that supports skill files)

## License

MIT

## Credits

Built by [Otter Labs](https://github.com/jslizar) for use with OpenClaw.
