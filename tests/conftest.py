import pytest


@pytest.fixture(autouse=True)
def immediate_first_prompt(monkeypatch):
    # The demo waits 10 s before the first guide question; tests do not.
    monkeypatch.setenv("FIRSTFIVE_FIRST_PROMPT_DELAY", "0")
