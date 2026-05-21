#!/usr/bin/env python3
import os
import sys
import json
import threading
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
except ImportError:
    os.system("pip install flask flask-cors")
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS

from src.models.schemas import AgentConfig
from src.backend.orchestrator import Orchestrator

app = Flask(__name__)
CORS(app)

config = AgentConfig(
    model=os.getenv("OLLAMA_MODEL", "llama3.2"),
    ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
    workspace_dir=os.getenv("WORKSPACE_DIR", str(Path.cwd())),
)
orch = Orchestrator(config)


# Auto-detect model if default not found
def _ensure_model():
    try:
        import requests
        r = requests.get(f"{config.ollama_host}/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            if models:
                names = [m["name"] for m in models]
                if config.model not in names:
                    old = config.model
                    config.model = names[0]
                    orch.config.model = names[0]
                    orch.llm.model = names[0]
                    print(f"Model '{old}' not found, using '{names[0]}' instead")
    except Exception:
        pass


_ensure_model()


@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({"success": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify(orch.check_health())


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_input = data.get("message", "")
    use_planning = data.get("planning", True)

    if not user_input:
        return jsonify({"error": "message is required"}), 400

    result = orch.execute_task(user_input, use_planning=use_planning)
    return jsonify(result)


TOOL_FAMILIES = {"llama", "qwen", "deepseek", "mistral", "mixtral", "command-r", "dbrx", "nemotron", "phi", "falcon"}

def _supports_tools(model_name: str) -> bool:
    try:
        r = requests.get(f"{config.ollama_host}/api/tags", timeout=5)
        if r.status_code == 200:
            for m in r.json().get("models", []):
                if m["name"] == model_name:
                    details = m.get("details", {})
                    families = details.get("families", [details.get("family", "")])
                    fam = " ".join(f for f in families if f).lower()
                    return any(f in fam for f in TOOL_FAMILIES)
    except Exception:
        pass
    return False


@app.route("/api/models", methods=["GET"])
def list_models():
    try:
        r = requests.get(f"{config.ollama_host}/api/tags", timeout=5)
        if r.status_code != 200:
            return jsonify({"models": [], "error": "Ollama not reachable"})
        data = r.json()
        models = []
        for m in data.get("models", []):
            name = m["name"]
            models.append({
                "name": name,
                "size": m.get("size", 0),
                "supports_tools": _supports_tools(name),
                "selected": name == config.model,
            })
        models.sort(key=lambda x: (-x["selected"], x["name"]))
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"models": [], "error": str(e)})


@app.route("/api/models/pull", methods=["POST"])
def pull_model():
    data = request.json or {}
    name = data.get("name", "")
    if not name:
        return jsonify({"error": "model name required"}), 400

    def stream_pull():
        try:
            r = requests.post(
                f"{config.ollama_host}/api/pull",
                json={"name": name},
                stream=True,
                timeout=600,
            )
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    try:
                        d = json.loads(line)
                        yield f"data: {json.dumps(d)}\n\n"
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    from flask import Response
    return Response(stream_pull(), mimetype="text/event-stream")


@app.route("/api/read-file", methods=["POST"])
def read_file():
    data = request.json or {}
    path = data.get("path", "")
    offset = data.get("offset", 0)
    limit = data.get("limit", 2000)
    result = orch.tools.fs.read_file(path, offset, limit)
    return jsonify({"success": result.success, "output": result.output, "error": result.error})


@app.route("/api/write-file", methods=["POST"])
def write_file():
    data = request.json or {}
    path = data.get("path", "")
    content = data.get("content", "")
    result = orch.tools.fs.write_file(path, content)
    return jsonify({"success": result.success, "output": result.output, "error": result.error})


@app.route("/api/list-dir", methods=["POST"])
def list_dir():
    data = request.json or {}
    path = data.get("path", ".")
    result = orch.tools.fs.list_dir(path)
    return jsonify({"success": result.success, "output": result.output, "error": result.error})


@app.route("/api/file-tree", methods=["GET"])
def file_tree():
    root = Path(orch.config.workspace_dir).resolve()
    exclude = {".git", "__pycache__", "node_modules", ".venv", "venv", "*.pyc"}

    def build_tree(path: Path, prefix: str = "") -> list:
        items = []
        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return items

        for entry in entries:
            if entry.name.startswith(".") and entry.name not in (".env.example", ".gitignore"):
                continue
            if entry.suffix in {".pyc"}:
                continue
            if entry.name in exclude:
                continue

            item = {
                "name": entry.name,
                "path": str(entry.relative_to(root)),
                "type": "directory" if entry.is_dir() else "file",
                "children": [],
            }
            if entry.is_dir():
                item["children"] = build_tree(entry)
            items.append(item)
        return items

    tree = build_tree(root)
    return jsonify(tree)


@app.route("/api/config", methods=["GET", "POST"])
def config_api():
    if request.method == "GET":
        return jsonify({
            "model": config.model,
            "ollama_host": config.ollama_host,
            "workspace_dir": config.workspace_dir,
        })
    data = request.json or {}
    if "model" in data:
        config.model = data["model"]
    if "ollama_host" in data:
        config.ollama_host = data["ollama_host"]
        orch.llm.host = data["ollama_host"].rstrip("/")
        orch.llm.chat_url = f"{orch.llm.host}/api/chat"
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    print(f"Backend server running on http://localhost:{port}")
    print(f"Using model: {config.model}")
    app.run(host="0.0.0.0", port=port, debug=False)
