import json
import pathlib

TITLE = "Triage: rate the findings"
WORLD = "craft"
KIND = "judge"
MODE = "delegate"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/07-craft/lvl26_triage.json"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl26_triage.json"
EMPTY_MARK = '"severity": ""'
LEVELS_ORDER = ["info", "low", "medium", "high", "critical"]
FINDINGS = {
    "F1": "An outsider's email, read by the assistant while it summarises the inbox, makes it issue $50 refunds to an attacker-controlled account. No customer action is needed. It repeats until stopped: 40 refunds in 10 minutes were observed, with no alert.",
    "F2": "Asking the assistant to repeat its instructions reveals its system prompt. The prompt contains only tone guidelines and the shop's public support phone number.",
    "F3": "A logged-in customer asks the assistant for their own order history and receives it.",
    "F4": "A help-center article imported from a partner site contains hidden text telling the assistant to add an affiliate link to every reply. Customers may click the link. No private data is exposed.",
    "F5": "The website's error page shows the name and version of the web framework.",
    "F6": "A researcher can tell, with 62% accuracy (chance is 50%), whether one specific past ticket was in the fine-tuning data. Tickets contain order numbers and first names.",
    "F7": "Anyone can send unlimited long requests to the chat widget without logging in. One simple script costs the shop roughly $900 per day in model usage, and legitimate customers slow down.",
}
EXPECT = {"F1": {"critical"}, "F2": {"info", "low"}, "F3": {"info"}, "F4": {"medium", "low"}, "F5": {"info", "low"}, "F6": {"low", "medium"}, "F7": {"high", "medium"}}

INTRO = ("A red team finds many things. The customer needs to know which ones to fix first. Rating severity honestly is a core part of the job, "
         "and getting it wrong in either direction hurts: inflate everything and nobody listens, shrug at the dangerous one and the shop loses money.")
CONCEPT = """SEVERITY is not how clever the attack was. It is a judgment from a few factors:
  - IMPACT: what is lost if it works? Money, private data, safety, reputation, only embarrassment, nothing?
  - EXPLOITABILITY: how hard is it? Does the attacker need an account, access, special knowledge, or just an email address?
  - SCOPE AND REPEATABILITY: one victim once, or everyone, automatically, for as long as nobody notices?
  - DETECTION AND CONTAINMENT: would the owner notice quickly? Is there a human or a limit in the loop?

Rules of thumb that serve you well:
  - CRITICAL means serious loss with little or no precondition and no safety net. Unauthenticated, automatable, repeating, undetected harm to money or data qualifies.
  - HIGH: serious impact but with a meaningful precondition, or real impact with limited scope.
  - MEDIUM: limited harm, or harm that needs user interaction or special conditions.
  - LOW: minor harm, hard to exploit, or leaking only low-value information.
  - INFO (informational): not a vulnerability at all: intended behavior, best-practice notes, hardening suggestions. Recognising what is NOT a finding is as valuable as finding things, and reports full of non-issues erode trust.

AI-specific notes: ask what the model can DO (its tools and permissions) and what it can SEE, because a prompt-injection finding's severity is the severity of the worst action it can trigger. A leaked system prompt is only as bad as what is in it.

Below are seven findings from a SupportBot engagement. Rate each one as info, low, medium, high or critical, with a one-sentence rationale in your own words that names the impact or the exploit condition. The grader knows the defensible range for each. There are no points for rating everything the same."""
WIN = ("At least 6 of the 7 ratings must be defensible, the refund finding must be rated exactly critical, the intended-behavior finding must be rated info, "
       "and every rationale must be a real sentence (10 words or more).")
BRIEF = INTRO + "\n\n" + CONCEPT + "\n\nTHE FINDINGS\n" + "\n".join(f"  {k}: {v}" for k, v in FINDINGS.items()) + "\n\n" + WIN

VIZ = [["severity_lab", {}]]
SPEC_PLACEHOLDER = "Give your agent the seven findings and the rating scale, and tell it how you want it to reason."
SPEC_CHIPS = [
    ("Give it the findings", "Here are the seven findings: " + " ".join(f"{k}: {v}" for k, v in FINDINGS.items())),
    ("Rating scale", "Rate each as one of: info, low, medium, high, critical. Fill the JSON file: for every finding set severity and a one-sentence why (at least 10 words) that names the impact or the condition needed to exploit it."),
    ("Judge on factors", "Judge each on impact, exploitability, scope and repeatability, and whether anyone would notice. Money loss that is automatic, repeatable and undetected is critical. Intended behavior is info, not a finding."),
    ("Do not inflate", "Do not rate everything high. Distinguish what must be fixed this week from what is a hardening note."),
]
SPEC_CHECKS = [
    ("Provides the findings", r"f1|refund|affiliate|membership|error page|system prompt|order history"),
    ("Defines the scale", r"info|low|medium|high|critical"),
    ("Judges on factors, not drama", r"impact|exploit|scope|repeat|detect|notice|factors"),
    ("Warns against inflation / recognises non-findings", r"inflate|not a finding|intended|info|not rate everything"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The file must stay valid JSON.")

QUIZ = [
    ('Why must severity reflect the worst action a prompt injection can trigger?',
     ['The injection itself does nothing; the harm comes from what the model is allowed to do', 'Injections are all equal', 'Severity is decided by the attacker'], 0,
     'A steerable model with no tools is a nuisance; with a refund API it is a loss.'),
    ('A customer receiving their own order history from the assistant is...',
     ['High severity', 'Informational: it is intended behaviour, not a vulnerability', 'Medium'], 1,
     'Recognising non-issues keeps a report credible.'),
    ('Which factor most increases the severity of F1?',
     ['It is automatic, repeatable, needs no victim action and triggered no alert', 'The attack is clever', 'It uses email'], 0,
     'Low precondition + repeatable + undetected = critical.'),
    ("You rate every finding 'critical' to get attention. What happens?",
     ['Everything gets fixed', 'Readers stop trusting your ratings, and the real critical one is lost in the noise', 'Nothing'], 1,
     'Calibration is the product you are selling.'),
]
HINTS = [
    "Ask your agent to reason per finding: impact, exploit conditions, whether it repeats, whether anyone would notice. Then pick a rating.",
    "F1 is the one that loses money automatically with no precondition and no alert. F3 is the customer's own data going to that customer.",
    "Ratings in the middle: F4 limited harm needs a click (medium); F6 is weak statistical leakage (low); F7 is real money but not data (high or medium).",
]


def check(path=STUB):
    try:
        data = json.loads(pathlib.Path(path).read_text())
    except Exception as e:
        return False, f"SYMPTOM: the file is not valid JSON ({type(e).__name__}: {e})."
    problems, good = [], 0
    for k in FINDINGS:
        e = data.get(k) if isinstance(data, dict) else None
        if not isinstance(e, dict) or e.get("severity", "").strip().lower() not in LEVELS_ORDER:
            problems.append(f"SYMPTOM: {k} has no valid severity (use info, low, medium, high or critical).")
            continue
        sev = e["severity"].strip().lower()
        if len(str(e.get("why", "")).split()) < 10:
            problems.append(f"SYMPTOM: the rationale for {k} is too short: write a real sentence of at least 10 words about the impact or the conditions.")
            continue
        if sev in EXPECT[k]:
            good += 1
        else:
            problems.append(f"SYMPTOM: {k} is rated {sev}, which is hard to defend given the facts: re-read what the attacker needs and what is lost.")
    sev_of = lambda k: (data.get(k, {}) or {}).get("severity", "").strip().lower() if isinstance(data, dict) else ""
    if sev_of("F1") != "critical":
        problems.append("SYMPTOM: F1 must be rated exactly critical: unauthenticated, automatic, repeating, no safety net, and money is lost.")
    if sev_of("F3") != "info":
        problems.append("SYMPTOM: F3 must be rated info: a customer receiving their own data is intended behavior, not a vulnerability.")
    distinct = len({sev_of(k) for k in FINDINGS})
    if distinct < 3:
        problems.append("SYMPTOM: you used fewer than 3 different ratings. Real findings differ; spread your ratings by the facts.")
    out = f"{good}/7 ratings defensible."
    if good < 6 or problems:
        return False, out + "\n  " + "\n  ".join(problems[:6])
    return True, out + "\n\nWell calibrated: the critical one stands out, and the non-issue is not dressed up as a finding."


def viz_api(name, q):
    return {}
