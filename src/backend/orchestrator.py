from src.models.schemas import AgentConfig
from src.backend.interface.ollama import OllamaLLM
from src.backend.tools import ToolRegistry
from src.backend.planner import Planner
from src.backend.agent_loop import AgentLoop


class Orchestrator:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm = OllamaLLM(
            host=config.ollama_host,
            model=config.model,
        )
        self.tools = ToolRegistry(config.workspace_dir)
        self.planner = Planner(self.llm)

    def check_health(self) -> dict:
        ollama_ok = self.llm.check_available()
        return {
            "ollama": ollama_ok,
            "model": self.config.model if ollama_ok else "unavailable",
            "workspace": self.config.workspace_dir,
        }

    def execute_task(self, user_input: str, use_planning: bool = True) -> dict:
        if not self.llm.check_available():
            return {"result": "Error: Ollama is not running", "events": [], "files": []}

        if use_planning:
            plan = self.planner.create_plan(user_input)
            plan_events = [{"type": "plan", "steps": [
                {"description": s.description, "tool": s.tool.value} for s in plan.steps
            ]}]

            plan_input = f"Goal: {user_input}\n\nPlan:\n" + "\n".join(
                f"{i}. {s.description}" for i, s in enumerate(plan.steps, 1)
            )
            loop = AgentLoop(self.llm, self.tools, self.config)
            result, loop_events, files = loop.run(plan_input)
            return {"result": result, "events": plan_events + loop_events, "files": files}
        else:
            loop = AgentLoop(self.llm, self.tools, self.config)
            result, events, files = loop.run(user_input)
            return {"result": result, "events": events, "files": files}
