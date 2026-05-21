#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.schemas import AgentConfig
from src.frontend.cli import run_cli


def load_config() -> AgentConfig:
    import json

    config_paths = [
        Path.cwd() / "llm_machine.json",
        Path.cwd() / ".llm_machine.json",
        Path.home() / ".config/llm_machine/config.json",
    ]

    config = AgentConfig(
        model=os.getenv("OLLAMA_MODEL", "llama3.2"),
        provider=os.getenv("LLM_PROVIDER", "ollama"),
        ollama_host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        max_retries=int(os.getenv("MAX_RETRIES", "3")),
        workspace_dir=os.getenv("WORKSPACE_DIR", "."),
    )

    for cfg_path in config_paths:
        if cfg_path.exists():
            try:
                data = json.loads(cfg_path.read_text())
                for key, val in data.items():
                    if hasattr(config, key):
                        setattr(config, key, val)
                break
            except (json.JSONDecodeError, OSError):
                pass

    return config


def main():
    config = load_config()
    workspace = Path(config.workspace_dir).resolve()

    if not workspace.exists():
        print(f"Workspace {workspace} does not exist. Creating...")
        workspace.mkdir(parents=True, exist_ok=True)

    os.chdir(workspace)

    run_cli(config)


if __name__ == "__main__":
    main()
