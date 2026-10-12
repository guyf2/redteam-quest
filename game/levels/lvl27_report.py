import pathlib
import re

TITLE = "Write the vulnerability report"
WORLD = "craft"
KIND = "delegate + verify"
MODE = "delegate"
XP = 90
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/07-craft/lvl27_report.md"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl27_report.md"
EMPTY_MARK = r"\(write it here\)"
SECRETS = ["sk-live-7Hq29XKd0LmPz4Wv", "maria.gonzalez@customer.example"]

INTRO = ("An attack nobody understands gets nothing fixed. The last skill is writing the finding so that an engineer who was not there can "
         "reproduce it, a manager can see why it matters, and nobody can use the report itself against the customer.")
CONCEPT = """A good vulnerability report is short, concrete and safe to share. The structure that works:
  1. SUMMARY: two sentences. What is broken, and why does it matter?
  2. IMPACT: what an attacker gains, in the customer's terms and with numbers from your evidence (dollars, records, time).
  3. SEVERITY: your rating and the reasoning (impact, exploit conditions, repeatability). Match it to your triage: this is the refund finding.
  4. STEPS TO REPRODUCE: numbered, exact, in order, so someone else can do it in a test environment. Say what they should see at each step.
  5. EVIDENCE: what you observed (counts, timings, what the system did), without raw sensitive data.
  6. REMEDIATION: specific fixes, layered. One control is a hope; several are a defense. Think across layers: restrict what the tool may do (permissions justified by the user, confirmation, per-day caps), separate or neutralise untrusted content, limit and monitor (rate limits, alerts on repeated refunds), and rotate anything exposed.
  7. DISCLOSURE: how and to whom you will share it, and that details stay private until fixed.

Hygiene is part of the job:
  - NEVER paste live secrets, keys or customer personal data into a report. Reports get forwarded, stored in tickets and screenshotted. Redact them ('sk-live-[REDACTED]', 'a customer address') and say where the original is held. Note that an exposed key itself is a finding: say it must be rotated.
  - Stay factual: state what you did and observed, not what you suspect. No drama, no blame.
  - Test only in the environment you were authorised for (here, staging).

Your lab notes are in the file, and they are sensitive. You are the commander: instruct your agent to write the report from the notes, review it with a skeptical eye (does it leak anything? are the numbers right?), and make sure the raw notes section is gone from the final text."""
WIN = ("The report must have the required sections, 4 or more numbered reproduction steps, a quantified impact from the notes, a critical rating with reasoning, "
       "remediation across at least 3 layers, a disclosure note, 250 to 750 words, and must not contain the raw API key or the customer's address.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["report_anatomy", {}]]
SPEC_PLACEHOLDER = "Tell your agent how to write the report from the lab notes in the file. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Structure", "Write the report with these sections, as markdown headings: Summary, Impact, Severity, Steps to reproduce, Evidence, Remediation, Disclosure."),
    ("Quantify", "Use the numbers from the lab notes in Impact and Evidence (40 refunds, $2,000 in ten minutes, no alert, no daily cap)."),
    ("Rate it", "Severity: critical, with reasoning about impact, no precondition, repeatability and no safety net."),
    ("Remediation", "Give layered fixes: user-justified permissions or human confirmation for refunds, a daily cap and rate limits, isolate or neutralise untrusted email content, alerts on repeated refunds, and rotate the exposed key."),
    ("Hygiene", "NEVER include the live API key or the customer's email address: redact them (for example sk-live-[REDACTED]) and say the key must be rotated. Delete the raw lab notes section from the final file."),
]
SPEC_CHECKS = [
    ("Asks for the section structure", r"section|summary|steps to reproduce|remediation|disclosure"),
    ("Uses the evidence numbers", r"40|2,?000|\$|no alert|daily cap|numbers"),
    ("Gives a severity with reasoning", r"critical|severity|reasoning|repeatab"),
    ("Asks for layered remediation", r"layer|permission|rate limit|confirm|alert|rotate|isolate|cap"),
    ("Insists on redaction", r"redact|never include|do not include|secret|api key|remove|delete the (raw )?(lab )?notes"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The lab notes in the file are sensitive: do not copy secrets into the report.")

QUIZ = [
    ('Why must a report never contain the live API key found during testing?',
     ['Keys cannot be included in any file format', 'Reports are forwarded and stored; the key would leak to everyone who reads it, and it should be rotated instead', 'Keys change weekly'], 1,
     'The report must not become a second vulnerability.'),
    ("What belongs in 'Steps to reproduce'?",
     ['A story of how you felt', 'Only the fix', 'Numbered, exact steps in a test environment that someone else can follow, with what to expect at each'], 2,
     'If the engineer cannot reproduce it, it will not get fixed.'),
    ('Why give remediation across several layers?',
     ['One control can fail; permissions, limits, isolation and monitoring each catch what the others miss', 'More text looks better', 'Managers like lists'], 0,
     'Defense in depth: assume any single fix will be bypassed.'),
    ("Why quantify impact ('40 refunds, $2,000 in 10 minutes, no alert')?",
     ['It sounds scary', 'To pad the report', "Numbers turn 'an attacker could' into a concrete, comparable harm that justifies priority"], 2,
     'Specific evidence is what moves a finding up the queue.'),
]
HINTS = [
    "Give your agent the exact seven headings and tell it to use the numbers from the notes. Review the Impact section: are there dollar figures?",
    "Tell your agent the redaction rule explicitly: no raw key, no customer address, and delete the 'LAB NOTES' section entirely from the file.",
    "Remediation needs at least three kinds of control: permissions or confirmation, limits and caps, isolating untrusted content, monitoring and alerts, and key rotation.",
]

SECTIONS = {"Summary": r"summary", "Impact": r"impact", "Severity": r"severity", "Steps to reproduce": r"steps? to reproduce|reproduction", "Evidence": r"evidence", "Remediation": r"remediation|recommendation|mitigation|fix", "Disclosure": r"disclosure|timeline"}
LAYERS = {"permissions or confirmation": r"confirm|approval|approve|justif|permission|least.?privilege|human",
          "caps and rate limits": r"daily cap|rate.?limit|cap|limit|throttl|threshold",
          "isolating untrusted content": r"untrusted|isolat|spotlight|sanitiz|separate|quarantine|neutrali[sz]e",
          "monitoring and alerts": r"alert|monitor|detect|anomal|log",
          "rotating the exposed key": r"rotate|revoke|rotation"}


def _section(text, rx):
    """The body of the first heading that matches rx, up to the next heading ('' if there is none)."""
    parts = re.split(r"^\s{0,3}#{1,4}\s*(.+?)\s*$", text, flags=re.M)
    for i in range(1, len(parts) - 1, 2):
        if re.search(rx, parts[i].lower()):
            return parts[i + 1]
    return ""


def check(path=STUB):
    text = pathlib.Path(path).read_text()
    low = text.lower()
    problems = []
    if re.search(r"\(write it here\)", low):
        return False, "The report section is still the placeholder. Write the report."
    for s in SECRETS:
        if s.lower() in low:
            problems.append(f"SYMPTOM: the report contains a live secret ({s[:12]}...). Redact it and delete the raw notes section: a report must never leak what it describes.")
    heads = [h.lower() for h in re.findall(r"^\s{0,3}#{1,4}\s*(.+?)\s*$", text, re.M)]
    missing = [name for name, rx in SECTIONS.items() if not any(re.search(rx, h) for h in heads)]
    if missing:
        problems.append("SYMPTOM: missing sections (as headings): " + ", ".join(missing))
    steps = re.findall(r"^\s*\d+[.)]\s+\S", text, re.M)
    if len(steps) < 4:
        problems.append(f"SYMPTOM: only {len(steps)} numbered steps to reproduce; at least 4 are needed so someone else can follow them.")
    if not (re.search(r"\$\s?2,?000", text) or re.search(r"\b40\b.{0,30}refund|refund.{0,30}\b40\b", low)):
        problems.append("SYMPTOM: the impact does not quantify the harm from the notes (40 refunds, $2,000).")
    if not re.search(r"\bcritical\b", low):
        problems.append("SYMPTOM: the severity should be critical, with reasoning.")
    layers = [n for n, rx in LAYERS.items() if re.search(rx, _section(text, SECTIONS["Remediation"]).lower())]
    if len(layers) < 3:
        problems.append(f"SYMPTOM: remediation covers only {len(layers)} kind(s) of control ({', '.join(layers) or 'none'}); layer at least 3.")
    if not re.search(r"redact|\[redacted\]|not (included|reproduced)|withheld", low) and not any(s.lower() in low for s in SECRETS):
        problems.append("SYMPTOM: the report does not mention that sensitive values were redacted or that the exposed key must be rotated.")
    if not re.search(r"private|confidential|coordinated|until (it is )?(fixed|patched)|disclos", low):
        problems.append("SYMPTOM: no disclosure note: say who receives the report and that details stay private until fixed.")
    words = len(re.sub(r"<!--.*?-->", "", text, flags=re.S).split())
    if words < 250 or words > 750:
        problems.append(f"SYMPTOM: the report is {words} words; aim for 250 to 750 (concise but complete).")
    if re.search(r"^\s*#\s*LAB NOTES", text, re.M | re.I):
        problems.append("SYMPTOM: the raw LAB NOTES section is still in the file. Delete it from the deliverable.")
    out = f"Sections found: {len(SECTIONS) - len(missing)}/{len(SECTIONS)}.   Numbered steps: {len(steps)}.   Remediation layers: {len(layers)}.   Words: {words}."
    if problems:
        return False, out + "\n  " + "\n  ".join(problems[:6])
    return True, out + "\n\nA report an engineer can act on and a manager can forward without a second incident."


def viz_api(name, q):
    return {}
