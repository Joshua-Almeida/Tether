import os

import pytest

from app.config import get_settings

pytestmark = pytest.mark.llm


def test_settings_see_a_chat_key():
    if not (os.environ.get("FASTROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")):
        if not get_settings().llm_configured:
            pytest.skip("no LLM keys in env")
    assert get_settings().llm_configured
