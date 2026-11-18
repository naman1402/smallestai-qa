"""Shared pytest setup.

- Every test outside tests/unit is marked `live` and skipped when no API key is set.
- Each test's node ID is stamped on the evidence it produces, so a failing assertion
  can be traced to its exact requests in evidence/<date>.jsonl.
"""

import os
from pathlib import Path

import pytest

from smallest_qa.config import ROOT, settings
from smallest_qa.utils import evidence

UNIT_DIR = Path(__file__).parent / "unit"


def pytest_addoption(parser):
    parser.addoption("--sample", default=os.environ.get("QA_SAMPLE", str(ROOT / "samples" / "my_voice.wav")),
                     help="your own 10-15 s voice recording, used by tests/cloning")


def pytest_collection_modifyitems(config, items):
    no_key = pytest.mark.skip(reason="SMALLEST_API_KEY not set (see .env.example)")
    for item in items:
        if UNIT_DIR not in Path(item.fspath).parents:
            item.add_marker(pytest.mark.live)
            if not settings.api_key:
                item.add_marker(no_key)


@pytest.fixture(autouse=True)
def _evidence_context(request):
    evidence.set_test(request.node.nodeid)
    yield
    evidence.set_test("manual")
