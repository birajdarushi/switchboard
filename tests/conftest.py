"""Shared pytest fixtures. Everything runs offline (replay/fake) — no key needed."""
import dataclasses
import os

os.environ.setdefault("CASE_ID", "CEDX-7F3A")

import pytest

from cedx import config


@pytest.fixture
def cfg():
    return config.load()


@pytest.fixture
def cfg_fake(cfg):
    os.environ["ALLOW_FAKE_LLM"] = "1"
    return dataclasses.replace(cfg, replay_llm=False)
