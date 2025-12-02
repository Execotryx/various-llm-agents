from os import getenv
from os.path import dirname, join
from dotenv import load_dotenv

class AIConfig:
    """Configuration class for AI settings."""

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        if not value:
            raise ValueError("API key cannot be empty.")
        self._api_key = value

    @property
    def model_name(self) -> str:
        return self.__model_name

    def __init__(self):
        load_dotenv(override=True, dotenv_path=join(dirname(dirname(__file__)), ".env"))  # Load environment variables from a .env file if present
        self._api_key: str = ""
        self.api_key = getenv("OPENAI_API_KEY", "")

        self.__model_name: str = getenv("OPENAI_MODEL_NAME", "gpt-5-nano")