from typing import Any

if __package__ in (None, ""):
    from ollama_ai_config import OllamaAIConfig
else:
    from .ollama_ai_config import OllamaAIConfig

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama


class TweetGenerator:
    def __init__(self, ollama_config: OllamaAIConfig | None = None):
        self.__config: OllamaAIConfig = ollama_config if ollama_config is not None else OllamaAIConfig()
        self.__messages: list[HumanMessage | AIMessage] = []
        self.__generator_system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", (
                "# Role\n"
                "You are a Twitter expert assigned to create outstanding tweets.\n\n"
                "# Task\n"
                "Generate the most engaging and impactful tweet possible, based on the user request.\n"
                "If the user provides feedback, refine and enhance your previous attempts accordingly for maximum engagement.\n"
                "Respond only with a created tweet, nothing more."
            )), MessagesPlaceholder(variable_name="messages")
        ])

        self.__reflection_system_prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages([
            ("system", (
                "# Role\n"
                "You are a Twitter influencer, known for your engaging content and sharp insights.\n"
                "# Task\n"
                "Review and critique the user's tweet.\n"
                "Provide constructive feedback, focusing on enhancing its depth, style and overall impact.\n"
                "Offer specific suggestions to make the tweet more compelling and engaging for their audience.\n"
                "Respond only with a bulleted list of critique.\n\n"
            )),
            MessagesPlaceholder(variable_name="messages")
        ])

        self.__llm = ChatOllama(
            model=self.__config.model_name,
            base_url=self.__config.base_url,
            temperature=0.7,
        )
        
        self.__generate_chain = self.__generator_system_prompt | self.__llm
        self.__reflect_chain = self.__reflection_system_prompt | self.__llm

    def _tweet(self, requested_content: str) -> str | list[str | dict[Any, Any]]:
        request: HumanMessage = HumanMessage(content=requested_content)
        messages = [*self.__messages, request]
        draft: AIMessage = self.__generate_chain.invoke({"messages": messages})

        reflection_request = HumanMessage(content=(
            f"Original request:\n{requested_content}\n\n"
            f"Draft tweet:\n{draft.text}"
        ))
        reflection: AIMessage = self.__reflect_chain.invoke({
            "messages": [reflection_request]
        })

        revision_request = HumanMessage(content=(
            "Revise the draft using the critique below. "
            "Return only the revised tweet.\n\n"
            f"Draft tweet:\n{draft.text}\n\n"
            f"Critique:\n{reflection.text}"
        ))
        revision_messages = [*messages, draft, revision_request]
        response: AIMessage = self.__generate_chain.invoke({
            "messages": revision_messages
        })

        self.__messages.extend([request, response])
        return response.content;

    def __call__(self, requested_content: str) -> str | list[str | dict[Any, Any]]:
        return self._tweet(requested_content)


if __name__ == "__main__":
    generator: TweetGenerator = TweetGenerator()
    tweet = generator("Write a tweet about local AI")
    print(tweet)
