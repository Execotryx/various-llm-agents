import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ollama_ai_config import OllamaAIConfig
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama


class TweetGenerator:
    def __init__(self, ollama_config: OllamaAIConfig | None = None):
        self.__config: OllamaAIConfig = ollama_config if ollama_config is not None else OllamaAIConfig()
        self.__messages: list[HumanMessage | AIMessage] = []
        self.__system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", (
                "# Role\n"
                "You are a Twitter expert assigned to create outstanding tweets.\n\n"
                "# Task\n"
                "Generate the most engaging and impactful tweet possible, based on the user request.\n"
                "If the user provides feedback, refine and enhance your previous attempts accordingly for maximum engagement.\n"
                "Respond only with a created tweet, nothing more."
            )), MessagesPlaceholder(variable_name="messages")
        ])

        self.__llm = ChatOllama(
            model=self.__config.model_name,
            base_url=self.__config.base_url,
            temperature=0.7,
        )
        self.__generate_chain = self.__system_prompt | self.__llm

    def _tweet(self, requested_content: str) -> str | list[str | dict[Any, Any]]:
        request: HumanMessage = HumanMessage(content=requested_content)
        messages = [*self.__messages, request]
        response: AIMessage = self.__generate_chain.invoke({"messages": messages})
        self.__messages.extend([request, response])
        return response.content;

    def __call__(self, requested_content: str) -> str | list[str | dict[Any, Any]]:
        return self._tweet(requested_content)


if __name__ == "__main__":
    generator: TweetGenerator = TweetGenerator()
    tweet = generator("Write a tweet about local AI")
    print(tweet)
