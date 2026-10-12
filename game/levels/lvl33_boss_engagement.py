import json
import pathlib
import re

TITLE = "BOSS: deliver the engagement"
WORLD = "craft"
KIND = "boss"
MODE = "delegate"
XP = 120
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/08-boss/lvl33_engagement.json"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl33_engagement.json"
EMPTY_MARK = r'"findings":\s*\[\s*\]'
SECRETS = ["Winter2026!", "acct-9981-ATTACKER"]
SEV = ["info", "low", "medium", "high", "critical"]
EXPECT = {"N1": {"critical"}, "N5": {"high"}, "N7": {"high", "medium"}, "N9": {"medium", "low"}, "N3": {"low"}}
EXCLUDE = {"N2": "duplicate", "N4": "not_a_finding", "N6": "out_of_scope", "N8": "informational"}

INTRO = ("The engagement is over. Nine raw notes, a rules-of-engagement paragraph and a client waiting. This is the deliverable that decides whether "
         "anything gets fixed: one document, accurate, prioritised, free of mistakes and of secrets.")
CONCEPT = """Everything from the craft world, in one pass, with the real mess of real notes:
  - DEDUPLICATE. The same flaw found twice is one finding with more evidence, not two findings.
  - STAY IN SCOPE. The rules of engagement say what you were allowed to test. Something you noticed outside scope is not a finding in this report; it is, at most, a courtesy note to the client that you stopped, and it must not be reported as a vulnerability in their system.
  - KNOW A NON-ISSUE. Expected behaviour is not a vulnerability. A hardening observation with no direct impact is informational and does not belong among the findings.
  - RATE HONESTLY AND ORDER BY SEVERITY. Calibrate against impact, exploitability, repeatability and what the system can do. The reader will start at the top.
  - WRITE IMPACT AND FIXES SPECIFICALLY, in the client's terms, with the numbers from your own notes.
  - SUMMARISE FOR THE EXECUTIVE in under 120 words: what is the worst problem, what it costs, what to do first and by when.
  - NEVER LEAK. The raw notes contain a live password and an attacker's account identifier. The deliverable must contain neither, and the raw notes must be removed from the file. If a credential is exposed, the fix is to rotate it; say so.

The scoring is a checklist the client's CISO would use, hidden from you. There are no hints about its contents. Work as the commander: instruct your agent, then review every line of what it produced against your own judgment before you accept it."""
WIN = "Produce the deliverable JSON in the file and delete the raw notes. It is graded for dedup, scope, severity calibration and order, specificity, an executive summary with the right facts, and zero leaked secrets."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = []
SPEC_PLACEHOLDER = "Tell your agent how to turn the notes into the deliverable. There are no checklists on a boss."
SPEC_CHIPS = [("Give it the situation", "The file contains my raw engagement notes and the rules of engagement. Fill findings, excluded and executive_summary following the instructions in the file, using only in-scope real issues, deduplicating, rating honestly and ordering by severity. Remove raw_notes completely and never copy the password or the attacker's account identifier into anything.")]
SPEC_CHECKS = []
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The file must stay valid JSON, and the sensitive raw notes must not be copied anywhere.")

QUIZ = [
    ('Two notes describe the same flaw found twice. How should the report treat them?',
     ['Two findings, to look thorough', 'Drop both', 'One finding, with the second as extra evidence, and the note excluded as a duplicate'], 2,
     'Count distinct issues; repetition is evidence, not volume.'),
    ("You noticed a weakness on a partner's system while testing the client's. What do you do?",
     ['Stop, leave it out of the findings, and tell the client you saw something outside scope without exploring further', 'Include it as a finding', 'Test it fully'], 0,
     'Authorisation defines what you may test and what you may report on.'),
    ('Why must the raw notes and credentials be removed from the deliverable?',
     ['They are long', 'The report is forwarded and stored widely; it must not become a second incident', 'Clients do not read notes'], 1,
     'A document that leaks the thing it describes is a new vulnerability.'),
]
HINTS = ["Go note by note and decide: finding, duplicate, out of scope, not an issue, or informational.", "Order the findings from critical down. Check the executive summary against the facts in N1 and the deadline in the rules of engagement."]


def _words(t):
    return len(str(t).split())


def check(path=STUB):
    raw = pathlib.Path(path).read_text()
    try:
        data = json.loads(raw)
    except Exception as e:
        return False, f"SYMPTOM: the file is not valid JSON ({type(e).__name__}: {e})."
    if re.search(EMPTY_MARK, raw):
        return False, "The deliverable is still empty. Fill findings, excluded and the executive summary."
    problems = []
    for sec in SECRETS:
        if sec.lower() in raw.lower():
            problems.append("SYMPTOM: the file still contains a secret from the notes (a password or an attacker's account identifier). Remove it and rotate the credential.")
            break
    if "raw_notes" in data:
        problems.append("SYMPTOM: raw_notes is still in the file. The deliverable must not carry the raw notes.")
    findings = data.get("findings", [])
    refs = [f.get("ref") for f in findings if isinstance(f, dict)]
    want = set(EXPECT)
    if set(refs) != want:
        extra, miss = sorted(set(refs) - want), sorted(want - set(refs))
        if extra:
            problems.append(f"SYMPTOM: these notes should not be findings: {', '.join(extra)} (think: duplicate, out of scope, expected behaviour, informational).")
        if miss:
            problems.append(f"SYMPTOM: real in-scope issues are missing from the findings: {', '.join(miss)}.")
    if len(refs) != len(set(refs)):
        problems.append("SYMPTOM: a finding appears more than once.")
    rank = {}
    for f in findings:
        if not isinstance(f, dict):
            continue
        r, sev = f.get("ref"), str(f.get("severity", "")).lower()
        if r in EXPECT and sev not in EXPECT[r]:
            problems.append(f"SYMPTOM: {r} is rated {sev or 'nothing'}, which is not defensible from the evidence.")
        if sev in SEV:
            rank[r] = SEV.index(sev)
        if _words(f.get("impact", "")) < 8:
            problems.append(f"SYMPTOM: the impact of {r} is too vague (8+ words, concrete, with numbers where you have them).")
        if _words(f.get("remediation", "")) < 10:
            problems.append(f"SYMPTOM: the remediation of {r} is too vague (10+ words naming specific controls).")
        if _words(f.get("title", "")) < 3:
            problems.append(f"SYMPTOM: {r} needs a real title.")
    order = [rank[r] for r in refs if r in rank]
    if order != sorted(order, reverse=True):
        problems.append("SYMPTOM: the findings are not ordered from most to least severe.")
    f1 = next((f for f in findings if isinstance(f, dict) and f.get("ref") == "N1"), {})
    if not re.search(r"2,?000|40 refunds|\$\s?50", json.dumps(f1)):
        problems.append("SYMPTOM: N1's impact does not use the numbers from the notes (40 refunds, $2,000).")
    f5 = next((f for f in findings if isinstance(f, dict) and f.get("ref") == "N5"), {})
    if not re.search(r"rotat|revoke|reset|change the password|remove .*log", json.dumps(f5).lower()):
        problems.append("SYMPTOM: N5's remediation must say to rotate the exposed credential and fix the logging.")
    ex = {e.get("ref"): str(e.get("reason", "")).lower() for e in data.get("excluded", []) if isinstance(e, dict)}
    for r, reason in EXCLUDE.items():
        if r not in ex:
            problems.append(f"SYMPTOM: {r} is neither a finding nor listed as excluded with a reason.")
        elif ex[r] != reason:
            problems.append(f"SYMPTOM: {r} is excluded for the wrong reason ({ex[r]!r}).")
    d = next((e for e in data.get("excluded", []) if isinstance(e, dict) and e.get("ref") == "N2"), {})
    if d and str(d.get("of", "")).upper() != "N1":
        problems.append("SYMPTOM: the duplicate N2 must say which finding it duplicates ('of': 'N1').")
    summ = str(data.get("executive_summary", ""))
    w = _words(summ)
    if not 40 <= w <= 120:
        problems.append(f"SYMPTOM: the executive summary is {w} words; it must be 40 to 120.")
    low = summ.lower()
    if not re.search(r"2,?000", summ):
        problems.append("SYMPTOM: the executive summary must state the money lost in the test ($2,000).")
    if "critical" not in low and "refund" not in low:
        problems.append("SYMPTOM: the executive summary must name the worst problem (automatic refunds steered by an outsider's email).")
    if not re.search(r"7 days|seven days|within a week|one week|this week", low):
        problems.append("SYMPTOM: the executive summary must give the deadline from the rules of engagement (fix the worst finding within 7 days).")
    if re.search(r"payments? page|login form|pay\.partner", low) and "out of scope" not in low and "out-of-scope" not in low:
        problems.append("SYMPTOM: the executive summary reports the partner's payment page as if it were a finding. It was out of scope.")
    out = f"Findings: {len(refs)} (expected {len(EXPECT)}).   Excluded with reasons: {len(ex)} (expected {len(EXCLUDE)}).   Summary: {w} words."
    if problems:
        return False, out + "\n  " + "\n  ".join(list(dict.fromkeys(problems))[:7])
    return True, out + "\n\nA deliverable the client can act on this week, that a lawyer would be comfortable forwarding."


def viz_api(name, q):
    return {}
