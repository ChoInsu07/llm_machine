import json
import requests
from typing import Optional
from src.models.schemas import Message, Role
from .base import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2"):
        self.host = host.rstrip("/")
        self.model = model
        self.chat_url = f"{self.host}/api/chat"

    def _format_messages(self, messages: list[Message]) -> list[dict]:
        return [
            {
                "role": m.role.value,
                "content": m.content,
            }
            for m in messages
        ]

    def chat(self, messages: list[Message], tools: list[dict] | None = None) -> Message:
        body = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "stream": False,
        }
        if tools:
            body["tools"] = tools

        resp = requests.post(self.chat_url, json=body, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        msg = data.get("message", {})
        content = msg.get("content", "")
        tool_calls = []

        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            raw_args = fn.get("arguments", {})
            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    raw_args = {}
            tool_calls.append({
                "name": fn.get("name", ""),
                "arguments": raw_args,
            })

        return Message(
            role=Role.ASSISTANT,
            content=content,
            tool_calls=tool_calls,
        )

    def chat_stream(self, messages: list[Message], tools: list[dict] | None = None):
        body = {
            "model": self.model,
            "messages": self._format_messages(messages),
            "stream": True,
        }
        if tools:
            body["tools"] = tools

        resp = requests.post(self.chat_url, json=body, stream=True, timeout=120)
        resp.raise_for_status()

        full_content = ""
        tool_calls = []

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "message" in data:
                msg = data["message"]
                delta = msg.get("content", "")
                if delta:
                    full_content += delta
                    yield {"type": "content", "text": delta}

                for tc in msg.get("tool_calls", []):
                    fn = tc.get("function", {})
                    raw_args = fn.get("arguments", {})
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            pass
                    tool_calls.append({
                        "name": fn.get("name", ""),
                        "arguments": raw_args,
                    })

            if data.get("done", False):
                yield {"type": "done", "content": full_content, "tool_calls": tool_calls}
                return

    def check_available(self) -> bool:
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False
