from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ImportTests(unittest.TestCase):
    def test_import_modes_without_ollama(self) -> None:
        cases = [
            (PROJECT_ROOT, "from tweet_generator.tweet_generator import TweetGenerator"),
            (PROJECT_ROOT / "tweet_generator", "import tweet_generator"),
        ]
        environment = os.environ.copy()
        environment["PYTHONNOUSERSITE"] = "1"
        for working_directory, statement in cases:
            with self.subTest(working_directory=working_directory):
                subprocess.run(
                    [sys.executable, "-c", statement],
                    cwd=working_directory,
                    env=environment,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )


if __name__ == "__main__":
    unittest.main()
