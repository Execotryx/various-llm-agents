from os import getenv
from os.path import dirname, join

from dotenv import load_dotenv


class OllamaAIConfig:
    """Configuration for a locally hosted Ollama server."""

    @property
    def model_name(self) -> str:
        return self.__model_name

    @model_name.setter
    def model_name(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Ollama model name cannot be empty.")
        self.__model_name = value.strip()

    @property
    def base_url(self) -> str:
        return self.__base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        if not value.strip():
            raise ValueError("Ollama base URL cannot be empty.")
        self.__base_url = value.strip().rstrip("/")

    def __init__(self) -> None:
        """Load Ollama settings from the repository-level ``.env`` file."""
        load_dotenv(
            override=True,
            dotenv_path=join(dirname(dirname(__file__)), ".env"),
        )

        self.__model_name = ""
        self.model_name = getenv("OLLAMA_MODEL_NAME", "lfm2.5-thinking:1.2b-q8_0")

        self.__base_url = ""
        self.base_url = getenv("OLLAMA_BASE_URL", "http://localhost:11434")
