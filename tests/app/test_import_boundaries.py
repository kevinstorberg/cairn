import json
import os
import subprocess
import sys


def test_app_import_does_not_load_optional_backend_modules():
    code = """
import json
import sys

import src.app  # noqa: F401

blocked = [
    "boto3",
    "langchain_aws",
    "langchain_anthropic",
    "langchain_openai",
    "langchain_pinecone",
    "langgraph.checkpoint.postgres",
    "pgvector",
    "pinecone",
    "pymongo",
    "redis",
    "sentence_transformers",
]
print(json.dumps([module for module in blocked if module in sys.modules]))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        env={**os.environ, "APP_ENV": "test"},
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == []
