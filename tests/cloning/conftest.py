"""Cloning fixtures: your own recording, derived sample variants, and guaranteed cleanup.

Brief rule: own data only, so the source must be your voice. Point at it with
`--sample PATH`, QA_SAMPLE=PATH, or drop it at samples/my_voice.wav.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from smallest_qa.waves import cloning


@pytest.fixture(scope="session")
def sample(pytestconfig) -> Path:
    path = Path(pytestconfig.getoption("--sample"))  # option defined in tests/conftest.py
    if not path.is_file():
        pytest.skip(f"no voice sample at {path} (record 10-15 s of your own voice)")
    return path


@pytest.fixture(scope="session")
def variant(sample, tmp_path_factory):
    """variant('name.ext', *ffmpeg_output_args) -> Path derived from your sample."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg not installed")
    out_dir = tmp_path_factory.mktemp("clone-samples")

    def make(name: str, *args: str, loop: bool = False) -> Path:
        out = out_dir / name
        if not out.exists():
            pre = ["-stream_loop", "-1"] if loop else []
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *pre, "-i", str(sample), *args, str(out)], check=True)
        return out

    return make


@pytest.fixture
def cleanup():
    """Register voice IDs a test created; they are deleted afterwards even if the test fails."""
    created: list[str] = []
    yield created
    for vid in created:
        cloning.delete(vid)
