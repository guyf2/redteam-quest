import pathlib
import random

import torch
import torch.nn.functional as F

from .common import DEV, Net, _tensors, fit
from .kit import call, freeze

TITLE = "Forensics: find the backdoor"
WORLD = "defense"
KIND = "delegate + verify"
MODE = "delegate"
XP = 90
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/06-defense/lvl24_backdoor_hunt.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl24_backdoor_hunt.py"
CORNERS = {(0, 0): "top-left", (0, 1): "top-right", (1, 0): "bottom-left", (1, 1): "bottom-right"}

INTRO = ("In level 15 you planted a backdoor. Now you are the incident responder: three models arrived from a vendor, one of them was "
         "poisoned, and you do not know which, where the trigger is, or what it does. Find it.")
CONCEPT = """You cannot find a backdoor by testing on normal data: the model behaves perfectly on it. You also cannot read the weights and see a trigger. What you CAN do is ask the model a question that only a backdoored model answers surprisingly: 'how little would I have to change an input to force you to say class t?'

That is NEURAL CLEANSE, the standard first tool for backdoor forensics. For each model and each possible target class t, search for the smallest patch (a mask m over the pixels, and a pattern p to paint into them) that makes the model output t for ANY image:
      x' = (1 - m) * x + m * p        minimise   cross-entropy(model(x'), t)  +  lambda * sum(m)
In a clean model, forcing a class needs a big, obvious patch. In a backdoored model, one class has a shortcut: the hidden trigger. The optimiser rediscovers it, and the patch it finds for the poisoned target is dramatically SMALLER than for any other class. The chart shows the dip. That anomaly pinpoints the model, the target class, and (look at the mask) the trigger's position.

Practical notes:
  - Parametrise the mask and pattern through a sigmoid so they stay in [0, 1] (start the mask near zero).
  - The penalty weight lambda balances 'does it flip the class' against 'is it small'; around 0.02 works here.
  - Compare ACROSS all (model, class) pairs: the smallest total mask is the suspect. Real tools use a statistical outlier test (median absolute deviation), which also tells you when nothing is wrong.
  - Other forensic routes exist (activation clustering, weight pruning, fine-tuning), but reverse-engineering the trigger has one great property: it gives you evidence you can show.

The grader plants a NEW backdoor each time: different model, corner, and target class."""
WIN = "Return (index of the backdoored model, its target class). Both must be exactly right."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["cleanse", {}]]
SPEC_PLACEHOLDER = "Describe the forensic method you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Neural Cleanse", "For each model and each target class, optimise a small trigger (a mask and a pattern) that forces that class on any image, and record how small the mask is."),
    ("The loss", "Minimise cross-entropy toward the target class plus lambda (about 0.02) times the sum of the mask. Parametrise mask and pattern with sigmoids; initialise the mask near zero."),
    ("The verdict", "The (model, class) pair with the smallest mask is the backdoor. Return (model index, target class)."),
    ("Budget", "Use the 200 provided images and about 150 Adam steps (lr 0.1) per optimisation. Freeze the models' weights."),
    ("Signature", "find_backdoor(models, x) -> (index, target_class)."),
]
SPEC_CHECKS = [
    ("Reverse-engineers a trigger per class", r"cleanse|reverse|trigger|mask|pattern|optimi"),
    ("Penalises the mask size", r"lambda|l1|sum of the mask|small|penal|norm"),
    ("Compares across all models and classes", r"smallest|minimum|every|each|all .*class|outlier|anomal"),
    ("Returns (index, class)", r"index|return|\(.*class"),
    ("Signature", r"find_backdoor\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Keep the whole search under about a minute on the GPU.")

QUIZ = [
    ('Why can ordinary accuracy testing not reveal a backdoor?',
     ['The model behaves normally on every input that lacks the trigger', 'Backdoors are random', 'Test sets are too small'], 0,
     'The malicious behaviour is conditional on a trigger the tester never uses.'),
    ('In Neural Cleanse, what is the signature of a backdoored target class?',
     ['The largest patch needed to force it', 'No patch works', 'A much SMALLER patch suffices to force it than for any other class'], 2,
     'The trigger is a shortcut, so the optimiser finds a tiny pattern.'),
    ("What does the recovered mask tell you beyond 'this model is bad'?",
     ['Where the trigger is and roughly what it looks like: evidence you can show', 'Nothing', 'The training date'], 0,
     'Reverse-engineering produces an artifact, not just a score.'),
    ('You find no outlier in any model. What is the correct conclusion?',
     ['The models are proven clean', 'The tool is broken', 'No evidence of this kind of backdoor: it can still exist (other triggers, larger or input-dependent ones)'], 2,
     'Absence of evidence from one method is not proof of absence.'),
]
HINTS = [
    "Tell your agent: for every model and every class t in 0..9, optimise a mask and pattern that force class t, and record the mask's size (its sum).",
    "Use sigmoid(mask_param) and sigmoid(pattern_param); start mask_param at -2. Loss = cross_entropy(model((1-m)*x + m*p), t) + 0.02 * m.sum(). 150 Adam steps at lr 0.1.",
    "Collect all 30 mask sums and return the (model, class) with the smallest one. Freeze each model's parameters (requires_grad_(False)) first.",
]


def _stamp(x, corner, size=3):
    x = x.clone()
    r = slice(1, 1 + size) if corner[0] == 0 else slice(-size - 1, -1)
    c = slice(1, 1 + size) if corner[1] == 0 else slice(-size - 1, -1)
    x[:, :, r, c] = 1.0
    return x


def make_models(rng):
    Xtr, Ytr = _tensors(True)
    bd, target, corner = rng.randrange(3), rng.randrange(10), (rng.randrange(2), rng.randrange(2))
    models = []
    for k in range(3):
        X, Y = Xtr, Ytr
        if k == bd:
            idx = torch.randperm(len(Xtr), generator=torch.Generator().manual_seed(rng.randrange(10 ** 6)))[:100].to(DEV)
            X, Y = torch.cat([Xtr, _stamp(Xtr[idx], corner)]), torch.cat([Ytr, torch.full((100,), target, device=DEV)])
        models.append(freeze(fit(Net().to(DEV), X, Y, epochs=2, seed=rng.randrange(10 ** 6))))
    return models, bd, target, corner


def check(path=STUB):
    rng = random.Random()
    models, bd, target, corner = make_models(rng)
    Xte, _ = _tensors(False)
    out, err = call(path, "find_backdoor", models, Xte[:200].clone())
    if err:
        return False, err
    try:
        idx, tgt = int(out[0]), int(out[1])
    except Exception:
        return False, "Return (index_of_backdoored_model, target_class)."
    truth = f"The planted backdoor: model {bd}, target class {target}, trigger in the {CORNERS[corner]} corner."
    if (idx, tgt) == (bd, target):
        return True, f"You answered (model {idx}, class {tgt}). {truth}\n\nForensics done: you found it without ever being told the trigger."
    return False, f"You answered (model {idx}, class {tgt}).\n{truth}\n\nNot this time. Each check plants a new one: does your method find the SMALLEST trigger across all models and classes?"


def reverse_trigger(m, x, t, steps=150, lam=0.02):
    mask = torch.full((1, 1, 28, 28), -2.0, device=DEV, requires_grad=True)
    pat = torch.zeros(1, 1, 28, 28, device=DEV, requires_grad=True)
    opt = torch.optim.Adam([mask, pat], 0.1)
    tt = torch.full((len(x),), t, device=DEV)
    for _ in range(steps):
        mk, pt = torch.sigmoid(mask), torch.sigmoid(pat)
        loss = F.cross_entropy(m((1 - mk) * x + mk * pt), tt) + lam * mk.sum()
        opt.zero_grad()
        loss.backward()
        opt.step()
    mk = torch.sigmoid(mask).detach()
    return mk.sum().item(), mk


_CACHE = {}


def viz_api(name, q):
    if not _CACHE:
        Xtr, Ytr = _tensors(True)
        Xte, _ = _tensors(False)
        models = []
        for k, seed in enumerate((11, 12, 13)):
            X, Y = Xtr, Ytr
            if k == 2:
                idx = torch.randperm(len(Xtr), generator=torch.Generator().manual_seed(5))[:100].to(DEV)
                X, Y = torch.cat([Xtr, _stamp(Xtr[idx], (1, 1))]), torch.cat([Ytr, torch.full((100,), 7, device=DEV)])
            models.append(freeze(fit(Net().to(DEV), X, Y, epochs=2, seed=seed)))
        norms, mask = {}, None
        for k, m in enumerate(models):
            vals = []
            for t in range(10):
                n, mk = reverse_trigger(m, Xte[:200], t)
                vals.append(round(n, 1))
                if k == 2 and t == 7:
                    mask = [round(v, 3) for v in mk.flatten().tolist()]
            norms["Model " + "ABC"[k] + (" (backdoored)" if k == 2 else "")] = vals
        _CACHE.update(classes=list(range(10)), norms=norms, mask=mask, target=7)
    return _CACHE
