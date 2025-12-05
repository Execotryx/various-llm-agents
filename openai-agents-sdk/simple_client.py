from openai import OpenAI
from openai.types.responses import Response
from ai_config import AIConfig

class SimpleClient:

    @property
    def _config(self) -> AIConfig:
        return self.__config

    @property
    def _client(self) -> OpenAI:
        return self.__client

    @property
    def _last_response_id(self) -> str | None:
        return self.__last_response_id

    def __init__(self):
        self.__config: AIConfig = AIConfig()
        self.__client: OpenAI = OpenAI(api_key=self._config.api_key)
        self.__last_response_id: str | None = None

    def ask(self, prompt: str) -> str:
        if self._last_response_id is None:
            response: Response = self._client.responses.create(
                model=self._config.model_name,
                input=prompt, 
                reasoning={"effort": "low"}
            )
        else:
            response: Response = self._client.responses.create(
                model=self._config.model_name,
                input=prompt,
                previous_response_id=self._last_response_id,
                reasoning={"effort": "low"}
            )
        self.__last_response_id = response.id
        return response.output_text

if __name__ == "__main__":
    client = SimpleClient()
    answer = client.ask("What is 2+2?")
    print(f"Answer: {answer}")
    answer = client.ask("Please propose a hard, challenging question to assess someone's IQ. Respond only with the question.\nQuestion: ")
    print(f"Answer: {answer}")