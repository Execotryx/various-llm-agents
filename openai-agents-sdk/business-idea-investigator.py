from openai import OpenAI
from openai.types.responses import Response
from ai_config import AIConfig

class BusinessIdeaInvestigator:

    @property
    def _config(self) -> AIConfig:
        return self.__config

    @property
    def _client(self) -> OpenAI:
        return self.__client

    @property
    def _system_behavior(self) -> str:
        return self.__system_behavior

    @property
    def _last_response_id(self) -> str | None:
        return self.__last_response_id

    def __init__(self):
        self.__config: AIConfig = AIConfig()
        self.__client: OpenAI = OpenAI(api_key=self._config.api_key)
        self.__system_behavior: str = (
            "You are a business idea investigator. Your task is to analyze and provide insights on business ideas presented to you."
        )
        self.__last_response_id: str | None = None

    def ask_starting_question(self, question: str) -> Response:
        if not question:
            raise ValueError("Question cannot be empty.")

        response: Response = self._client.responses.create(
            model=self._config.model_name,
            input=question,
            reasoning={"effort": "medium"}
        )
        self.__last_response_id = response.id
        return response

    def ask_followup_question(self, question: str) -> Response:
        if not question:
            raise ValueError("Question cannot be empty.")

        if self._last_response_id is None:
            raise ValueError("No previous response to follow up on.")

        response: Response = self._client.responses.create(
            model=self._config.model_name,
            input=question,
            previous_response_id=self._last_response_id,
            reasoning={"effort": "medium"}
        )
        self.__last_response_id = response.id
        return response

    def investigate(self, idea: str) -> str:
        if not idea:
            raise ValueError("Business idea cannot be empty.")

        prompt: str = ("Investigate the following business idea and identify its pain-points.\n"
                  "Your response should contain only a bullet list of the problems and bottlenecks"
                  "that preventing the successful implementation of a said idea.\n"
                  f"Idea:\n\n###\n{idea}\n###\n\nPain points:\n")

        self.ask_starting_question(prompt)

        agentic_ai_solution_prompt: str = (
            "Based on the identified pain-points, propose potential solutions or strategies to overcome these challenges.\n"
            "Solution should involve application of Agentic AI technology."
            "Your response should contain only a bullet list of actionable solutions and software required to achiieve the Agentic AI solution.\n"
            "Agentic AI Solution:\n"
        )

        final: Response = self.ask_followup_question(agentic_ai_solution_prompt)
        
        return final.output_text

if __name__ == "__main__":
    investigator = BusinessIdeaInvestigator()
    idea: str = "Connection of local farmers directly with consumers for fresh produce delivery."
    insights = investigator.investigate(idea)
    print(f"Insights: {insights}")