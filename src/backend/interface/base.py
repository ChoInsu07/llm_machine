from abc import ABC, abstractmethod
from src.models.schemas import Message


class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: list[Message], tools: list[dict] | None = None) -> Message:
        ...

    @abstractmethod
    def chat_stream(self, messages: list[Message], tools: list[dict] | None = None):
        ...
