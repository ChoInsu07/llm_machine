import subprocess
from pathlib import Path
from src.models.schemas import ToolResult


class GitTools:
    def __init__(self, workspace_dir: str = "."):
        self.workspace = str(Path(workspace_dir).resolve())

    def _git(self, *args: str) -> ToolResult:
        try:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.workspace,
            )
            output = result.stdout.strip() or result.stderr.strip()
            success = result.returncode == 0
            if success:
                return ToolResult(True, output or "(empty)")
            return ToolResult(False, output or "(no output)", f"git exit code {result.returncode}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def status(self) -> ToolResult:
        return self._git("status")

    def diff(self, *paths: str) -> ToolResult:
        args = ["diff"]
        if paths:
            args.extend(paths)
        return self._git(*args)

    def log(self, n: int = 10) -> ToolResult:
        return self._git("log", f"-{n}", "--oneline")

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "git_status",
                    "description": "Show git status of the workspace",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "git_diff",
                    "description": "Show git diff (uncommitted changes)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "paths": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional paths to diff",
                            }
                        },
                    },
                },
            },
        ]
