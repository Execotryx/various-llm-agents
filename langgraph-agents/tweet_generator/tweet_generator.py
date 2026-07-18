from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass
from math import isfinite
from numbers import Real
from pathlib import Path
from threading import RLock
from typing import Any, TypedDict

if __package__ in (None, ""):
    from ollama_ai_config import OllamaAIConfig
else:
    from .ollama_ai_config import OllamaAIConfig

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph


@dataclass(frozen=True, slots=True)
class TweetGeneratorSettings:
    """Performance and session limits for a tweet generator."""

    reflection_rounds: int = 1
    max_history_turns: int = 4
    temperature: float = 0.7

    def __post_init__(self) -> None:
        if isinstance(self.reflection_rounds, bool) or not isinstance(
            self.reflection_rounds, int
        ):
            raise TypeError("reflection_rounds must be an integer.")
        if self.reflection_rounds < 0:
            raise ValueError("reflection_rounds cannot be negative.")

        if isinstance(self.max_history_turns, bool) or not isinstance(
            self.max_history_turns, int
        ):
            raise TypeError("max_history_turns must be an integer.")
        if self.max_history_turns < 0:
            raise ValueError("max_history_turns cannot be negative.")

        if isinstance(self.temperature, bool) or not isinstance(self.temperature, Real):
            raise TypeError("temperature must be a real number.")
        temperature = float(self.temperature)
        if not isfinite(temperature) or temperature < 0:
            raise ValueError("temperature must be a finite, non-negative number.")
        object.__setattr__(self, "temperature", temperature)


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """One complete successful request/response pair."""

    request: str
    response: str


class TweetState(TypedDict):
    history: tuple[ConversationTurn, ...]
    current_request: str
    current_draft: str
    latest_critique: str
    completed_rounds: int
    reflection_rounds: int


class TweetStateUpdate(TypedDict, total=False):
    current_draft: str
    latest_critique: str
    completed_rounds: int


@dataclass(frozen=True, slots=True)
class _RuntimeKey:
    model_name: str
    base_url: str
    temperature: float


@dataclass(frozen=True, slots=True)
class _TweetRuntime:
    """Immutable, shareable model workflow plus a conservative invoke lock."""

    graph: Any
    invoke_lock: RLock


_RUNTIME_CACHE_MAX_SIZE = 8
_RUNTIME_CACHE: OrderedDict[_RuntimeKey, _TweetRuntime] = OrderedDict()
_RUNTIME_CACHE_LOCK = RLock()
_PROMPTS_DIRECTORY = Path(__file__).with_name("prompts")


def _load_system_prompt(filename: str) -> str:
    return (_PROMPTS_DIRECTORY / filename).read_text(encoding="utf-8").strip()


def _create_llm(key: _RuntimeKey) -> ChatOllama:
    return ChatOllama(
        model=key.model_name,
        base_url=key.base_url,
        temperature=key.temperature,
    )


def _message_text(message: BaseMessage) -> str:
    if not isinstance(message, AIMessage):
        raise TypeError("The Ollama workflow must return an AI message.")
    return message.text


def _history_messages(history: tuple[ConversationTurn, ...]) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    for turn in history:
        messages.extend(
            [HumanMessage(content=turn.request), AIMessage(content=turn.response)]
        )
    return messages


def _build_runtime(key: _RuntimeKey) -> _TweetRuntime:
    generator_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                _load_system_prompt("generate-system.md"),
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    reflection_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                _load_system_prompt("reflect-system.md"),
            ),
            (
                "human",
                "Original request:\n{current_request}\n\n"
                "Draft tweet:\n{current_draft}",
            ),
        ]
    )
    revision_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                _load_system_prompt("revise-system.md"),
            ),
            (
                "human",
                "Original request:\n{current_request}\n\n"
                "Current draft:\n{current_draft}\n\n"
                "Critique:\n{latest_critique}",
            ),
        ]
    )

    llm = _create_llm(key)
    generate_chain = generator_prompt | llm
    reflect_chain = reflection_prompt | llm
    revise_chain = revision_prompt | llm

    def generate_draft(state: TweetState) -> TweetStateUpdate:
        messages = _history_messages(state["history"])
        messages.append(HumanMessage(content=state["current_request"]))
        response = generate_chain.invoke({"messages": messages})
        return {
            "current_draft": _message_text(response),
            "latest_critique": "",
        }

    def reflect(state: TweetState) -> TweetStateUpdate:
        response = reflect_chain.invoke(
            {
                "current_request": state["current_request"],
                "current_draft": state["current_draft"],
            }
        )
        return {"latest_critique": _message_text(response)}

    def revise(state: TweetState) -> TweetStateUpdate:
        response = revise_chain.invoke(
            {
                "current_request": state["current_request"],
                "current_draft": state["current_draft"],
                "latest_critique": state["latest_critique"],
            }
        )
        return {
            "current_draft": _message_text(response),
            "latest_critique": "",
            "completed_rounds": state["completed_rounds"] + 1,
        }

    def after_draft(state: TweetState) -> str:
        return END if state["reflection_rounds"] == 0 else "reflect"

    def after_revision(state: TweetState) -> str:
        if state["completed_rounds"] >= state["reflection_rounds"]:
            return END
        return "reflect"

    graph_builder = StateGraph(TweetState)
    graph_builder.add_node("generate_draft", generate_draft)
    graph_builder.add_node("reflect", reflect)
    graph_builder.add_node("revise", revise)
    graph_builder.add_edge(START, "generate_draft")
    graph_builder.add_conditional_edges(
        "generate_draft",
        after_draft,
        {"reflect": "reflect", END: END},
    )
    graph_builder.add_edge("reflect", "revise")
    graph_builder.add_conditional_edges(
        "revise",
        after_revision,
        {"reflect": "reflect", END: END},
    )
    return _TweetRuntime(graph=graph_builder.compile(), invoke_lock=RLock())


def _get_runtime(key: _RuntimeKey) -> _TweetRuntime:
    # Build under the cache lock so concurrent constructors cannot duplicate a
    # heavyweight client/graph for the same immutable configuration.
    with _RUNTIME_CACHE_LOCK:
        runtime = _RUNTIME_CACHE.get(key)
        if runtime is None:
            runtime = _build_runtime(key)
            _RUNTIME_CACHE[key] = runtime
            if len(_RUNTIME_CACHE) > _RUNTIME_CACHE_MAX_SIZE:
                _RUNTIME_CACHE.popitem(last=False)
        else:
            _RUNTIME_CACHE.move_to_end(key)
        return runtime


def _clear_runtime_cache() -> None:
    """Clear shared runtimes for deterministic tests."""

    with _RUNTIME_CACHE_LOCK:
        _RUNTIME_CACHE.clear()


class TweetGenerator:
    def __init__(
        self,
        ollama_config: OllamaAIConfig | None = None,
        settings: TweetGeneratorSettings | None = None,
    ) -> None:
        config = ollama_config if ollama_config is not None else OllamaAIConfig()
        self.__settings = settings if settings is not None else TweetGeneratorSettings()
        self.__history: deque[ConversationTurn] = deque(
            maxlen=self.__settings.max_history_turns
        )
        self.__session_lock = RLock()
        self.__runtime = _get_runtime(
            _RuntimeKey(
                model_name=config.model_name,
                base_url=config.base_url,
                temperature=self.__settings.temperature,
            )
        )

    @property
    def settings(self) -> TweetGeneratorSettings:
        return self.__settings

    @property
    def history(self) -> tuple[ConversationTurn, ...]:
        with self.__session_lock:
            return tuple(self.__history)

    def _tweet(self, requested_content: str) -> str:
        if not isinstance(requested_content, str):
            raise TypeError("requested_content must be a string.")
        current_request = requested_content.strip()
        if not current_request:
            raise ValueError("requested_content cannot be empty.")

        # Serialize calls on one session so each request sees a coherent history.
        # The shared runtime lock is a safe fallback for clients/runnables whose
        # installed versions do not guarantee concurrent invocation safety.
        with self.__session_lock, self.__runtime.invoke_lock:
            state: TweetState = {
                "history": tuple(self.__history),
                "current_request": current_request,
                "current_draft": "",
                "latest_critique": "",
                "completed_rounds": 0,
                "reflection_rounds": self.__settings.reflection_rounds,
            }
            result = self.__runtime.graph.invoke(state)
            response = result["current_draft"]
            if not isinstance(response, str):
                raise TypeError("The reflection graph must finish with text.")

            # Commit only after every model call succeeds, preserving rollback on
            # any exception raised by generation, reflection, or revision.
            self.__history.append(
                ConversationTurn(request=current_request, response=response)
            )
            return response

    def __call__(self, requested_content: str) -> str:
        return self._tweet(requested_content)


if __name__ == "__main__":
    generator = TweetGenerator()
    tweet = generator("Write a tweet about local AI")
    print(tweet)
