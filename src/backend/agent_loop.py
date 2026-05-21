from src.models.schemas import (
    Message, Role, Plan, PlanStep, ToolName,
    ActionStatus, ToolResult, AgentConfig,
)
from src.backend.interface.base import BaseLLM
from src.backend.tools import ToolRegistry


SYSTEM_PROMPT = """You are an autonomous coding agent. You solve problems by using tools and thinking step by step.

Available tools:
- read_file: Read a file's contents
- write_file: Create or overwrite a file
- edit_file: Edit a file by replacing text
- list_dir: List directory contents
- run_command: Run a shell command
- bash: Run a bash command (for scripts/compilation)
- git_status: Show git status
- git_diff: Show uncommitted changes
- search_code: Search codebase for a pattern
- finish: Call when the task is complete

Guidelines:
1. First understand the problem by reading relevant files
2. Make a plan before writing code
3. Test your changes by running commands
4. If something fails, diagnose and fix it
5. Call finish when done with a summary
6. Keep your responses concise and focused on actions"""


class AgentLoop:
    def __init__(self, llm: BaseLLM, tools: ToolRegistry, config: AgentConfig):
        self.llm = llm
        self.tools = tools
        self.config = config
        self.messages: list[Message] = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
        ]
        self.turn = 0
        self.done = False

    def run(self, user_input: str) -> str:
        self.messages.append(Message(role=Role.USER, content=user_input))
        summary = ""

        while self.turn < self.config.max_turns and not self.done:
            self.turn += 1

            response = self.llm.chat(self.messages, self.tools.get_all_tool_definitions())
            self.messages.append(response)

            if response.content:
                print(f"\n  Agent: {response.content}")

            if response.tool_calls:
                for tc in response.tool_calls:
                    tool_name = tc["name"]
                    args = tc.get("arguments", {})

                    if tool_name == "finish":
                        summary = args.get("summary", "Task completed")
                        self.done = True
                        print(f"\n  [Finish] {summary}")
                        break

                    print(f"\n  [Tool] {tool_name}({args})")
                    result = self.tools.execute(tool_name, **args)
                    print(f"  [Result] {'OK' if result.success else 'FAIL'}: {result.output[:300]}")

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
                self.done = True

        if not self.done and self.turn >= self.config.max_turns:
            summary = "Reached max turns"

        return summary or "Task completed"
