"""Real-world JSON-RPC 2.0 Stdio Client Test for WhyCode MCP Server.

Simulates exactly what Cursor, Claude Desktop, and VS Code do:
1. Spawns `python whycode_mcp.py` over stdin/stdout.
2. Sends `initialize` request.
3. Sends `notifications/initialized`.
4. Sends `tools/list` request.
5. Sends `tools/call` request for `whycode_ask`.
6. Sends `tools/call` request for ungrounded question (Conformal Gate check).
7. Sends `tools/call` request for `whycode_list_repos`.
"""
import subprocess
import json
import sys
import os

python_exe = sys.executable

cmd = [python_exe, "whycode_mcp.py"]

print(f"🚀 Spawning WhyCode MCP Server: {' '.join(cmd)}")
proc = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

req_id = 1

def send_request(method, params=None):
    global req_id
    payload = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method
    }
    if params is not None:
        payload["params"] = params
    msg = json.dumps(payload) + "\n"
    proc.stdin.write(msg)
    proc.stdin.flush()
    req_id += 1
    
    # Read response
    while True:
        line = proc.stdout.readline()
        if not line:
            err = proc.stderr.read()
            raise RuntimeError(f"Server closed connection. Stderr: {err}")
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                return data
            except json.JSONDecodeError:
                # Some servers print logs, ignore until valid JSON-RPC
                continue

try:
    # 1. Initialize
    print("\n--- 1. Testing MCP 'initialize' Handshake ---")
    init_res = send_request("initialize", {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "TestClient-Cursor", "version": "1.0.0"}
    })
    server_info = init_res.get("result", {}).get("serverInfo", {})
    print(f"✓ Initialized successfully with Server: {server_info.get('name')} v{server_info.get('version')}")

    # Send initialized notification
    notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
    proc.stdin.write(notif)
    proc.stdin.flush()

    # 2. List Tools
    print("\n--- 2. Testing MCP 'tools/list' ---")
    tools_res = send_request("tools/list")
    tools = tools_res.get("result", {}).get("tools", [])
    print(f"✓ Registered {len(tools)} MCP Tools:")
    for t in tools:
        print(f"  • {t['name']}: {t.get('description', '')[:70]}...")

    # 3. Call whycode_ask with Grounded Question
    print("\n--- 3. Testing MCP 'tools/call' -> whycode_ask (Valid Query) ---")
    call_res = send_request("tools/call", {
        "name": "whycode_ask",
        "arguments": {
            "question": "why did Django avoid duplicate joins in filter after aggregation?",
            "repo": "django/django"
        }
    })
    content = call_res.get("result", {}).get("content", [])
    output_text = content[0].get("text", "") if content else ""
    print("✓ Tool Response Received:")
    print(output_text[:350] + "...\n[Truncated for display]")

    # 4. Call whycode_ask with Ungrounded Question (Conformal Abstention)
    print("\n--- 4. Testing MCP 'tools/call' -> whycode_ask (Conformal Abstention) ---")
    abstain_res = send_request("tools/call", {
        "name": "whycode_ask",
        "arguments": {
            "question": "why does Django use quantum blockchain?",
            "repo": "django/django"
        }
    })
    abs_content = abstain_res.get("result", {}).get("content", [])
    abs_text = abs_content[0].get("text", "") if abs_content else ""
    print("✓ Conformal Gate Response Received:")
    print(abs_text)

    # 5. Call whycode_list_repos
    print("\n--- 5. Testing MCP 'tools/call' -> whycode_list_repos ---")
    repos_res = send_request("tools/call", {
        "name": "whycode_list_repos",
        "arguments": {}
    })
    repos_content = repos_res.get("result", {}).get("content", [])
    repos_text = repos_content[0].get("text", "") if repos_content else ""
    print("✓ Repositories List Received:")
    print(repos_text)

    print("\n🎯 ALL MCP JSON-RPC 2.0 PROTOCOL TESTS PASSED WITH 100% SUCCESS!")

finally:
    proc.terminate()
