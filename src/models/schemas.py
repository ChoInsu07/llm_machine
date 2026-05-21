from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolName(str, Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    RUN_COMMAND = "run_command"
    GIT_DIFF = "git_diff"
    GIT_STATUS = "git_status"
    SEARCH_CODE = "search_code"
    LIST_DIR = "list_dir"
    BASH = "bash"
    FINISH = "finish"


class ActionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Message:
    role: Role
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


@dataclass
class PlanStep:
    description: str
    action: str
    tool: ToolName
    args: dict
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep] = field(default_factory=list)
    current_step: int = 0
    completed: bool = False

    def add_step(self, step: PlanStep):
        self.steps.append(step)

    def next_step(self) -> Optional[PlanStep]:
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None

    def current(self) -> Optional[PlanStep]:
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None


@dataclass
class ToolResult:
    success: bool
    output: str
    error: Optional[str] = None


@dataclass
class AgentConfig:
    model: str = "llama3.2"
    provider: str = "ollama"
    ollama_host: str = "http://localhost:11434"
    max_retries: int = 3
    workspace_dir: str = "."
    max_turns: int = 30
    system_prompt: str = ""
