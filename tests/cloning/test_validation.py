"""Clone upload: POST /waves/v1/voice-cloning accepts a valid WAV whatever MIME label the client sends.

Contract: docs/reference/smallest-docs-2026-11-18/models__voice-cloning__instant-clone-api.md
  "Supported types: .mp3, .wav, .mp4, .webm" (file types, no MIME list). Evidence: finding C2 in
  evidence/2026-11-18-cloning-findings.md.
"""

import pytest

from smallest_qa.utils.evidence import RUN_ID
from smallest_qa.waves import cloning

pytestmark = pytest.mark.clone


@pytest.mark.parametrize("mime", ["audio/x-wav", "audio/vnd.wave"])
def test_valid_wav_is_accepted_under_common_mime_labels(mime, variant, cleanup):
    """The docs list supported file types (.wav), not MIME labels. audio/x-wav is the most common WAV label and
    audio/vnd.wave is the IANA one (Python 3.14 mimetypes); the same bytes as audio/wav must be accepted."""
    path = variant("ok.wav", "-ac", "1", "-ar", "24000", "-t", "12")
    ex = cloning.create(path, name=f"qa-mime-{RUN_ID}", mime=mime, language="en", model="lightning-v3.1-pro")
    vid = cloning.voice_id(ex)
    if vid:
        cleanup.append(vid)
    assert ex.status == 200, f"valid WAV labelled {mime} rejected: {ex}"
