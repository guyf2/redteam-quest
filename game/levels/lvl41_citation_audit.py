import json
import pathlib

TITLE = "Audit the citations: which ones are real?"
WORLD = "craft"
KIND = "audit"
MODE = "audit"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/07-craft/lvl41_citations.json"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl41_citations.json"
EMPTY_MARK = '"verdict": ""'

ANSWER = """[1] AcmeShop offers free returns within 45 days of purchase.
[2] The support team is available 24/7, including holidays.
[3] AcmeShop ships to over 30 countries worldwide.
[4] Approved refunds are processed within 2 business days.
[5] AcmeShop's loyalty program gives customers 5% cash back on every purchase.
[6] Orders over $50 qualify for free standard shipping."""
SOURCES = {
    1: "Return Policy: Items may be returned within 30 days of delivery for a full refund, provided the item is unused.",
    2: "Support Hours: Our support team is available 9am to 5pm, Monday to Friday, excluding public holidays.",
    3: "Shipping FAQ: AcmeShop currently ships to 32 countries worldwide, with new destinations added regularly.",
    4: "Refund Timeline: Once a refund is approved, it is processed within 2 business days back to the original payment method.",
    5: "Loyalty Program: Members earn 1 point for every dollar spent, redeemable for discounts on future orders.",
    6: "Shipping FAQ: Free standard shipping applies automatically to orders over $50.",
}
EXPECT = {1: "fabricated", 2: "fabricated", 3: "genuine", 4: "genuine", 5: "fabricated", 6: "genuine"}

INTRO = ("A RAG assistant answered a customer with six numbered citations, each pointing at a real source document. "
         "RAG answers look trustworthy because they cite sources, but a citation number only proves the assistant POINTED at a document, "
         "not that the document actually says what the assistant claims. Find the citations that do not hold up.")
CONCEPT = """FABRICATED CITATIONS are a specific, checkable failure mode, different from a plain hallucination: the assistant names a real, existing source, but the claim next to the citation number either is not supported by that source, or outright contradicts it. A reader who never opens the source sees a confident number and assumes the claim is backed. That is worse than no citation at all, because it borrows the credibility of a real document for a claim the document never made.

Auditing citations is a close-reading skill, not a vibe check:
  1. Read the CLAIM next to each citation number carefully, including its exact numbers, dates and conditions.
  2. Read the cited SOURCE for that number.
  3. Ask: does the source state this, a strictly weaker version of this, or something different? A claim that adds, inflates, or changes a number, a condition, or a scope beyond what the source says is FABRICATED, even if the topic matches. A claim that accurately restates (or safely narrows) what the source says is GENUINE.

Below is the assistant's answer and the six source documents it cited. For each citation, decide GENUINE or FABRICATED and write one sentence saying exactly what in the source does or does not support the claim, pointing at the specific mismatch (a number, a condition, a scope) when it is fabricated."""
WIN = "At least 5 of the 6 verdicts must be correct, with a one-sentence rationale (10+ words) for each that names the specific supporting or contradicting detail."
BRIEF = (INTRO + "\n\n" + CONCEPT + "\n\nTHE ASSISTANT'S ANSWER\n" + ANSWER + "\n\nTHE SOURCE DOCUMENTS\n" +
         "\n".join(f"  [{k}] {v}" for k, v in SOURCES.items()) + "\n\n" + WIN)

VIZ = []
SPEC_PLACEHOLDER = "Give your agent the answer, the sources, and the verdict scale. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Give it the material", "Here is the assistant's answer with six citations, and the six source documents it cites: " + ANSWER.replace("\n", " ") + " SOURCES: " + " ".join(f"[{k}] {v}" for k, v in SOURCES.items())),
    ("Verdict scale", "For each citation 1-6, fill the JSON file with verdict (exactly 'genuine' or 'fabricated') and a one-sentence why (10+ words) naming the specific matching or mismatching detail."),
    ("Close reading, not vibes", "Compare the claim's exact numbers, dates and conditions against what the source actually states. A claim that inflates, adds or changes a number or condition beyond the source is fabricated, even if the general topic matches."),
    ("Do not guess from topic alone", "A citation pointing at a real, relevant document is not automatically genuine; check whether that specific document supports that specific claim."),
]
SPEC_CHECKS = [
    ("Provides the answer and sources", r"citation|source|return policy|support hours|shipping|refund|loyalty"),
    ("Defines the verdict scale", r"genuine|fabricated"),
    ("Demands close reading", r"exact|number|date|condition|specific|compare|mismatch"),
    ("Warns against topic-only guessing", r"topic alone|not automatically|does not mean|guess"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The file must stay valid JSON.")

QUIZ = [
    ('Why can a fabricated citation be more misleading than an answer with no citation at all?',
     ['Citations always slow readers down', "It borrows the credibility of a real, checkable source for a claim that source never actually made", 'Numbered citations are harder to read'], 1,
     'A citation signals "verified", so a false one actively misleads rather than just omitting support.'),
    ('Citation [1] claims 45-day free returns; the source says 30 days. This citation is...',
     ['Genuine, since both are about returns', 'Fabricated: the source supports a weaker, different claim (30 days), and the answer inflated the number', 'Unverifiable'], 1,
     'A changed number is exactly the kind of mismatch that makes a citation fabricated even though the topic matches.'),
    ('What is the right way to check whether a citation is genuine?',
     ['Check whether the cited document exists', 'Check whether the cited document actually supports the specific claim next to the citation, not just the general topic', 'Check how confidently the answer is worded'], 1,
     'Existence of the source and relevance to the topic are necessary but not sufficient; the claim itself must be verified against the text.'),
    ('A claim exactly restates what its cited source says, with no added numbers or conditions. This citation is...',
     ['Fabricated, since it adds no new information', 'Genuine: an accurate restatement is exactly what a citation should be', 'Unverifiable without the original author'], 1,
     'Genuine citations are not required to add anything; faithfully reflecting the source is the bar.'),
]
HINTS = [
    "Read each claim's exact number or condition, then the matching source, and ask whether the source states that exact thing.",
    "Citations 1, 2 and 5 each change a specific detail from their source (a day count, hours, or a reward structure) while staying on-topic: that is the fabricated pattern.",
    "Citations 3, 4 and 6 restate their source's numbers and conditions exactly: that is what a genuine citation looks like.",
]


def check(path=STUB):
    try:
        data = json.loads(pathlib.Path(path).read_text())
    except Exception as e:
        return False, f"SYMPTOM: the file is not valid JSON ({type(e).__name__}: {e})."
    problems, good = [], 0
    for k in EXPECT:
        key = str(k)
        e = data.get(key) if isinstance(data, dict) else None
        if not isinstance(e, dict) or e.get("verdict", "").strip().lower() not in ("genuine", "fabricated"):
            problems.append(f"SYMPTOM: citation [{k}] has no valid verdict (use exactly 'genuine' or 'fabricated').")
            continue
        verdict = e["verdict"].strip().lower()
        if len(str(e.get("why", "")).split()) < 10:
            problems.append(f"SYMPTOM: the rationale for citation [{k}] is too short: write a real sentence (10+ words) naming the specific detail.")
            continue
        if verdict == EXPECT[k]:
            good += 1
        else:
            problems.append(f"SYMPTOM: citation [{k}] is marked {verdict}, but re-read source [{k}] against the exact claim.")
    distinct = len({str(data.get(str(k), {}).get("verdict", "")).strip().lower() for k in EXPECT})
    if distinct < 2:
        problems.append("SYMPTOM: every citation got the same verdict; real citation sets mix genuine and fabricated ones.")
    out = f"{good}/6 verdicts correct."
    if good < 5 or problems:
        return False, out + "\n  " + "\n  ".join(problems[:6])
    return True, out + "\n\nYou can tell a real source from a borrowed one: the test that matters for trusting any RAG answer."


def viz_api(name, q):
    return {}
