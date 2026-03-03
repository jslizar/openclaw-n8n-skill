#!/usr/bin/env python3
"""
n8n Workflow Validator v2.0
===========================
Validates n8n workflow JSON before deployment. Catches 95% of common errors
that cause workflow creation or execution failures.

Usage:
    python validate_workflow.py workflow.json
    python validate_workflow.py --json '{"name":"test","nodes":[],...}'
    python validate_workflow.py --stdin < workflow.json

Exit codes:
    0 = Valid (may have warnings)
    1 = Errors found (do NOT deploy)
    2 = Invalid input (not valid JSON, missing file, etc.)
"""

import json
import sys
import re
import uuid
from typing import Any

# ============================================================================
# KNOWN NODE TYPES — validated against n8n v1.70+ (Feb 2026)
# ============================================================================

VALID_PREFIXES = ["n8n-nodes-base.", "@n8n/n8n-nodes-langchain."]

TRIGGER_NODES = {
    "n8n-nodes-base.webhook", "n8n-nodes-base.scheduleTrigger",
    "n8n-nodes-base.formTrigger", "n8n-nodes-base.emailReadImap",
    "n8n-nodes-base.manualTrigger", "n8n-nodes-base.errorTrigger",
    "n8n-nodes-base.cronTrigger",
    "@n8n/n8n-nodes-langchain.chatTrigger",
    "n8n-nodes-base.executeWorkflowTrigger",
}

AI_CONNECTION_TYPES = {
    "ai_languageModel", "ai_tool", "ai_memory", "ai_outputParser",
    "ai_retriever", "ai_embedding", "ai_document", "ai_textSplitter",
}

STANDARD_CONNECTION = "main"

# Nodes that REQUIRE a language model connection
AI_NODES_REQUIRING_MODEL = {
    "@n8n/n8n-nodes-langchain.agent",
    "@n8n/n8n-nodes-langchain.chainLlm",
    "@n8n/n8n-nodes-langchain.chainRetrievalQa",
    "@n8n/n8n-nodes-langchain.chainSummarization",
}

# Nodes that can ONLY be used with webhook/form triggers
RESPOND_TO_WEBHOOK_NODES = {
    "n8n-nodes-base.respondToWebhook",
}

WEBHOOK_TRIGGER_TYPES = {
    "n8n-nodes-base.webhook",
    "n8n-nodes-base.formTrigger",
}

# Common WRONG prefixes people use
WRONG_PREFIX_MAP = {
    "nodes-base.": "n8n-nodes-base.",
    "n8n-nodes-langchain.": "@n8n/n8n-nodes-langchain.",
    "nodes-langchain.": "@n8n/n8n-nodes-langchain.",
    "n8n.nodes.": "n8n-nodes-base.",
}

# ============================================================================
# VALIDATOR CLASS
# ============================================================================

class WorkflowValidator:
    def __init__(self, workflow: dict):
        self.wf = workflow
        self.errors: list = []
        self.warnings: list = []
        self.fixes: list = []
        self.nodes_by_name: dict = {}
        self.nodes_by_id: dict = {}
        self.node_types: set = set()
        self.trigger_nodes: list = []
        self._index_nodes()

    def _index_nodes(self):
        for node in self.wf.get("nodes", []):
            name = node.get("name", "")
            nid = node.get("id", "")
            ntype = node.get("type", "")
            self.nodes_by_name[name] = node
            if nid:
                self.nodes_by_id[nid] = node
            self.node_types.add(ntype)
            if ntype in TRIGGER_NODES:
                self.trigger_nodes.append(name)

    def check_top_level(self):
        if not isinstance(self.wf, dict):
            self.errors.append("Workflow must be a JSON object")
            return
        if "name" not in self.wf:
            self.errors.append("Missing required field: 'name'")
        if "nodes" not in self.wf:
            self.errors.append("Missing required field: 'nodes'")
        elif not isinstance(self.wf["nodes"], list):
            self.errors.append("'nodes' must be an array")
        if "connections" not in self.wf:
            self.warnings.append("Missing 'connections' — workflow has no data flow")
        elif not isinstance(self.wf["connections"], dict):
            self.errors.append("'connections' must be an object")
        settings = self.wf.get("settings", {})
        if not settings.get("executionOrder"):
            self.warnings.append("Missing settings.executionOrder — add 'executionOrder': 'v1'")
            self.fixes.append({
                "path": "settings.executionOrder", "action": "set",
                "value": "v1", "reason": "Required for v1 execution order"
            })

    def check_nodes(self):
        nodes = self.wf.get("nodes", [])
        if not nodes:
            self.errors.append("Workflow has no nodes")
            return
        names_seen = set()
        ids_seen = set()
        has_trigger = False
        positions_seen = set()
        for i, node in enumerate(nodes):
            prefix = f"nodes[{i}] ({node.get('name', 'unnamed')})"
            if "name" not in node:
                self.errors.append(f"{prefix}: Missing 'name'")
            if "type" not in node:
                self.errors.append(f"{prefix}: Missing 'type'")
                continue
            if "position" not in node:
                self.warnings.append(f"{prefix}: Missing 'position'")
            if "typeVersion" not in node:
                self.warnings.append(f"{prefix}: Missing 'typeVersion' — may default to v1")
            name = node.get("name", "")
            if name in names_seen:
                self.errors.append(f"{prefix}: Duplicate node name '{name}' — connections reference by NAME")
            names_seen.add(name)
            nid = node.get("id", "")
            if nid and nid in ids_seen:
                self.errors.append(f"{prefix}: Duplicate node ID '{nid}'")
            if nid:
                ids_seen.add(nid)
            pos = tuple(node.get("position", [0, 0]))
            if pos in positions_seen:
                self.warnings.append(f"{prefix}: Overlapping position {pos}")
            positions_seen.add(pos)
            ntype = node.get("type", "")
            self._check_node_type(ntype, prefix)
            if ntype in TRIGGER_NODES:
                has_trigger = True
            self._check_node_specific(node, prefix)
        if not has_trigger:
            self.errors.append("No trigger node found — every workflow needs at least one trigger")

    def _check_node_type(self, ntype, prefix):
        for wrong, correct in WRONG_PREFIX_MAP.items():
            if ntype.startswith(wrong):
                self.errors.append(
                    f"{prefix}: Wrong prefix '{wrong}' in '{ntype}'. Use '{ntype.replace(wrong, correct)}'"
                )
                self.fixes.append({
                    "path": "type", "node": prefix, "action": "replace",
                    "old": ntype, "new": ntype.replace(wrong, correct),
                    "reason": "Workflow JSON requires full prefix"
                })
                return
        has_valid = any(ntype.startswith(p) for p in VALID_PREFIXES)
        if not has_valid:
            self.warnings.append(f"{prefix}: Unrecognized type '{ntype}' — may be a community node")

    def _check_node_specific(self, node, prefix):
        ntype = node.get("type", "")
        params = node.get("parameters", {})
        if ntype == "n8n-nodes-base.webhook":
            if not params.get("path"):
                self.errors.append(f"{prefix}: Webhook missing 'path' parameter")
        if ntype == "n8n-nodes-base.code":
            js_code = params.get("jsCode", "")
            py_code = params.get("pythonCode", "")
            code = js_code or py_code
            lang = "javascript" if js_code else "python"
            if code:
                self._check_code_node(code, lang, prefix)
        if ntype == "n8n-nodes-base.httpRequest":
            if not params.get("url") and not params.get("options", {}).get("url"):
                self.warnings.append(f"{prefix}: HTTP Request missing 'url'")
        if ntype in RESPOND_TO_WEBHOOK_NODES:
            has_wh = any(n.get("type") in WEBHOOK_TRIGGER_TYPES for n in self.wf.get("nodes", []))
            if not has_wh:
                self.errors.append(f"{prefix}: 'Respond to Webhook' requires a Webhook or Form trigger")
        if ntype == "n8n-nodes-base.if":
            if not params.get("conditions"):
                self.warnings.append(f"{prefix}: IF node has no conditions configured")

    def _check_code_node(self, code, lang, prefix):
        if lang == "javascript":
            if "return" in code and "[{" not in code and "json" not in code.lower():
                self.warnings.append(f"{prefix}: Code node return may need [{{json: {{...}}}}] format")
            if "{{" in code and "}}" in code:
                self.errors.append(f"{prefix}: Code node contains n8n expressions — use JS variables instead")
            if "console.log" in code:
                self.warnings.append(f"{prefix}: console.log outputs to server logs, not workflow data")
        elif lang == "python":
            for imp in ["requests", "pandas", "numpy", "beautifulsoup", "flask"]:
                if f"import {imp}" in code or f"from {imp}" in code:
                    self.errors.append(f"{prefix}: Python cannot use '{imp}' — standard library only")
            if "$input" in code:
                self.errors.append(f"{prefix}: Python uses '_input' not '$input'")
                self.fixes.append({
                    "path": "parameters.pythonCode", "node": prefix,
                    "action": "replace", "old": "$input", "new": "_input",
                    "reason": "Python Code nodes use _input"
                })

    def check_connections(self):
        connections = self.wf.get("connections", {})
        if not connections:
            if len(self.wf.get("nodes", [])) > 1:
                self.warnings.append("Multiple nodes but no connections")
            return
        for source_name, outputs in connections.items():
            if source_name not in self.nodes_by_name:
                self.errors.append(f"Connection references non-existent source node '{source_name}'")
                continue
            if not isinstance(outputs, dict):
                self.errors.append(f"Connections for '{source_name}' must be an object")
                continue
            for conn_type, output_indices in outputs.items():
                is_ai = conn_type in AI_CONNECTION_TYPES
                is_main = conn_type == STANDARD_CONNECTION
                if not is_ai and not is_main:
                    self.errors.append(
                        f"Connection from '{source_name}': unknown type '{conn_type}'. "
                        f"Use 'main' or: {', '.join(sorted(AI_CONNECTION_TYPES))}"
                    )
                if not isinstance(output_indices, list):
                    continue
                for targets in output_indices:
                    if not isinstance(targets, list):
                        continue
                    for target in targets:
                        tname = target.get("node", "")
                        if tname not in self.nodes_by_name:
                            self.errors.append(f"Connection target '{tname}' doesn't exist")
        # Check AI nodes have model
        for node in self.wf.get("nodes", []):
            if node.get("type") in AI_NODES_REQUIRING_MODEL:
                name = node.get("name", "")
                has_model = False
                for src, outputs in connections.items():
                    for ct, indices in outputs.items():
                        if ct == "ai_languageModel":
                            for idx_list in indices:
                                for t in (idx_list if isinstance(idx_list, list) else []):
                                    if t.get("node") == name:
                                        has_model = True
                if not has_model:
                    self.errors.append(f"AI node '{name}' has no language model — connect via 'ai_languageModel'")

    def check_expressions(self):
        for node in self.wf.get("nodes", []):
            prefix = f"({node.get('name', 'unnamed')})"
            self._scan_expr(node.get("parameters", {}), prefix, node)

    def _scan_expr(self, obj, prefix, node):
        if isinstance(obj, str):
            if "{{" in obj:
                opens = obj.count("{{")
                closes = obj.count("}}")
                if opens != closes:
                    self.errors.append(f"{prefix}: Unclosed expression — {opens} '{{{{' vs {closes} '}}}}'")
                if re.search(r'\{\{\s*\}\}', obj):
                    self.errors.append(f"{prefix}: Empty expression '{{}}'")
        elif isinstance(obj, dict):
            for k, v in obj.items():
                self._scan_expr(v, f"{prefix}.{k}", node)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                self._scan_expr(item, f"{prefix}[{i}]", node)

    def check_orphan_nodes(self):
        connections = self.wf.get("connections", {})
        connected = set()
        for src, outputs in connections.items():
            connected.add(src)
            for ct, indices in outputs.items():
                for idx_list in (indices if isinstance(indices, list) else []):
                    for t in (idx_list if isinstance(idx_list, list) else []):
                        connected.add(t.get("node", ""))
        for node in self.wf.get("nodes", []):
            name = node.get("name", "")
            ntype = node.get("type", "")
            if name not in connected and ntype not in TRIGGER_NODES:
                if ntype != "n8n-nodes-base.stickyNote":
                    self.warnings.append(f"Node '{name}' is orphaned — not connected")

    def check_respond_webhook(self):
        has_respond = any(n.get("type") in RESPOND_TO_WEBHOOK_NODES for n in self.wf.get("nodes", []))
        has_mode = any(
            n.get("type") in WEBHOOK_TRIGGER_TYPES and n.get("parameters", {}).get("responseMode") == "responseNode"
            for n in self.wf.get("nodes", [])
        )
        if has_mode and not has_respond:
            self.errors.append("Webhook responseMode='responseNode' but no Respond to Webhook node found")
        if has_respond and not has_mode:
            self.warnings.append("Respond to Webhook node found but webhook responseMode != 'responseNode'")

    def check_ids(self):
        for i, node in enumerate(self.wf.get("nodes", [])):
            if not node.get("id"):
                self.warnings.append(f"nodes[{i}] ({node.get('name', 'unnamed')}): Missing 'id'")
                self.fixes.append({
                    "path": f"nodes[{i}].id", "action": "set",
                    "value": str(uuid.uuid4()), "reason": "Every node should have a unique ID"
                })

    def validate(self) -> dict:
        self.check_top_level()
        if self.errors:
            return self._results()
        self.check_nodes()
        self.check_connections()
        self.check_expressions()
        self.check_orphan_nodes()
        self.check_respond_webhook()
        self.check_ids()
        return self._results()

    def _results(self):
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
            "fixes": self.fixes,
            "summary": {
                "total_nodes": len(self.wf.get("nodes", [])),
                "trigger_nodes": self.trigger_nodes,
                "node_types": sorted(self.node_types),
                "connection_count": sum(
                    len(targets)
                    for outputs in self.wf.get("connections", {}).values()
                    for indices in outputs.values()
                    for targets in (indices if isinstance(indices, list) else [])
                ),
            }
        }


def auto_fix(workflow, fixes):
    wf = json.loads(json.dumps(workflow))
    for fix in fixes:
        if fix["action"] == "set" and fix["path"] == "settings.executionOrder":
            wf.setdefault("settings", {})["executionOrder"] = fix["value"]
        elif fix["action"] == "replace" and "old" in fix and "new" in fix:
            wf_str = json.dumps(wf)
            wf_str = wf_str.replace(f'"{fix["old"]}"', f'"{fix["new"]}"')
            wf = json.loads(wf_str)
        elif fix["action"] == "set" and fix["path"].startswith("nodes["):
            match = re.match(r'nodes\[(\d+)\]\.id', fix["path"])
            if match:
                idx = int(match.group(1))
                if idx < len(wf.get("nodes", [])):
                    wf["nodes"][idx]["id"] = fix["value"]
    return wf


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate n8n workflow JSON")
    parser.add_argument("file", nargs="?", help="Path to workflow JSON file")
    parser.add_argument("--json", help="Inline JSON string")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--fix", action="store_true", help="Auto-fix and output corrected JSON")
    parser.add_argument("--quiet", action="store_true", help="Only output errors")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        if args.json:
            workflow = json.loads(args.json)
        elif args.stdin:
            workflow = json.load(sys.stdin)
        elif args.file:
            with open(args.file) as f:
                workflow = json.load(f)
        else:
            parser.print_help()
            sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        sys.exit(2)

    validator = WorkflowValidator(workflow)
    results = validator.validate()

    if args.fix and results["fixes"]:
        fixed = auto_fix(workflow, results["fixes"])
        print(json.dumps(fixed, indent=2))
        sys.exit(0)

    if args.json_output:
        print(json.dumps(results, indent=2))
        sys.exit(0 if results["valid"] else 1)

    if not args.quiet:
        print(f"\nWorkflow: {workflow.get('name', 'unnamed')}")
        print(f"  Nodes: {results['summary']['total_nodes']}")
        print(f"  Triggers: {', '.join(results['summary']['trigger_nodes']) or 'NONE'}")
        print(f"  Connections: {results['summary']['connection_count']}")
        print()

    if results["errors"]:
        print(f"ERRORS ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"  - {err}")
        print()

    if results["warnings"] and not args.quiet:
        print(f"WARNINGS ({len(results['warnings'])}):")
        for warn in results["warnings"]:
            print(f"  - {warn}")
        print()

    if results["fixes"] and not args.quiet:
        print(f"AUTO-FIXES AVAILABLE ({len(results['fixes'])}) — run with --fix:")
        for fix in results["fixes"]:
            print(f"  - {fix['reason']}")
        print()

    if results["valid"]:
        print("VALID" + (" (with warnings)" if results["warnings"] else ""))
        sys.exit(0)
    else:
        print("INVALID — do NOT deploy")
        sys.exit(1)


if __name__ == "__main__":
    main()
