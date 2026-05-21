import os
from pathlib import Path
from src.models.schemas import ToolResult


class FileSystemTools:
    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir).resolve()

    def _resolve_path(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        return p.resolve()

    def _is_safe(self, path: Path) -> bool:
        try:
            path.relative_to(self.workspace)
            return True
        except ValueError:
            return False

    def read_file(self, path: str, offset: int = 0, limit: int = 2000) -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            if not self._is_safe(full_path):
                return ToolResult(False, "", "Access denied: outside workspace")
            if not full_path.exists():
                return ToolResult(False, "", f"File not found: {path}")
            with open(full_path, encoding="utf-8") as f:
                lines = f.readlines()
            total = len(lines)
            selected = lines[offset:offset + limit]
            content = "".join(selected)
            info = f"File: {path} ({total} lines, showing {len(selected)})\n"
            return ToolResult(True, info + content)
        except Exception as e:
            return ToolResult(False, "", str(e))

    def write_file(self, path: str, content: str) -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            if not self._is_safe(full_path):
                return ToolResult(False, "", "Access denied: outside workspace")
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(True, f"Written {len(content)} bytes to {path}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def edit_file(self, path: str, old_string: str, new_string: str) -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            if not self._is_safe(full_path):
                return ToolResult(False, "", "Access denied: outside workspace")
            if not full_path.exists():
                return ToolResult(False, "", f"File not found: {path}")
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
            if old_string not in content:
                return ToolResult(False, "", f"old_string not found in {path}")
            new_content = content.replace(old_string, new_string, 1)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return ToolResult(True, f"Edited {path}")
        except Exception as e:
            return ToolResult(False, "", str(e))

    def list_dir(self, path: str = ".") -> ToolResult:
        try:
            full_path = self._resolve_path(path)
            if not self._is_safe(full_path):
                return ToolResult(False, "", "Access denied: outside workspace")
            if not full_path.exists():
                return ToolResult(False, "", f"Directory not found: {path}")
            entries = os.listdir(full_path)
            lines = []
            for e in sorted(entries):
                fp = full_path / e
                suffix = "/" if fp.is_dir() else ""
                lines.append(f"{e}{suffix}")
            return ToolResult(True, "\n".join(lines))
        except Exception as e:
            return ToolResult(False, "", str(e))

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file from the workspace",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "offset": {"type": "number", "description": "Start line"},
                            "limit": {"type": "number", "description": "Max lines"},
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Create or overwrite a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "File content"},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Replace first occurrence of old_string with new_string in a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "old_string": {"type": "string", "description": "Text to replace"},
                            "new_string": {"type": "string", "description": "New text"},
                        },
                        "required": ["path", "old_string", "new_string"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "List directory contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path"},
                        },
                    },
                },
            },
        ]
