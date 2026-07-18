from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import runpy
import sys
from threading import Lock
from time import sleep
from typing import Any
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables import RunnableLambda

from tweet_generator import tweet_generator as module
from tweet_generator.ollama_ai_config import OllamaAIConfig
from tweet_generator.tweet_generator import TweetGenerator, TweetGeneratorSettings


class RecordingModel:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []
        self.fail_on_call: int | None = None
        self.active = 0
        self.max_active = 0
        self._lock = Lock()

    def invoke(self, prompt: ChatPromptValue) -> AIMessage:
        contents = [str(message.content) for message in prompt.to_messages()]
        system = contents[0]
        if "bulleted list of critique" in system:
            kind = "reflect"
        elif "Revise the draft" in system:
            kind = "revise"
        else:
            kind = "generate"

        with self._lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)
            call_number = len(self.calls) + 1
            self.calls.append((kind, contents))
        try:
            if self.fail_on_call == call_number:
                raise RuntimeError(f"failure on call {call_number}")
            sleep(0.005)
            if kind == "generate":
                return AIMessage(content=f"generated:{contents[-1]}")
            return AIMessage(content=f"{kind}-{call_number}")
        finally:
            with self._lock:
                self.active -= 1


def make_config(
    model_name: str = "test-model",
    base_url: str = "http://test-ollama",
) -> OllamaAIConfig:
    config = OllamaAIConfig()
    config.model_name = model_name
    config.base_url = base_url
    return config


class TweetGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        module._clear_runtime_cache()
        self.config = make_config()
        self.recorder = RecordingModel()
        self.model_patch = patch.object(
            module,
            "_create_llm",
            lambda _key: RunnableLambda(self.recorder.invoke),
        )
        self.model_patch.start()

    def tearDown(self) -> None:
        self.model_patch.stop()
        module._clear_runtime_cache()

    def test_call_count_and_termination(self) -> None:
        for reflection_rounds, expected_calls in ((0, 1), (1, 3), (2, 5)):
            with self.subTest(reflection_rounds=reflection_rounds):
                module._clear_runtime_cache()
                self.recorder.calls.clear()
                generator = TweetGenerator(
                    self.config,
                    TweetGeneratorSettings(reflection_rounds=reflection_rounds),
                )

                result = generator("request")

                self.assertEqual(len(self.recorder.calls), expected_calls)
                self.assertEqual(
                    [kind for kind, _ in self.recorder.calls],
                    ["generate"] + ["reflect", "revise"] * reflection_rounds,
                )
                expected = (
                    "generated:request"
                    if reflection_rounds == 0
                    else f"revise-{expected_calls}"
                )
                self.assertEqual(result, expected)

    def test_each_round_uses_only_latest_draft_and_critique(self) -> None:
        generator = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=2),
        )
        self.assertEqual(generator("request"), "revise-5")

        first_reflection = self.recorder.calls[1][1]
        first_revision = self.recorder.calls[2][1]
        second_reflection = self.recorder.calls[3][1]
        second_revision = self.recorder.calls[4][1]
        self.assertEqual(len(first_reflection), 2)
        self.assertEqual(len(first_revision), 2)
        self.assertEqual(len(second_reflection), 2)
        self.assertEqual(len(second_revision), 2)
        self.assertIn("generated:request", first_reflection[-1])
        self.assertIn("reflect-2", first_revision[-1])
        self.assertIn("revise-3", second_reflection[-1])
        self.assertNotIn("generated:request", second_reflection[-1])
        self.assertIn("reflect-4", second_revision[-1])
        self.assertNotIn("reflect-2", second_revision[-1])

    def test_history_is_bounded_by_complete_turns(self) -> None:
        generator = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=0, max_history_turns=2),
        )
        for request in ("one", "two", "three", "four"):
            generator(request)

        fourth_prompt = self.recorder.calls[3][1]
        self.assertFalse(any("one" in content for content in fourth_prompt))
        self.assertTrue(any("two" in content for content in fourth_prompt))
        self.assertTrue(any("generated:two" in content for content in fourth_prompt))
        self.assertTrue(any("three" in content for content in fourth_prompt))
        self.assertEqual(fourth_prompt[-1], "four")
        self.assertEqual([turn.request for turn in generator.history], ["three", "four"])

    def test_zero_history_limit_retains_nothing(self) -> None:
        generator = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=0, max_history_turns=0),
        )
        generator("one")
        generator("two")
        self.assertEqual(generator.history, ())
        self.assertEqual(self.recorder.calls[1][1][-1], "two")
        self.assertFalse(any("one" in content for content in self.recorder.calls[1][1]))

    def test_failed_calls_do_not_commit_history(self) -> None:
        for failure_offset in (1, 2, 3):
            with self.subTest(failure_offset=failure_offset):
                module._clear_runtime_cache()
                self.recorder.calls.clear()
                self.recorder.fail_on_call = None
                generator = TweetGenerator(
                    self.config,
                    TweetGeneratorSettings(reflection_rounds=1),
                )
                generator("successful")
                self.recorder.fail_on_call = len(self.recorder.calls) + failure_offset

                with self.assertRaisesRegex(RuntimeError, "failure on call"):
                    generator("failed")

                self.assertEqual(
                    [turn.request for turn in generator.history],
                    ["successful"],
                )

    def test_matching_configuration_reuses_runtime_and_isolates_sessions(self) -> None:
        first = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=0),
        )
        second = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=2, max_history_turns=1),
        )
        self.assertIs(
            getattr(first, "_TweetGenerator__runtime"),
            getattr(second, "_TweetGenerator__runtime"),
        )
        first("first-only")
        second("second-only")
        self.assertEqual(first.history[0].request, "first-only")
        self.assertEqual(second.history[0].request, "second-only")

    def test_runtime_cache_is_bounded(self) -> None:
        runtimes = []
        for index in range(module._RUNTIME_CACHE_MAX_SIZE + 1):
            generator = TweetGenerator(make_config(model_name=f"model-{index}"))
            runtimes.append(getattr(generator, "_TweetGenerator__runtime"))
        self.assertEqual(len(module._RUNTIME_CACHE), module._RUNTIME_CACHE_MAX_SIZE)

        recreated = TweetGenerator(make_config(model_name="model-0"))
        self.assertIsNot(
            getattr(recreated, "_TweetGenerator__runtime"),
            runtimes[0],
        )

    def test_shared_runtime_serializes_concurrent_sessions(self) -> None:
        first = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=0),
        )
        second = TweetGenerator(
            self.config,
            TweetGeneratorSettings(reflection_rounds=0),
        )
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    lambda item: item[0](item[1]),
                    [(first, "A"), (second, "B")],
                )
            )
        self.assertEqual(sorted(results), ["generated:A", "generated:B"])
        self.assertEqual(self.recorder.max_active, 1)
        self.assertEqual(first.history[0].request, "A")
        self.assertEqual(second.history[0].request, "B")

    def test_settings_validation(self) -> None:
        invalid: list[tuple[dict[str, Any], type[Exception]]] = [
            ({"reflection_rounds": -1}, ValueError),
            ({"reflection_rounds": True}, TypeError),
            ({"max_history_turns": -1}, ValueError),
            ({"max_history_turns": False}, TypeError),
            ({"temperature": -0.1}, ValueError),
            ({"temperature": float("inf")}, ValueError),
            ({"temperature": True}, TypeError),
        ]
        for settings, exception in invalid:
            with self.subTest(settings=settings):
                with self.assertRaises(exception):
                    TweetGeneratorSettings(**settings)

    def test_empty_input_is_rejected_without_model_call(self) -> None:
        generator = TweetGenerator(self.config)
        for requested_content in ("", "   ", "\n\t"):
            with self.subTest(requested_content=requested_content):
                with self.assertRaisesRegex(ValueError, "cannot be empty"):
                    generator(requested_content)
        self.assertEqual(self.recorder.calls, [])

    def test_direct_debug_and_package_imports(self) -> None:
        from ollama_ai_config import OllamaAIConfig as CompatibilityConfig

        self.assertIs(CompatibilityConfig, OllamaAIConfig)
        script = Path(module.__file__).resolve()
        previous = sys.modules.pop("ollama_ai_config", None)
        original_path = list(sys.path)
        try:
            sys.path.insert(0, str(script.parent))
            namespace = runpy.run_path(str(script))
        finally:
            sys.path[:] = original_path
            sys.modules.pop("ollama_ai_config", None)
            if previous is not None:
                sys.modules["ollama_ai_config"] = previous
        self.assertIn("TweetGenerator", namespace)


if __name__ == "__main__":
    unittest.main()
