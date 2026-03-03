#!/usr/bin/env python3
"""
n8n Workflow Deploy Pipeline v2.0
==================================
Implements the complete Build Loop:
  scaffold → validate → create (inactive) → test execute → check logs → activate

Usage:
    python deploy_workflow.py --url https://n8n.example.com --api-key KEY workflow.json
    python deploy_workflow.py --url https://n8n.example.com --api-key KEY --stdin < workflow.json
    python deploy_workflow.py --url https://n8n.example.com --api-key KEY --validate-only workflow.json
    python deploy_workflow.py --url https://n8n.example.com --api-key KEY --update WORKFLOW_ID workflow.json

Environment variables:
    N8N_API_URL  - n8n instance URL
    N8N_API_KEY  - API key for authentication
"""

import json
import sys
import os
import time
import argparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Import validator from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_workflow import WorkflowValidator, auto_fix


class N8nClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self.api_key = api_key

    def _request(self, method: str, path: str, data=None) -> dict:
        url = f"{self.api_url}{path}"
        headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.readable() else ""
            raise Exception(f"HTTP {e.code}: {error_body}")

    def create_workflow(self, workflow: dict) -> dict:
        return self._request("POST", "/workflows", workflow)

    def update_workflow(self, wf_id: str, workflow: dict) -> dict:
        return self._request("PUT", f"/workflows/{wf_id}", workflow)

    def get_workflow(self, wf_id: str) -> dict:
        return self._request("GET", f"/workflows/{wf_id}")

    def activate_workflow(self, wf_id: str) -> dict:
        return self._request("POST", f"/workflows/{wf_id}/activate")

    def deactivate_workflow(self, wf_id: str) -> dict:
        return self._request("POST", f"/workflows/{wf_id}/deactivate")

    def run_workflow(self, wf_id: str) -> dict:
        return self._request("POST", f"/workflows/{wf_id}/run")

    def get_executions(self, wf_id: str = None, limit: int = 5) -> dict:
        path = f"/executions?limit={limit}"
        if wf_id:
            path += f"&workflowId={wf_id}"
        return self._request("GET", path)

    def get_execution(self, exec_id: str) -> dict:
        return self._request("GET", f"/executions/{exec_id}")

    def list_workflows(self, limit: int = 100) -> dict:
        return self._request("GET", f"/workflows?limit={limit}")

    def list_credentials(self) -> dict:
        return self._request("GET", "/credentials")

    def delete_workflow(self, wf_id: str) -> dict:
        return self._request("DELETE", f"/workflows/{wf_id}")


def deploy(client: N8nClient, workflow: dict, validate_only=False, update_id=None, auto_activate=False):
    """Full deployment pipeline."""
    steps = []

    # Step 1: Validate
    print("\n[1/6] Validating workflow...")
    validator = WorkflowValidator(workflow)
    results = validator.validate()

    if results["errors"]:
        print(f"  ERRORS ({len(results['errors'])}):")
        for err in results["errors"]:
            print(f"    - {err}")

        if results["fixes"]:
            print(f"\n  Attempting auto-fix ({len(results['fixes'])} fixes)...")
            workflow = auto_fix(workflow, results["fixes"])
            validator2 = WorkflowValidator(workflow)
            results2 = validator2.validate()
            if results2["errors"]:
                print("  Auto-fix did not resolve all errors:")
                for err in results2["errors"]:
                    print(f"    - {err}")
                print("\n  DEPLOY ABORTED — fix errors manually")
                return {"success": False, "step": "validate", "errors": results2["errors"]}
            else:
                print("  Auto-fix resolved all errors!")
                results = results2
        else:
            print("\n  DEPLOY ABORTED — fix errors manually")
            return {"success": False, "step": "validate", "errors": results["errors"]}

    if results["warnings"]:
        print(f"  Warnings ({len(results['warnings'])}):")
        for w in results["warnings"]:
            print(f"    - {w}")

    print(f"  Nodes: {results['summary']['total_nodes']}, "
          f"Triggers: {', '.join(results['summary']['trigger_nodes'])}, "
          f"Connections: {results['summary']['connection_count']}")
    steps.append({"step": "validate", "status": "passed"})

    if validate_only:
        print("\n  Validation only — stopping here")
        return {"success": True, "step": "validate", "results": results}

    # Step 2: Create/Update workflow (inactive)
    if update_id:
        print(f"\n[2/6] Updating workflow {update_id}...")
        try:
            result = client.update_workflow(update_id, workflow)
            wf_id = result.get("id", update_id)
            print(f"  Updated: {wf_id}")
        except Exception as e:
            print(f"  UPDATE FAILED: {e}")
            return {"success": False, "step": "update", "error": str(e)}
    else:
        print("\n[2/6] Creating workflow (inactive)...")
        try:
            result = client.create_workflow(workflow)
            wf_id = result.get("id")
            print(f"  Created: {wf_id}")
            print(f"  URL: {client.base_url}/workflow/{wf_id}")
        except Exception as e:
            print(f"  CREATE FAILED: {e}")
            return {"success": False, "step": "create", "error": str(e)}
    steps.append({"step": "create", "status": "ok", "id": wf_id})

    # Step 3: Test execution (for manual/schedule triggers only)
    has_manual = any(
        n.get("type") in ("n8n-nodes-base.manualTrigger", "n8n-nodes-base.scheduleTrigger")
        for n in workflow.get("nodes", [])
    )

    if has_manual:
        print("\n[3/6] Test executing...")
        try:
            exec_result = client.run_workflow(wf_id)
            exec_id = exec_result.get("id")
            print(f"  Execution started: {exec_id}")

            # Step 4: Wait and check
            print("\n[4/6] Checking execution result...")
            time.sleep(2)
            if exec_id:
                try:
                    exec_details = client.get_execution(exec_id)
                    status = exec_details.get("status", exec_details.get("finished"))
                    if status == "error" or status == "crashed":
                        print(f"  Execution FAILED: {status}")
                        error_msg = exec_details.get("data", {}).get("resultData", {}).get("error", {}).get("message", "Unknown error")
                        print(f"  Error: {error_msg}")
                        steps.append({"step": "test", "status": "failed", "error": error_msg})
                    else:
                        print(f"  Execution status: {status}")
                        steps.append({"step": "test", "status": "passed"})
                except Exception as e:
                    print(f"  Could not check execution: {e}")
                    steps.append({"step": "test", "status": "unknown"})
        except Exception as e:
            print(f"  Test execution skipped: {e}")
            steps.append({"step": "test", "status": "skipped", "reason": str(e)})
    else:
        print("\n[3/6] Skipping test execution (webhook/form/chat trigger)")
        print("[4/6] Skipping execution check")
        steps.append({"step": "test", "status": "skipped", "reason": "non-manual trigger"})

    # Step 5: Review
    print("\n[5/6] Reviewing deployed workflow...")
    try:
        deployed = client.get_workflow(wf_id)
        node_count = len(deployed.get("nodes", []))
        is_active = deployed.get("active", False)
        print(f"  Name: {deployed.get('name')}")
        print(f"  Nodes: {node_count}")
        print(f"  Active: {is_active}")
        steps.append({"step": "review", "status": "ok"})
    except Exception as e:
        print(f"  Review failed: {e}")

    # Step 6: Activate (if requested)
    if auto_activate:
        print("\n[6/6] Activating workflow...")
        try:
            client.activate_workflow(wf_id)
            print(f"  Activated!")
            steps.append({"step": "activate", "status": "ok"})
        except Exception as e:
            print(f"  Activation failed: {e}")
            steps.append({"step": "activate", "status": "failed", "error": str(e)})
    else:
        print(f"\n[6/6] Workflow ready — activate manually or run:")
        print(f"  POST {client.api_url}/workflows/{wf_id}/activate")
        steps.append({"step": "activate", "status": "pending"})

    print(f"\n{'='*50}")
    print(f"  Workflow ID: {wf_id}")
    print(f"  Editor URL: {client.base_url}/workflow/{wf_id}")
    print(f"{'='*50}\n")

    return {"success": True, "workflow_id": wf_id, "steps": steps}


def main():
    parser = argparse.ArgumentParser(description="Deploy n8n workflow with full validation pipeline")
    parser.add_argument("file", nargs="?", help="Workflow JSON file")
    parser.add_argument("--url", default=os.environ.get("N8N_API_URL"), help="n8n instance URL")
    parser.add_argument("--api-key", default=os.environ.get("N8N_API_KEY"), help="API key")
    parser.add_argument("--stdin", action="store_true", help="Read from stdin")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't deploy")
    parser.add_argument("--update", metavar="ID", help="Update existing workflow by ID")
    parser.add_argument("--activate", action="store_true", help="Auto-activate after deploy")
    parser.add_argument("--json-output", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load workflow
    try:
        if args.stdin:
            workflow = json.load(sys.stdin)
        elif args.file:
            with open(args.file) as f:
                workflow = json.load(f)
        else:
            parser.print_help()
            sys.exit(2)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    if args.validate_only:
        validator = WorkflowValidator(workflow)
        results = validator.validate()
        if args.json_output:
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps(results, indent=2))
        sys.exit(0 if results["valid"] else 1)

    if not args.url:
        print("Error: --url or N8N_API_URL required", file=sys.stderr)
        sys.exit(2)
    if not args.api_key:
        print("Error: --api-key or N8N_API_KEY required", file=sys.stderr)
        sys.exit(2)

    client = N8nClient(args.url, args.api_key)
    result = deploy(client, workflow, update_id=args.update, auto_activate=args.activate)

    if args.json_output:
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
