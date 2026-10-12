import pathlib

import torch

from . import attacks
from .common import acc, art, target as load_target
from .kit import call, check_images, freeze, viz_target

TITLE = "Targeted attack: choose what the model says"
WORLD = "vision"
KIND = "delegate + verify"
MODE = "delegate"
XP = 40
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl03_targeted.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl03_targeted.py"
EPS, NEED = 0.3, 0.85

INTRO = ("So far you made the model WRONG. Now make it wrong in a way YOU choose: turn every digit into a specific "
         "other digit. This is what separates a nuisance from a weapon: an attacker who picks the outcome.")
CONCEPT = """An untargeted attack climbs the loss of the TRUE class: "be anything but a 7". A targeted attack picks a destination class t and walks toward it: it DESCENDS the loss of class t, the same way training would, but by changing the pixels instead of the weights.

  x_adv = x - alpha * sign(gradient of loss(model(x), t))   (note the minus sign)

Reaching one specific class is a much smaller region of input space than "anywhere but the true class", so one big step usually is not enough. Take several small steps and keep the result inside the eps-ball and the valid pixel range.

Real-world meaning: untargeted = the stop sign is misread. Targeted = the stop sign is read as "speed limit 80", or the face is read as "administrator"."""
WIN = (f"At eps = {EPS}, at least {NEED:.0%} of 500 digits must be classified as their assigned target class "
       "(the grader uses target = (true label + 3) mod 10), with every pixel within eps and inside [0, 1].")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["targeted", {}], ["stepcurve", {}]]
SPEC_PLACEHOLDER = "Describe the targeted attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Targeted, not untargeted", "This is a TARGETED attack: the model must output the class given in `target`, not merely a wrong class."),
    ("Direction", "Move toward the target: minimize the cross-entropy loss with respect to the target label."),
    ("Iterate", "Use several small gradient-sign steps rather than one big step."),
    ("Threat model", f"White-box, L-infinity budget eps, pixels clipped to [0, 1]. Signature: targeted_attack(model, x, target, eps)."),
    ("Success measure", f"Success means at least {NEED:.0%} of images are classified as their target at eps={EPS}."),
]
SPEC_CHECKS = [
    ("Says it is targeted", r"target"),
    ("Direction: toward the target", r"minimi|descen|toward|decreas|reduce the loss|lower the loss"),
    ("Iterates", r"iterat|steps|loop|repeat|multiple|several"),
    ("Budget and range", r"eps|l.?inf|budget"),
    ("Signature", r"targeted_attack\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for.")

QUIZ = [
    ('A targeted attack toward class t, compared with an untargeted one, uses the gradient of the loss of class t...',
     ['...and ascends it', '...and descends it', '...and ignores its sign'], 1,
     'Untargeted ascends the loss of the true class to escape it; targeted descends the loss of the wanted class to walk toward it.'),
    ('Why does a targeted attack usually need more steps than an untargeted one at the same budget?',
     ['It needs a bigger model to compute', "One specific class is a much smaller region of input space than 'anything but the true class'", 'Gradients toward a specific class are noisier than gradients away from the true class'], 1,
     'Landing in one particular class is a harder target than merely escaping the true class, so more small steps are needed to reach it precisely.'),
    ("Your agent's code makes 99% of digits misclassified, but only 12% reach the target class. What did it build?",
     ['A correct targeted attack with a low success rate', 'A broken grader', "An untargeted attack, probably (it ascended the true-class loss instead of descending the target's)"], 2,
     'High error with a low target-hit rate is the signature of an untargeted attack: it is good at making the model wrong, just not wrong in the chosen direction.'),
    ('Why is a targeted attack scarier for a defender than an untargeted one?',
     ['It needs no gradients', 'It runs faster', "The attacker chooses the outcome (e.g. 'speed limit' instead of 'stop')"], 2,
     'Choosing the outcome turns misclassification into controlled misbehaviour, which is a much more useful capability for an attacker than random errors.'),
]
HINTS = [
    "Tell your agent: this is a targeted attack. The loss is cross-entropy against the TARGET labels, not the true labels.",
    "Update with a minus sign: x_adv = x_adv - alpha * grad.sign(), then project to [x - eps, x + eps] and clip to [0, 1].",
    "Use about 20-40 steps with alpha = 2.5 * eps / steps. A single step reaches the target only about half the time.",
]


def check(path=STUB):
    model, x, y = load_target()
    freeze(model)
    t = (y + 3) % 10
    adv, err = call(path, "targeted_attack", model, x.clone(), t.clone(), EPS)
    if err:
        return False, err
    err = check_images(adv, x, EPS)
    if err:
        return False, err
    with torch.no_grad():
        pred = model(adv).argmax(1)
    hit, wrong = (pred == t).float().mean().item(), (pred != y).float().mean().item()
    out = f"Clean accuracy: {acc(model, x, y):.0%}   Target hit rate: {hit:.0%}   (needed {NEED:.0%})"
    i = (pred == t).nonzero()
    if len(i):
        k = i[0].item()
        out += f"\n\ntrue label {y[k].item()}  ->  model says {pred[k].item()} (target was {t[k].item()})\n"
        out += "\n".join(f"{a}   {b}" for a, b in zip(art(x[k]), art(adv[k])))
    if hit < NEED:
        extra = "\n\nThe model IS wrong on most images but not toward the targets: that is an untargeted attack." if wrong > 0.6 else ""
        return False, out + f"\n\nNot enough: only {hit:.0%} of images reach their target class." + extra
    return True, out


def viz_api(name, q):
    model, x, y = viz_target()
    freeze(model)
    if name == "targeted":
        i, t, eps, steps = int(q["i"]) % len(x), int(q["t"]) % 10, float(q["eps"]), int(q["steps"])
        xi, ti = x[i:i + 1], torch.tensor([t], device=x.device)
        adv = attacks.targeted_pgd(model, xi, ti, eps, steps)
        with torch.no_grad():
            pa = model(adv).softmax(1)[0]
        r = lambda v: [round(a, 3) for a in v.flatten().tolist()]
        return {"label": int(y[i]), "x": r(xi), "adv": r(adv), "pa": r(pa)}
    if name == "steps":
        if "steps" not in _CACHE:
            xs, t = x[:300], (y[:300] + 3) % 10
            steps = [1, 2, 5, 10, 20, 40]
            _CACHE["steps"] = {"steps": steps, "success": [round((model(attacks.targeted_pgd(model, xs, t, 0.3, s)).argmax(1) == t).float().mean().item() * 100, 1) for s in steps]}
        return _CACHE["steps"]


_CACHE = {}
