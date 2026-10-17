import importlib.util
import pathlib

import torch

from .common import acc, target

TITLE = "PGD: the agent's code is broken"
WORLD = "vision"
KIND = "audit"
MODE = "audit"
XP = 40
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl02_pgd.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl02_pgd.py"
EPS = 0.15

INTRO = ("An agent wrote a PGD attack for you. It is well formatted, well commented, and wrong. "
         "Agents produce plausible code with subtle bugs. Your job is to catch them.")
CONCEPT = """PGD is FGSM repeated in small steps, plus a leash:

repeat N times:
  1. step alpha along sign(gradient), which ascends the loss
  2. project back so no pixel is more than eps from the ORIGINAL image
  3. clip to the valid range [0, 1]

Starting from a random point inside the eps-ball helps the attack escape flat spots.

The grader reports SYMPTOMS only (budget, range, accuracy). It never names the bug. Read the code, form a hypothesis from each symptom, and fix it, either yourself or by telling your agent. A good instruction names the symptom and the rule that is broken, not just "fix it"."""
WIN = (f"At eps = {EPS}, accuracy under attack must drop below 25% (plain FGSM at this eps only reaches about 49%, "
       "so iterating has to pay off), while budget and pixel range are respected.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

SPEC_PLACEHOLDER = "Tell your agent what is wrong. Click 'Use the grader's last message' to paste the symptom."
SPEC_CHIPS = [
    ("Use the grader's last message", "@LAST_GRADER"),
    ("Ask for the root cause", "Explain the root cause of this symptom before changing anything, then fix only that."),
    ("Name the rule", "The attack must keep every pixel within eps of the ORIGINAL image and inside [0, 1]."),
]
SPEC_CHECKS = [
    ("Names the symptom", r"symptom|budget|range|accuracy|violat|weak|more accurate"),
    ("States the rule that is broken", r"eps|\[\s*0\s*,\s*1\s*\]|ball|project|clip|clamp|sign|ascend"),
    ("Asks for cause, not a blind patch", r"why|root|cause|explain|because"),
]
AGENT_TASK = ("The player found problems in this attack code. Apply ONLY the fixes their instructions describe, "
              "keep everything else unchanged, and say what you changed and why.")
VIZ = [["landscape", {"modes": ["fgsm", "pgd"]}], ["curve", {"series": ["fgsm", "pgd"], "eps": 0.15}]]
EMPTY_NUDGE = ""

QUIZ = [
    ('Why does PGD project onto the eps-ball AFTER each step, not just once at the end?',
     ['Steps can accumulate drift; projecting each time keeps iterates feasible and the next gradient meaningful', 'It only matters when eps is very large', 'It prevents the attack from ever reducing the loss by accident'], 0,
     'Projection is part of the optimisation itself (projected gradient ASCENT), not a final cleanup step, and it matters at every eps, not just large ones.'),
    ('Projection centre: the eps-ball must be centred on...',
     ['Zero', 'The current iterate', 'The ORIGINAL clean image'], 2,
     'Centring on the current iterate lets the total perturbation grow without bound as steps accumulate; centring on zero would clip unrelated to the image at all.'),
    ("An agent's attack reports 'success' but the eval used a different eps than the threat model. What do you do?",
     ['Accept it: a higher success rate is still evidence the model is weak', 'Increase eps further to double-check', 'Reject it: robustness numbers are only meaningful for the stated threat model'], 2,
     "Attack-success claims without a matching threat model are the most common mistake in AI security reports: a bigger eps can always 'succeed' more, which proves nothing about the budget you actually care about."),
]
HINTS = [
    "Read the budget message literally: which line should ever let a pixel drift more than eps from x?",
    "After every step you need two operations: clamp the perturbation to [-eps, eps] relative to the ORIGINAL x, then clamp to [0, 1].",
    "If accuracy goes UP under attack, check the sign on the update line.",
]


def check(path=STUB):
    spec = importlib.util.spec_from_file_location("student", path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        model, x, y = target()
        clean = acc(model, x, y)
        adv = mod.pgd(model, x.clone(), y, EPS)
    except Exception as e:  # agent-written code can fail in any way; show it
        return False, f"The code crashed: {type(e).__name__}: {e}"
    if adv.shape != x.shape or not torch.isfinite(adv).all():
        return False, "SYMPTOM: the output has the wrong shape or contains NaN/inf."
    worst = (adv - x).abs().max().item()
    if worst > EPS + 1e-5:
        return False, f"SYMPTOM: budget violated. Largest pixel change {worst:.3f}, allowed eps={EPS}."
    if adv.min() < 0 or adv.max() > 1:
        return False, f"SYMPTOM: pixels outside the valid range [0, 1] (min {adv.min():.2f}, max {adv.max():.2f})."
    after = acc(model, adv, y)
    out = f"Clean accuracy: {clean:.0%}   Accuracy under attack: {after:.0%}"
    if after > clean:
        return False, out + "\n\nSYMPTOM: the 'attack' made the model MORE accurate."
    if after >= 0.25:
        return False, out + "\n\nSYMPTOM: attack too weak. Accuracy must drop below 25%."
    return True, out + "\n\nThe agent's code is now safe to trust. (A little.)"
