import json
from src.models.schemas import Message, Role, Plan, PlanStep, ToolName, ActionStatus
from src.backend.interface.base import BaseLLM


SYSTEM_PROMPT = """You are a planning agent. Given a user goal, break it down into a sequence of steps.

Each step must have:
- description: what to do
- tool: which tool to use (read_file, write_file, edit_file, run_command, bash, git_status, git_diff, search_code, list_dir, finish)
- args: arguments for the tool

Output ONLY valid JSON in this format:
{
  "steps": [
    {"description": "...", "tool": "read_file", "args": {"path": "..."}},
    {"description": "...", "tool": "write_file", "args": {"path": "...", "content": "..."}},
    {"description": "...", "tool": "run_command", "args": {"command": "..."}},
    {"description": "...", "tool": "finish", "args": {"summary": "..."}}
  ]
}

Be specific and concrete. Never use placeholders."""


class Planner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def create_plan(self, goal: str, context: str = "") -> Plan:
        user_msg = f"Goal: {goal}\n\nContext:\n{context}" if context else f"Goal: {goal}"

        messages = [
            Message(role=Role.SYSTEM, content=SYSTEM_PROMPT),
            Message(role=Role.USER, content=user_msg),
        ]

        response = self.llm.chat(messages)
        plan = Plan(goal=goal)

        try:
            json_str = response.content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            data = json.loads(json_str.strip())

            for s in data.get("steps", []):
                tool_name = s.get("tool", "finish")
                plan.add_step(PlanStep(
                    description=s.get("description", ""),
                    action=s.get("description", ""),
                    tool=ToolName(tool_name),
                    args=s.get("args", {}),
                ))
        except (json.JSONDecodeError, KeyError) as e:
            plan.add_step(PlanStep(
                description=f"Execute goal: {goal}",
                action=f"Execute goal: {goal}",
                tool=ToolName.BASH,
                args={"command": goal},
            ))

        return plan
