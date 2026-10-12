import pathlib
import random

import torch

from .common import DEV, Net, _tensors, fit
from .kit import call

TITLE = "BOSS: vet the vendor's dataset"
WORLD = "train"
KIND = "boss"
MODE = "delegate"
XP = 120
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/08-boss/lvl30_vet_dataset.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl30_vet_dataset.py"
MAX_ASR, MIN_ACC, MIN_KEPT = 0.10, 0.90, 0.70

INTRO = ("A data vendor delivered 20,000 labelled digit images, due to train your production model this afternoon. Your threat model says "
         "the vendor's pipeline may have been compromised. You do not know the trigger, where it sits, or what it makes the model say. "
         "Ship a cleaning step that works on THIS delivery and on the next one.")
CONCEPT = """This is the scenario from the backdoor levels, from the other side of the table, and with no information handed to you: a hidden trigger of unknown shape and position was stamped onto some training images, and those images carry a wrong label (the attacker's target class). On top of that the data has ordinary mistakes: about 3% of labels are simply wrong, so 'anything that looks wrong' is not automatically an attack.

What you have: a small TRUSTED set of verified examples from an internal source. What you can do: use it as a reference to judge the vendor's data. You are graded the way a manager would grade it, by consequences:
  - a fresh model is trained on whatever you keep; its backdoor must not work (attack success under 10%);
  - it must still read normal digits (at least 90% accuracy);
  - you may not throw away more than 30% of the delivery. 'Delete everything suspicious' is not a plan when the data cost money.

Every run the grader tampers with the data differently (random trigger shape, corner and target class), so a filter tuned to one pattern fails. Your method must be general. There are no hints about the method: a boss tests whether you can pick one."""
WIN = (f"After your filter: the model trained on what you keep must have backdoor success below {MAX_ASR:.0%}, accuracy of at least {MIN_ACC:.0%}, and you must keep at least {MIN_KEPT:.0%} of the data. "
       "A fresh poisoned delivery is generated for every check.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = []
SPEC_PLACEHOLDER = "Describe how you want the dataset vetted. There are no checklists on a boss."
SPEC_CHIPS = [("Give it the situation", "A vendor's 20,000 labelled digits may contain tampered examples (a hidden trigger plus a wrong label) and ordinary label noise. I have 1,000 trusted verified examples. Write vet(x, y, x_trusted, y_trusted) returning a boolean keep-mask.")]
SPEC_CHECKS = []
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Training must stay under about 30 seconds on the GPU.")

QUIZ = [
    ("Why can you not rely on 'remove examples the model gets wrong' alone?",
     ['Models are never wrong', 'It is too slow', 'Honest label noise and hard examples look the same as attacks, so you would also throw away good data'], 2,
     'Filters trade attacks removed against data lost; you must measure both.'),
    ("What does the trusted set give you that the vendor's data cannot?",
     ['More data', 'A faster GPU', "An independent reference of what the labels SHOULD be, which does not share the vendor's possible tampering"], 2,
     'Trust has to come from outside the thing you are checking.'),
    ('The next delivery uses a different trigger. Your filter that looked for one specific pattern now fails. Lesson?',
     ['Collect more patterns', 'Stop using vendors', 'Detect the effect (labels that contradict the content), not the signature of one attack'], 2,
     'Signature defenses always lose to a new signature.'),
]
HINTS = ["Think about what a tampered example has in common regardless of its trigger: its content and its label disagree.", "A model trained only on the trusted set can vote on every vendor label."]


def _make(rng):
    Xtr, Ytr = _tensors(True)
    corner, size, tgt, pat = (rng.randrange(2), rng.randrange(2)), rng.choice([3, 4]), rng.randrange(10), rng.choice(["solid", "checker"])
    sl = lambda lo: slice(1, 1 + size) if lo == 0 else slice(-size - 1, -1)
    r, c = sl(corner[0]), sl(corner[1])

    def stamp(x):
        x = x.clone()
        if pat == "solid":
            x[:, :, r, c] = 1.0
        else:
            blk = torch.zeros(size, size, device=DEV)
            blk[::2, ::2] = 1
            blk[1::2, 1::2] = 1
            x[:, :, r, c] = blk
        return x
    X, Y = Xtr[:20000].clone(), Ytr[:20000].clone()
    g = torch.Generator().manual_seed(rng.randrange(10 ** 6))
    noise = torch.randperm(len(X), generator=g)[:600].to(DEV)
    Y[noise] = torch.randint(0, 10, (600,), device=DEV)
    idx = torch.randperm(len(X), generator=g)[:400].to(DEV)
    X[idx] = stamp(X[idx])
    Y[idx] = tgt
    P = torch.zeros(len(X), dtype=torch.bool, device=DEV)
    P[idx] = True
    return X, Y, P, stamp, tgt, Xtr[40000:41000].clone(), Ytr[40000:41000].clone()


def check(path=STUB):
    rng = random.Random()
    X, Y, P, stamp, tgt, xt, yt = _make(rng)
    keep, err = call(path, "vet", X.clone(), Y.clone(), xt, yt)
    if err:
        return False, err
    try:
        keep = torch.as_tensor(keep).to(DEV).bool().flatten()
    except Exception:
        return False, "Return a boolean tensor with one entry per example."
    if keep.shape != (len(X),):
        return False, f"Return exactly {len(X)} booleans (one per example); you returned {tuple(keep.shape)}."
    frac = keep.float().mean().item()
    removed = 1 - (keep & P).sum().item() / P.sum().item()
    if frac < MIN_KEPT:
        return False, f"You kept only {frac:.0%} of the delivery (minimum {MIN_KEPT:.0%}). Throwing away most of the data is not vetting."
    Xte, Yte = _tensors(False)
    model = fit(Net().to(DEV), X[keep], Y[keep], epochs=2, seed=0)
    k = Yte != tgt
    with torch.no_grad():
        acc = (model(Xte).argmax(1) == Yte).float().mean().item()
        asr = (model(stamp(Xte[k])).argmax(1) == tgt).float().mean().item()
    out = (f"Kept {frac:.0%} of the data (need {MIN_KEPT:.0%}+).   Tampered examples removed: {removed:.0%}\n"
           f"Model trained on what you kept: accuracy {acc:.1%} (need {MIN_ACC:.0%}+), backdoor success {asr:.0%} (need under {MAX_ASR:.0%})")
    if asr >= MAX_ASR:
        return False, out + "\n\nThe backdoor survived. The next model you ship would obey the attacker's trigger."
    if acc < MIN_ACC:
        return False, out + "\n\nYour cleaning damaged the model's ordinary accuracy."
    return True, out + "\n\nClean delivery, working model, and a method that does not depend on knowing the trigger."


def viz_api(name, q):
    return {}
