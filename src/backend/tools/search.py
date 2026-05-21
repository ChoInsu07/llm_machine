import re
from pathlib import Path
from src.models.schemas import ToolResult


class SearchTools:
    def __init__(self, workspace_dir: str = "."):
        self.workspace = Path(workspace_dir).resolve()
        self._exclude_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv"}

    def _walk(self, path: Path, pattern: str, include: str | None = None) -> list[str]:
        results = []
        for p in path.rglob("*"):
            if any(part in self._exclude_dirs for part in p.parts):
                continue
            if p.is_file():
                if include and not p.match(include):
                    continue
                try:
                    content = p.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(content.splitlines(), 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            rel = p.relative_to(self.workspace)
                            results.append(f"{rel}:{i}: {line.strip()}")
                except Exception:
                    pass
        return results

    def search_code(self, pattern: str, include: str | None = None) -> ToolResult:
        try:
            results = self._walk(self.workspace, pattern, include)
            if not results:
                return ToolResult(True, "No matches found")
            output = "\n".join(results[:200])
            if len(results) > 200:
                output += f"\n... and {len(results) - 200} more results"
            return ToolResult(True, output)
        except Exception as e:
            return ToolResult(False, "", str(e))

    def grep(self, pattern: str, include: str | None = None) -> ToolResult:
        return self.search_code(pattern, include)

    def get_tool_definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_code",
                    "description": "Search codebase for a regex pattern",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {"type": "string", "description": "Regex to search"},
                            "include": {"type": "string", "description": "Glob filter (e.g. *.py)"},
                        },
                        "required": ["pattern"],
                    },
                },
            },
        ]
