import re
import json
from src.models.schemas import (
    Message, Role, ToolName, ToolResult, AgentConfig,
)
from src.backend.interface.base import BaseLLM
from src.backend.tools import ToolRegistry


TOOL_DESCRIPTIONS = """
Available tools - call them by writing EXACTLY this format in your response:

read_file(path="file.py", offset=0, limit=2000)
write_file(path="file.py", content="your code here")
edit_file(path="file.py", old_string="old", new_string="new")
run_command(command="pytest tests/")
bash(command="python script.py")
git_status()
git_diff()
search_code(pattern="TODO", include="*.py")
list_dir(path=".")
finish(summary="What was done")

You MUST use these tools to read, write, and execute code.
Always use write_file to create files, run_command to test, finish when done.
"""

TOOL_PATTERN = re.compile(
    r'(read_file|write_file|edit_file|run_command|bash|git_status|git_diff|search_code|list_dir|finish)'
    r'\s*\(\s*((?:[^)]*?))\s*\)',
    re.DOTALL
)

ARG_PATTERN = re.compile(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\d+)|(\[.*?\]))')


def parse_tool_call(text: str) -> list[dict]:
    calls = []
    for match in TOOL_PATTERN.finditer(text):
        name = match.group(1)
        args_str = match.group(2).strip()
        args = {}
        for am in ARG_PATTERN.finditer(args_str):
            key = am.group(1)
            val = am.group(2) or am.group(3) or am.group(4) or am.group(5)
            args[key] = val
        calls.append({"name": name, "arguments": args})
    return calls


class AgentLoop:
    def __init__(self, llm: BaseLLM, tools: ToolRegistry, config: AgentConfig):
        self.llm = llm
        self.tools = tools
        self.config = config
        self.turn = 0
        self.done = False
        self.modified_files = []

    def run(self, user_input: str) -> tuple[str, list[dict], list[str]]:
        system_content = "You are an autonomous coding agent. You solve problems step by step."
        system_content += TOOL_DESCRIPTIONS
        system_content += "\n\nThink step by step, then call tools to execute."

        self.messages = [Message(role=Role.SYSTEM, content=system_content)]
        self.messages.append(Message(role=Role.USER, content=user_input))
        events = []
        summary = ""

        while self.turn < self.config.max_turns and not self.done:
            self.turn += 1

            response = self.llm.chat(self.messages)
            self.messages.append(response)

            text = response.content or ""

            tool_calls = parse_tool_call(text)

            if tool_calls:
                think_text = text
                for tc in tool_calls:
                    placeholder = f"{tc['name']}({', '.join(f'{k}={v}' for k,v in tc['arguments'].items())})"
                    think_text = think_text.replace(placeholder, f"[calling {tc['name']}...]", 1)
                think_text = think_text.strip()
                if think_text:
                    events.append({"type": "think", "content": think_text})

                for tc in tool_calls:
                    tool_name = tc["name"]
                    args = tc.get("arguments", {})

                    if tool_name == "finish":
                        summary = args.get("summary", "Task completed")
                        self.done = True
                        events.append({"type": "finish", "content": summary})
                        break

                    events.append({"type": "tool", "name": tool_name, "args": dict(args)})

                    result = self.tools.execute(tool_name, **args)

                    events.append({
                        "type": "result",
                        "success": result.success,
                        "output": result.output[:500],
                        "error": result.error,
                    })

                    if tool_name in ("write_file", "edit_file") and result.success:
                        file_path = args.get("path", "")
                        self.modified_files.append(file_path)
                        events.append({"type": "file", "path": file_path, "action": tool_name})

                    tool_msg = Message(
                        role=Role.TOOL,
                        content=result.output if result.success else f"Error: {result.error or result.output}",
                        name=tool_name,
                        tool_call_id=tool_name,
                    )
                    self.messages.append(tool_msg)

                    if not result.success:
                        retry_msg = Message(
                            role=Role.USER,
                            content=f"The tool {tool_name} failed. Try a different approach or fix the error.",
                        )
                        self.messages.append(retry_msg)
            else:
                if text.strip():
                    events.append({"type": "think", "content": text.strip()})
                self.done = True

        if not self.done and self.turn >= self.config.max_turns:
            summary = "Reached max turns"

        return summary or "Task completed", events, list(set(self.modified_files))
