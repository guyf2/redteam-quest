import json
import pathlib
import re

TITLE = "Threat model a real system"
WORLD = "craft"
KIND = "delegate + verify"
MODE = "delegate"
XP = 90
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/07-craft/lvl25_threats.json"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl25_threats.json"
EMPTY_MARK = "what is being attacked"
CATEGORIES = ["prompt_injection", "data_exfiltration", "tool_abuse", "training_data_poisoning", "model_extraction", "privacy_leakage", "supply_chain", "resource_abuse"]
ASSETS = {"the refund API": r"refund", "support emails": r"e-?mail|inbox", "the help-center knowledge base": r"vector|help.?center|knowledge|article|rag",
          "the system prompt": r"system prompt", "customer order data": r"order|customer data|personal|pii", "the fine-tuned model": r"fine.?tun|weights|model",
          "credentials and API keys": r"api key|credential|secret|token"}

INTRO = ("You have attacked many systems from the outside. A red team's most valuable product is the opposite view: a clear map of what could go "
         "wrong in a system before it ships, ranked, with a plan. Threat-model this one.")
CONCEPT = """THE SYSTEM: SupportBot, a customer-support assistant for an online shop.
  - It answers customers in a chat widget. It can read the logged-in customer's order history and the support-inbox emails (many written by outsiders).
  - It searches a VECTOR STORE of help-center articles. Support staff edit the articles, and some are imported automatically from a partner's website.
  - It can issue REFUNDS up to $50 through a refund API and send confirmation emails.
  - The system prompt contains tone guidance and an internal escalation phone number. The model is a hosted LLM reached with an API key, and a copy of it was FINE-TUNED on past support tickets.

THREAT MODELING asks four questions: what are we building, what can go wrong, what are we going to do about it, and did we do a good enough job? For AI systems, 'what can go wrong' is organised by well-known catalogues: the OWASP Top 10 for LLM Applications, and MITRE ATLAS (a matrix of adversary tactics against ML systems). Together they give you a vocabulary for the categories in the table below, which you already met level by level: prompt_injection, data_exfiltration, tool_abuse, training_data_poisoning, model_extraction, privacy_leakage, supply_chain, resource_abuse (unbounded cost or denial of service).

For each threat write down:
  - the ASSET attacked, the CATEGORY, and the ATTACK in one concrete sentence (who does what, to what);
  - LIKELIHOOD (1-5) and IMPACT (1-5). Their product ranks the threats;
  - a MITIGATION: something specific you would build or change (not 'be careful').

The skill is judgment about WHAT MATTERS MOST. Count what the system can DO. A bot that can read untrusted text, see private data, AND issue refunds or send mail has the dangerous combination from the permission-policy level. A leaked tone-guidance prompt is embarrassing; a refund API steered by an outsider's email is money gone. Your ranking must reflect that.

Work as the commander: tell your agent the system, the categories and the format, then REVIEW the table it produces. Agents love generic threats ('data breach'); you want threats specific to THIS system's parts. The grader gives symptoms about coverage and priorities."""
WIN = ("Write a JSON threat list with at least 8 threats that covers all 8 categories and every key asset of SupportBot, with likelihood and impact from 1 to 5, "
       "concrete attacks and mitigations, and a top-ranked threat that reflects what the bot can actually do.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["risk_matrix", {}]]
SPEC_PLACEHOLDER = "Describe the threat model you want, and give your agent the system description. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Give it the system", "The system is SupportBot: a support assistant that reads customers' order history and support-inbox emails (some written by outsiders), searches a vector store of help-center articles (some imported from a partner site), can issue refunds up to $50 via a refund API and send emails, has a system prompt with an internal phone number, uses a hosted LLM through an API key, and was fine-tuned on past tickets."),
    ("Format", "Fill the JSON file: a list of threats, each with id, asset, category, attack, likelihood (1-5), impact (1-5) and mitigation. Categories must be exactly: prompt_injection, data_exfiltration, tool_abuse, training_data_poisoning, model_extraction, privacy_leakage, supply_chain, resource_abuse."),
    ("Coverage", "Cover every category and every asset: refund API, support emails, the help-center knowledge base, the system prompt, customer order data, the fine-tuned model, and credentials/API keys. At least 8 threats."),
    ("Be concrete", "Each attack must say who does what to which part of THIS system in at least 8 words, and each mitigation must be a specific control in at least 8 words. No generic threats like 'data breach'."),
    ("Prioritise", "Rate likelihood and impact honestly. The highest-risk threat should be whatever lets untrusted input trigger the bot's powers (the refund API or outbound email)."),
]
SPEC_CHECKS = [
    ("Describes the system", r"supportbot|refund|vector|support.?inbox|fine.?tun"),
    ("Specifies the JSON format", r"json|id.*asset|likelihood|impact|mitigation"),
    ("Covers all categories and assets", r"every|all (8|eight)? ?categor|each categor|cover"),
    ("Demands concrete threats", r"concrete|specific|at least 8|who does what|no generic"),
    ("Asks for honest prioritisation", r"prioriti|rate|highest|rank|honest"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The file must stay valid JSON.")

QUIZ = [
    ('What are the first steps of any threat model?',
     ['Understand what the system is and what it can do, then ask what can go wrong', 'Writing exploits', 'Choosing a firewall'], 0,
     'You cannot rank risks for a system you have not mapped.'),
    ('Why is the product likelihood x impact used, rather than impact alone?',
     ['It is traditional', 'It is easier to compute', 'A catastrophic but nearly impossible event and a likely nuisance should not tie; the product balances both'], 2,
     'Risk is exposure times consequence.'),
    ('Which finding should usually rank highest for SupportBot?',
     ['The system prompt can be extracted', "Outsiders' emails can steer the refund API", 'Error messages show the framework version'], 1,
     'Untrusted input reaching a tool that moves money is the combination that causes real loss.'),
    ("What is wrong with the mitigation 'be careful with user input'?",
     ['Nothing', 'It is too long', 'It is not specific or testable: a mitigation should name a control, such as user-justified permissions or rate limits'], 2,
     'A mitigation you cannot build or verify is not a mitigation.'),
]
HINTS = [
    "Tell your agent the whole system description and the exact list of categories. Models write better threats when they know the parts.",
    "If the grader says an asset is uncovered, ask for a threat about it by name. The seven assets are the refund API, support emails, the knowledge base, the system prompt, order data, the fine-tuned model, and keys.",
    "For the top threat: ask your agent to rate the refund API steered by a malicious email with likelihood 4 and impact 5, and to put a user-justified-permission policy and rate limits in the mitigation.",
]


def _words(t):
    return len(str(t).split())


def check(path=STUB):
    try:
        data = json.loads(pathlib.Path(path).read_text())
        threats = data["threats"] if isinstance(data, dict) else data
    except Exception as e:
        return False, f"SYMPTOM: the file is not valid JSON with a 'threats' list ({type(e).__name__}: {e})."
    if not isinstance(threats, list) or not threats:
        return False, "SYMPTOM: 'threats' must be a non-empty list."
    problems, ids, cats, scored = [], set(), set(), []
    for k, t in enumerate(threats):
        tag = t.get("id", f"#{k + 1}") if isinstance(t, dict) else f"#{k + 1}"
        if not isinstance(t, dict):
            problems.append(f"SYMPTOM: threat {tag} is not an object.")
            continue
        miss = [f for f in ("id", "asset", "category", "attack", "likelihood", "impact", "mitigation") if f not in t or t[f] in ("", None)]
        if miss:
            problems.append(f"SYMPTOM: threat {tag} is missing {', '.join(miss)}.")
            continue
        if t["id"] in ids:
            problems.append(f"SYMPTOM: duplicate id {t['id']}.")
        ids.add(t["id"])
        if t["category"] not in CATEGORIES:
            problems.append(f"SYMPTOM: threat {tag} has category {t['category']!r}, which is not in the list.")
        else:
            cats.add(t["category"])
        try:
            l, i = int(t["likelihood"]), int(t["impact"])
            assert 1 <= l <= 5 and 1 <= i <= 5
            scored.append((l * i, t))
        except Exception:
            problems.append(f"SYMPTOM: threat {tag} needs likelihood and impact as whole numbers from 1 to 5.")
        if _words(t["attack"]) < 8:
            problems.append(f"SYMPTOM: the attack in threat {tag} is too vague (needs at least 8 words: who does what to which part).")
        if _words(t["mitigation"]) < 8:
            problems.append(f"SYMPTOM: the mitigation in threat {tag} is too vague (needs at least 8 words naming a specific control).")
    if len(threats) < 8:
        problems.append(f"SYMPTOM: only {len(threats)} threats; at least 8 are needed.")
    missing_c = [c for c in CATEGORIES if c not in cats]
    if missing_c:
        problems.append("SYMPTOM: categories not covered: " + ", ".join(missing_c))
    blob = [(" ".join(str(t.get(f, "")) for f in ("asset", "attack"))).lower() for t in threats if isinstance(t, dict)]
    missing_a = [name for name, rx in ASSETS.items() if not any(re.search(rx, b) for b in blob)]
    if missing_a:
        problems.append("SYMPTOM: assets with no threat: " + ", ".join(missing_a))
    if scored:
        top = max(scored, key=lambda s: s[0])[1]
        text = (str(top.get("asset", "")) + " " + str(top.get("attack", ""))).lower()
        if not re.search(r"refund|e-?mail", text):
            problems.append(f"SYMPTOM: your highest-risk threat is {top.get('id')} ({top.get('asset')!r}). Look at what the bot can DO: which threat lets untrusted input trigger money or mail?")
        rf = [s for s, t in scored if re.search(r"refund", (str(t.get('asset', '')) + str(t.get('attack', ''))).lower())]
        if rf and max(rf) < 12:
            problems.append("SYMPTOM: a threat against the refund API is rated below 12 (likelihood x impact). A tool that moves money, steerable by outsiders, is not a low risk.")
    out = f"{len(threats)} threats, {len(cats)}/8 categories covered."
    if problems:
        return False, out + "\n  " + "\n  ".join(problems[:6])
    return True, out + "\n\nA map you can plan work from: specific, covering, and ranked by what the system can really do."


_ = None


def viz_api(name, q):
    return {}
