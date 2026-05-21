import subprocess
import tempfile
import os
from pathlib import Path
from src.models.schemas import ToolResult


class ShellTools:
    def __init__(self, workspace_dir: str = "."):
        self.workspace = str(Path(workspace_dir).resolve())

    def run_command(self, command: str, timeout: int = 60) -> ToolResult:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace,
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += result.stderr
            success = result.returncode == 0
            if success:
                return ToolResult(True, output.strip() if output.strip() else "(empty output)")
            else:
                return ToolResult(False, output.strip() if output.strip() else "(no output)", f"exit code {result.returncode}")
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", f"Command timed out after {timeout}s")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def run_bash(self, command: str, timeout: int = 120) -> ToolResult:
        return self.run_command(command, timeout)

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a shell command in the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"},
                            "timeout": {"type": "number", "description": "Timeout in seconds"},
                        },
                        "required": ["command"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Run a bash command (longer timeout for scripts)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Bash command"},
                            "timeout": {"type": "number", "description": "Timeout in seconds"},
                        },
                        "required": ["command"],
                    },
                },
            },
        ]
