from src.backend.tools.filesystem import FileSystemTools
from src.backend.tools.shell import ShellTools
from src.backend.tools.git_tool import GitTools
from src.backend.tools.search import SearchTools
from src.models.schemas import ToolName, ToolResult


class ToolRegistry:
    def __init__(self, workspace_dir: str = "."):
        self.fs = FileSystemTools(workspace_dir)
        self.shell = ShellTools(workspace_dir)
        self.git = GitTools(workspace_dir)
        self.search = SearchTools(workspace_dir)

    def execute(self, tool_name: str, **kwargs) -> ToolResult:
        name = ToolName(tool_name)

        if name == ToolName.READ_FILE:
            return self.fs.read_file(**kwargs)
        elif name == ToolName.WRITE_FILE:
            return self.fs.write_file(**kwargs)
        elif name == ToolName.EDIT_FILE:
            return self.fs.edit_file(**kwargs)
        elif name == ToolName.LIST_DIR:
            return self.fs.list_dir(**kwargs)
        elif name == ToolName.RUN_COMMAND:
            return self.shell.run_command(**kwargs)
        elif name == ToolName.BASH:
            return self.shell.run_bash(**kwargs)
        elif name == ToolName.GIT_STATUS:
            return self.git.status()
        elif name == ToolName.GIT_DIFF:
            return self.git.diff(**kwargs)
        elif name == ToolName.SEARCH_CODE:
            return self.search.search_code(**kwargs)

        return ToolResult(False, "", f"Unknown tool: {tool_name}")

    def get_all_tool_definitions(self) -> list[dict]:
        tools = []
        tools.extend(self.fs.get_tool_definitions())
        tools.extend(self.shell.get_tool_definitions())
        tools.extend(self.git.get_tool_definitions())
        tools.extend(self.search.get_tool_definitions())
        tools.append({
            "type": "function",
            "function": {
                "name": "finish",
                "description": "Call when the task is complete",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Summary of what was done"},
                    },
                    "required": ["summary"],
                },
            },
        })
        return tools
