"""A scripted stand-in for the LLM: fixed replies streamed word by word with LLM-like timing.

Keeps runs repeatable and free of third-party calls; the agent code consumes it exactly like a real token stream.
"""

import asyncio
from collections.abc import AsyncIterator

BRAND = "Qzvx"  # a made-up brand name: only a pronunciation dictionary can say it right

SCRIPT = [
    f"Thanks for calling {BRAND} support. I can see your order from last Tuesday. It shipped this morning "
    "and should reach you by Friday before noon.",
    "Of course. I have moved the delivery to Saturday between nine and twelve. You will get a text message "
    "with the new time slot shortly.",
    f"You are welcome. Is there anything else I can help you with today? {BRAND} is always here to help.",
]

INTERRUPTIBLE = (  # long enough to be interrupted mid-answer
    "Let me walk you through the full refund policy. Refunds are processed within five business days. "
    "Items must be unused and in their original packaging. Shipping costs are not refunded unless the item "
    "arrived damaged. You can start a return from the orders page at any time."
)


class ScriptedLLM:
    def __init__(self, first_token_ms: float = 350, token_ms: float = 35):
        self.first_token_ms, self.token_ms = first_token_ms, token_ms

    async def stream(self, reply: str) -> AsyncIterator[str]:
        """Yield the reply as word tokens (with their leading space), after a first-token delay."""
        await asyncio.sleep(self.first_token_ms / 1000)
        for i, word in enumerate(reply.split(" ")):
            yield word if i == 0 else " " + word
            await asyncio.sleep(self.token_ms / 1000)

    def reply(self, turn: int) -> str:
        return SCRIPT[turn % len(SCRIPT)]
