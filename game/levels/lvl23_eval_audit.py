import pathlib

import torch

from . import attacks
from .common import Defended, _tensors, acc, quantize
from .kit import call, freeze, viz_target
from .lvl21_adv_training import _train

TITLE = "Audit the robustness evaluation"
WORLD = "defense"
KIND = "audit"
MODE = "audit"
XP = 90
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/06-defense/lvl23_eval_audit.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl23_eval_audit.py"
EPS, TOL = 0.2, 0.08

INTRO = ("A report claims three models are 'robust'. The evaluation script was written by a coding agent. Your job is the one every security "
         "reviewer eventually faces: decide whether the NUMBER can be believed.")
CONCEPT = """A robustness number is an upper bound on what the attacker can do, produced by the best attack the evaluator thought of. If the attack is weak, the number is flattering, and nobody can tell from the number alone. The famous failures of defenses in the literature are almost all evaluation failures.

What goes wrong, and what the harness above does:
  1. TOO FEW EXAMPLES. Evaluating 32 images gives a very noisy estimate. Use enough samples that the error bar is small.
  2. THE WRONG BUDGET. The attack budget eps lives on the same [0, 1] pixel scale as the images. Dividing by 255 (a habit from 0-255 images) makes the attack a hundred times weaker than claimed.
  3. A WEAK ATTACK. One gradient step is not a worst case. Use an iterative attack (PGD, many steps) with a random start, and several restarts, counting a point as robust only if EVERY attempt fails.
  4. NO PROJECTION OR CLIPPING. Perturbed pixels must stay in [0, 1] and within eps of the original.
  5. ATTACKS THAT FOLLOW A MASKED GRADIENT. If a model hides or flattens its gradient (like the quantization defense in the boss level), a gradient attack goes nowhere and reports a false victory for the defender. A trustworthy evaluation includes ADAPTIVE attacks: transfer from the model's inner network, or BPDA (a straight-through approximation of the non-differentiable step), and takes the WORST case across all of them.

The three models in the grader: a standard classifier, the quantization-'defended' classifier from the 'robust' model boss (which exposes its inner network as `model.base` and its `levels` attribute), and a PGD adversarially-trained classifier. The grader knows the true worst-case robust accuracy of each (measured with a strong adaptive evaluation). Your function must reproduce it, not flatter it.

The grader gives symptoms only: your number and the true one for each model."""
WIN = (f"For each of the three models at eps = {EPS}, your robust_accuracy must land within {TOL:.0%} of the true worst-case value, "
       "on 1,000 test images.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["eval_gap", {}]]
SPEC_PLACEHOLDER = "Tell your agent what is wrong. Click 'Use the grader's last message' to paste the symptom."
SPEC_CHIPS = [
    ("Use the grader's last message", "@LAST_GRADER"),
    ("Ask for the root cause", "Explain the root cause of this symptom before changing anything, then fix only that."),
    ("Name the rule", "Evaluate on ALL provided images with PGD (many steps, random start, several restarts) at the true eps scale, clip to [0, 1] and the eps-ball, and count an image as robust only if every attempt fails. Also attack model.base directly when it exists, and take the worst case."),
]
SPEC_CHECKS = [
    ("Names the symptom", r"symptom|true|reports?|expected|says|but|robust"),
    ("States the rule that is broken", r"pgd|restart|worst|steps|eps|scale|all images|base|adaptive|bpda|transfer|mask|clip"),
    ("Asks for cause, not a blind patch", r"why|root|cause|explain|because"),
]
AGENT_TASK = ("The player found problems in this evaluation code. Apply ONLY the fixes their instructions describe, "
              "keep everything else unchanged, and say what you changed and why.")

QUIZ = [
    ('Why is a robustness number from a weak attack meaningless?',
     ['It is an upper bound only as good as the attack; a stronger attack could find far more failures', 'It is too low', 'Weak attacks are illegal'], 0,
     'You are reporting what the evaluator managed, not what an attacker could.'),
    ('Dividing eps by 255 when your images are already in [0, 1] means...',
     ['Nothing', 'The attack is stronger', 'The attack is about 255 times weaker than you claim, so the model looks robust'], 2,
     'Units are the quietest bug in robustness evaluation.'),
    ('Your evaluation says a model is 98% robust, but a transfer attack from its inner network gets it to 0%. What happened?',
     ['The transfer attack is unfair', 'The model is robust', 'The model masks its gradient; your attack followed a useless gradient'], 2,
     'That is gradient masking, and the reason adaptive attacks are mandatory.'),
    ('How should you count an example when you run an attack with several random restarts?',
     ['Robust if the first attempt fails', 'Average over attempts', 'Robust only if EVERY attempt fails (worst case)'], 2,
     'An attacker needs one success; the defender needs to survive all of them.'),
]
HINTS = [
    "Read the symptoms: on which model is your number far above the truth? A model that LOOKS robust to your attack but is not points to a weak or misled attack.",
    "Use all N images, eps on the [0, 1] scale, PGD with 50 steps, random start, step 2.5*eps/steps, project and clamp, and 3 restarts counting an image as robust only if every restart fails.",
    "For models that have a .base attribute (an inner network), also run PGD on model.base and evaluate the result on the full model; report the lowest accuracy across all attacks.",
]


def _strong(model, x, y, eps):
    alive = torch.ones(len(x), dtype=torch.bool, device=x.device)
    base = getattr(model, "base", None)
    for r in range(3):
        torch.manual_seed(300 + r)
        alive &= model(attacks.pgd(model, x, y, eps, 50)).argmax(1) == y
        if base is not None:
            alive &= model(attacks.pgd(base, x, y, eps, 50)).argmax(1) == y
            alive &= model(attacks.bpda_pgd(model, base, lambda z: quantize(z, model.levels), x, y, eps, 40)).argmax(1) == y
    return alive.float().mean().item()


def _models():
    std, _, _ = viz_target()
    std = freeze(std)
    return [("standard model", std), ("quantization-defended model", freeze(Defended(std, 4))), ("adversarially trained model", _train("pgd"))]


_TRUTH = {}


def _truth(x, y):
    if not _TRUTH:
        for name, m in _models():
            _TRUTH[name] = _strong(m, x, y, EPS)
    return _TRUTH


def check(path=STUB):
    Xte, Yte = _tensors(False)
    x, y = Xte[:1000], Yte[:1000]
    truth = _truth(x, y)
    bad, lines = 0, []
    for name, m in _models():
        got, err = call(path, "robust_accuracy", m, x.clone(), y.clone(), EPS)
        if err:
            return False, err
        try:
            got = float(got)
        except Exception:
            return False, "robust_accuracy must return a number between 0 and 1."
        want = truth[name]
        ok = abs(got - want) <= TOL
        bad += not ok
        lines.append(f"{'ok ' if ok else 'BAD'} {name}: your evaluation says {got:.0%}, the true worst-case value is {want:.0%}")
    out = f"{3 - bad}/3 models evaluated correctly.\n" + "\n".join(lines)
    if bad:
        hints = []
        if any("BAD quantization" in l or l.startswith("BAD quantization") for l in lines):
            hints.append("The defended model looks safer than it is: is your attack following a useful gradient?")
        return False, out + ("\n\n" + " ".join(hints) if hints else "")
    return True, out + "\n\nThese numbers can be trusted."


_CACHE = {}


def viz_api(name, q):
    if not _CACHE:
        Xte, Yte = _tensors(False)
        x, y = Xte[:500], Yte[:500]
        res = []
        for nm, m in _models():
            weak = acc(m, attacks.fgsm(m, x, y, EPS), y)
            res.append({"model": nm.replace(" model", ""), "weak": round(weak * 100, 1), "strong": round(_strong(m, x, y, EPS) * 100, 1)})
        _CACHE["rows"] = res
    return _CACHE
