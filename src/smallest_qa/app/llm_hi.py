"""Hindi script for the support agent, and how a Hindi reply is judged after a round trip through Pulse STT.

Text follows the docs' rule for Hindi (models__text-to-speech__best-practices.md, "Language and script"):
Hindi in Devanagari, English words in Latin script, as Indian support agents mix them (Hinglish). Replies carry
the content that stresses text normalisation: an order number, a DD/MM/YYYY date (Indian convention), a mobile
number and a rupee amount.

Judging a round trip honestly:
  - LOANWORDS: an English word may come back from Pulse in either script ("सपोर्ट" or "support"); both sides are
    mapped to one spelling. DIGIT_WORDS: a number may come back as digits or as Hindi/English digit words.
  - Entities (numbers, the date) are checked on their own against an explicit list of accepted readings, then
    removed from both sides, so the similarity score is about the words and the entity checks about the numbers.
"""

import difflib
from dataclasses import dataclass, field

from smallest_qa.app.llm import BRAND
from smallest_qa.waves.stt import normalize, similarity

BRAND_SAYS_HI = "क्विक ज़ेबरा विज़न एक्सप्रेस"  # long respelling: the dictionary's effect is measurable in seconds
BRAND_SAYS_LATIN = "quick zebra vision express"  # the English suite's respelling (fallback)
CALLER_VOICE = "ahan"  # stock Pro voice, Hindi (voices-languages.md: "Hindi | ahan (M) / rhea (F) | pass language: hi")

PREVIEW = "नमस्ते, सपोर्ट में आपका स्वागत है।"  # same sentence as the English suite's Hindi preview

CALLER = [  # what the (synthetic) Hindi caller says, turn by turn
    "नमस्ते, मेरा ऑर्डर अभी तक नहीं पहुँचा है। क्या आप चेक कर सकते हैं?",
    "क्या delivery शनिवार सुबह हो सकती है? और confirmation मुझे SMS पर भेज दीजिए।",
    "और मेरे पिछले order का refund कब तक आएगा?",
]


@dataclass(frozen=True)
class Reply:
    text: str
    entities: dict = field(default_factory=dict)  # name -> (text as written, accepted readings in the transcript)


DAY_FIRST = ("5 दिसंबर", "दिसंबर 5", "5 december", "december 5")  # 05/12/2026 read the Indian way
MONTH_FIRST = ("मई", "may")  # 05/12/2026 read US-style ("May 12")

SCRIPT = [  # opening sentences of 4-5 words, like the English script, so first-audio times compare
    Reply(f"{BRAND} सपोर्ट में आपका स्वागत है। आपका ऑर्डर नंबर 48213 कल शिप हो गया है, "
          "और यह 05/12/2026 तक आपके पास पहुँच जाएगा।",
          {"order": ("48213", ("48213", "अड़तालीस हज़ार दो सौ तेरह", "48 हज़ार 213")),
           "date": ("05/12/2026", DAY_FIRST)}),
    Reply("जी बिल्कुल, यह हो जाएगा। आपकी delivery अब शनिवार सुबह नौ से बारह बजे के बीच होगी। "
          "Confirmation का SMS आपके number 98765 43210 पर आ जाएगा।",
          {"mobile": ("98765 43210", ("9876543210",))}),
    Reply(f"आपका refund process हो गया है। ₹1,499 पाँच से सात working days में आपके account में आ जाएगा। "
          f"{BRAND} चुनने के लिए धन्यवाद।",
          {"amount": ("₹1,499", ("1499", "एक हज़ार चार सौ निन्यानवे", "चौदह सौ निन्यानवे", "1 हज़ार 499"))}),
]

INTERRUPTIBLE = (  # long enough to be interrupted mid-answer
    "हमारी पूरी refund policy इस तरह है। Refund पाँच कार्य दिवसों में process होते हैं। सामान बिना इस्तेमाल "
    "किया हुआ और अपनी असली packing में होना चाहिए। Shipping का खर्च तभी वापस मिलता है जब सामान खराब हालत में पहुँचा हो।"
)
AFTER_BARGE_IN = "जी, बोलिए। और क्या मदद करूँ?"

# one sentence long enough to be released on its own (continuations.md, "How buffering works" rule 2)
BOUNDARY_FIRST = "आपका refund आज शुरू हो गया है और पैसे जल्द ही आपके खाते में दिखने लगेंगे"
BOUNDARY_REST = "धन्यवाद।"

LOANWORDS = {  # Devanagari spelling -> Latin spelling Pulse may use instead
    "सपोर्ट": "support", "ऑर्डर": "order", "आर्डर": "order", "शिप": "ship", "डिलीवरी": "delivery",
    "डिलिवरी": "delivery", "कन्फर्मेशन": "confirmation", "कंफर्मेशन": "confirmation", "एसएमएस": "sms",
    "नंबर": "number", "नम्बर": "number", "रिफंड": "refund", "प्रोसेस": "process", "वर्किंग": "working",
    "डेज़": "days", "अकाउंट": "account", "एकाउंट": "account", "कॉल": "call", "चेक": "check", "पॉलिसी": "policy",
    "पैकिंग": "packing", "शिपिंग": "shipping", "क्विक": "quick", "ज़ेबरा": "zebra", "विज़न": "vision",
    "एक्सप्रेस": "express",
}
DIGIT_WORDS = {
    "शून्य": "0", "ज़ीरो": "0", "zero": "0", "एक": "1", "one": "1", "दो": "2", "two": "2", "तीन": "3",
    "three": "3", "चार": "4", "four": "4", "पाँच": "5", "five": "5", "छह": "6", "छः": "6", "छे": "6", "six": "6",
    "सात": "7", "seven": "7", "आठ": "8", "eight": "8", "नौ": "9", "nine": "9",
}
ALIASES = {**LOANWORDS, **DIGIT_WORDS}

# Runaway guard. Normal speech is ~0.06-0.075 s per character (English suite turns; stock Hindi voice clips);
# a clone speaking Hindi has produced 128 s of audio for one 76-character sentence.
PER_CHAR_S, SLACK_S = 0.15, 1.0


def plausible_s(text: str) -> float:
    """Longest audio (s) that is still plausible speech for `text`: about twice a normal speaking rate."""
    return round(PER_CHAR_S * len(text) + SLACK_S, 1)


def spoken(text: str, brand_says: str | None) -> str:
    """What the caller should hear: the brand as the active dictionary respells it."""
    return text.replace(BRAND, brand_says) if brand_says else text


def judge(reply: Reply, heard: str, brand_says: str | None = None) -> dict:
    """Score one agent reply as transcribed by Pulse (language=hi).

    similarity  words only: loanword/digit-word aware, entities removed from both sides
    plain       the English suite's scoring of the same pair (no aliases, nothing removed), for comparison
    entities    {name: accepted reading found}; "date" means read day-first (5 December)
    month_first the date came back as May (US order)
    """
    expected = spoken(reply.text, brand_says)
    h = normalize(heard, ALIASES)
    found = {}
    for name, (written, readings) in reply.entities.items():
        expected = expected.replace(written, " ")
        hit = next((normalize(r, ALIASES) for r in readings if normalize(r, ALIASES) in h), None)
        found[name] = hit is not None
        if hit:
            h = h.replace(hit, "", 1)
    sim = difflib.SequenceMatcher(None, normalize(expected, ALIASES), h).ratio()
    heard_words = {normalize(w) for w in heard.split()}
    month_first = "date" in found and not found["date"] and bool(heard_words & set(MONTH_FIRST))
    return {"similarity": round(sim, 2), "plain": similarity(spoken(reply.text, brand_says), heard),
            "entities": found, "month_first": month_first}
