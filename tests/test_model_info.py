import asyncio
import sys
from pathlib import Path

import pytest
from autogen_ext.models.openai import OpenAIChatCompletionClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import configured_model_info


CUSTOM_MODEL = "provider-custom-model"
CUSTOM_INFO = {
    "vision": False,
    "function_calling": True,
    "json_output": False,
    "structured_output": False,
    "family": "unknown",
}


def test_custom_identifier_needs_explicit_autogen_model_info() -> None:
    with pytest.raises(ValueError, match="model_info is required"):
        OpenAIChatCompletionClient(model=CUSTOM_MODEL, api_key="offline-test-key")


def test_custom_model_info_constructs_client_offline() -> None:
    client = OpenAIChatCompletionClient(
        model=CUSTOM_MODEL,
        api_key="offline-test-key",
        model_info=CUSTOM_INFO,
    )
    asyncio.run(client.close())


def test_model_info_environment_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEAVZ_MODEL_INFO", '{"vision": false, "function_calling": true, "json_output": false, "structured_output": false, "family": "unknown"}')
    assert configured_model_info() == CUSTOM_INFO


def test_model_info_environment_rejects_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WEAVZ_MODEL_INFO", "not-json")
    with pytest.raises(RuntimeError, match="valid JSON"):
        configured_model_info()
