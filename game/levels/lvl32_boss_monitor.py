import pathlib

import torch

from . import attacks
from .common import _tensors
from .kit import call, freeze, viz_target

TITLE = "BOSS: the input monitor"
WORLD = "defense"
KIND = "boss"
MODE = "delegate"
XP = 120
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/08-boss/lvl32_input_monitor.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl32_input_monitor.py"
MAX_FPR, MIN_TPR = 0.10, 0.70

INTRO = ("Your model is live. You cannot retrain it today, and you cannot know who is attacking it or how. What you can do is put a monitor in "
         "front of it that raises a flag on suspicious inputs. A security team will review each flag, so false alarms cost real hours.")
CONCEPT = """Detection is the other half of defense: when you cannot make a model robust, make attacks visible. A good monitor is judged by two numbers that pull against each other: how many attacks it catches (true positives) and how many ordinary inputs it wrongly flags (false positives). Set the threshold too low and the team drowns in false alarms and starts ignoring the monitor; too high and attacks slip through.

What separates an adversarial input from a normal one, regardless of who made it? Adversarial perturbations are fragile in a way natural variation is not: the model's answer is often balanced on a knife edge, and simplifying or transforming the input (reducing precision, smoothing) can flip it back. Ordinary images survive that kind of treatment unchanged. Comparing the model's answer before and after a harmless transformation is a signal an attacker did not optimise against. (The technique is known as feature squeezing, and it has limits: an adversary who knows the monitor can adapt, which is why the final grade here uses attacks that do not.)

The attacker's identity is hidden: the grader mixes different attack methods (single-step and iterative) and budgets in the range 0.15 to 0.30, and counts only attacks that actually succeeded in changing the model's answer. You have a calibration set of normal images to set a sensible threshold, and the grader measures false alarms on different normal images. Pick the signals, combine them, and choose the threshold yourself. There are no hints about the method."""
WIN = (f"The monitor must flag at least {MIN_TPR:.0%} of successful adversarial inputs while flagging no more than {MAX_FPR:.0%} of ordinary ones. "
       "The attacks, budgets and normal images are different from your calibration data.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = []
SPEC_PLACEHOLDER = "Describe the monitor you want built. There are no checklists on a boss."
SPEC_CHIPS = [("Give it the situation", "Build detect(model, x, x_calib) returning a boolean tensor (N,). It must flag adversarial digit images and not flag ordinary ones. I do not know the attack method or budget (0.15 to 0.30 L-infinity). I have 1,000 clean calibration images to choose the threshold.")]
SPEC_CHECKS = []
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Use torch.no_grad() and keep it fast.")

QUIZ = [
    ('Why do false alarms matter as much as missed attacks?',
     ['They cost GPU time', 'They do not', 'A monitor that cries wolf gets ignored or switched off, so it protects nothing in practice'], 2,
     'Operational cost decides whether a control survives.'),
    ("Why does comparing the model's output before and after a simple transformation reveal many adversarial inputs?",
     ['The perturbation is tuned to the exact pixel values, so removing detail often undoes it while ordinary images stay stable', 'It makes the model bigger', 'Transformations are secret'], 0,
     'Adversarial examples tend to be brittle.'),
    ('Your monitor works perfectly in your tests but an attacker who knows it bypasses it. What is true?',
     ['That cannot happen', 'Detectors can be attacked adaptively too: treat them as one layer, not a guarantee', 'The attacker used magic'], 1,
     'Evaluate against adaptive adversaries before calling a detector robust.'),
]
HINTS = ["The model itself can be asked a second question: what would you say about a slightly simplified copy of this image?", "Choose the threshold from your clean calibration images so that about 5% of them would be flagged."]


def _squeezers():
    def med(x, k=2):
        xp = torch.nn.functional.pad(x, (0, k - 1, 0, k - 1), mode="replicate")
        u = xp.unfold(2, k, 1).unfold(3, k, 1)
        return u.reshape(*u.shape[:4], -1).median(-1).values
    return [lambda x: torch.round(x), lambda x: med(x, 2), lambda x: torch.round(x * 3) / 3]


def _suite(model, x, y):
    """Fresh attacked sets: (name, adversarial images that fooled the model)."""
    out = []
    for name, f in (("single-step", lambda e: attacks.fgsm(model, x, y, e)), ("iterative", lambda e: attacks.pgd(model, x, y, e, 20))):
        for e in (0.15, 0.2, 0.25, 0.3):
            adv = f(e)
            with torch.no_grad():
                ok = model(adv).argmax(1) != y
            out.append((f"{name} eps {e}", adv[ok]))
    return out


def check(path=STUB):
    model, _, _ = viz_target()
    freeze(model)
    Xte, Yte = _tensors(False)
    calib, x_clean, y_clean = Xte[:1000], Xte[1000:2000], Yte[1000:2000]
    flags, err = call(path, "detect", model, x_clean.clone(), calib.clone())
    if err:
        return False, err

    def flag(x):
        f, e = call(path, "detect", model, x.clone(), calib.clone())
        if e:
            raise RuntimeError(e)
        f = torch.as_tensor(f).flatten().bool().to(x.device)
        if f.shape != (len(x),):
            raise RuntimeError(f"Return one boolean per input image ({len(x)}), you returned {tuple(f.shape)}.")
        return f
    try:
        fpr = flag(x_clean).float().mean().item()
        rows, caught, total = [], 0, 0
        for name, adv in _suite(model, x_clean, y_clean):
            if len(adv) == 0:
                continue
            f = flag(adv)
            rows.append(f"  {name:22} {f.float().mean():.0%} of {len(adv)} successful attacks flagged")
            caught += int(f.sum())
            total += len(adv)
    except RuntimeError as e:
        return False, str(e)
    tpr = caught / max(total, 1)
    out = f"False alarms on ordinary images: {fpr:.1%}   (max {MAX_FPR:.0%})\nSuccessful attacks flagged overall: {tpr:.0%}   (need {MIN_TPR:.0%}+)\n" + "\n".join(rows)
    if fpr > MAX_FPR:
        return False, out + "\n\nToo many false alarms: the security team would switch this off."
    if tpr < MIN_TPR:
        return False, out + "\n\nToo many attacks get through."
    return True, out + "\n\nA monitor worth putting in front of a live model."


def viz_api(name, q):
    return {}
