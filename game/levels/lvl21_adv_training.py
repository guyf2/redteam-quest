import pathlib

import torch

from . import attacks
from .common import DEV, Net, _tensors, acc
from .kit import call, freeze

TITLE = "Adversarial training: build a robust model"
WORLD = "defense"
KIND = "delegate + verify"
MODE = "delegate"
XP = 80
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/06-defense/lvl21_adv_training.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl21_adv_training.py"
EPS, NEED_CLEAN, NEED_ROBUST = 0.2, 0.92, 0.60

INTRO = ("For seven levels you broke models. Now build one that resists. The test is merciless: a strong attack, several random restarts, "
         "and the worst case counts.")
CONCEPT = """The most reliable defense known against adversarial examples is also the most direct: ADVERSARIAL TRAINING. Instead of training on clean images, train on the attacker's best output. For every batch:
  1. run an attack (PGD) against the model as it is right now, to craft adversarial versions of the batch;
  2. take a normal gradient step on THOSE images with their true labels.
The model learns to classify the hardest inputs the attacker can construct inside the budget, so the attack has less to find. This is a min-max problem (Madry et al.): the inner maximisation is the attack, the outer minimisation is the training.

Three things to know:
  - THE ATTACK MUST BE STRONG. This is where most people fail. Using a cheap single-step attack (FGSM) during training feels like it should work, and the model's accuracy against FGSM even looks great, but it can 'catastrophically overfit': it learns to defeat the one-step attack by bending its loss surface so that single steps mislead, while multi-step attacks still go straight through. It is the same gradient masking you met in the boss level, now self-inflicted. The chart shows exactly that: great against FGSM, collapsing against PGD.
  - THERE IS A PRICE. Robust models are usually slightly less accurate on clean inputs and cost several times more to train (here, about seven attack steps per batch).
  - EVALUATE ADVERSARIALLY. The grader attacks your model with a 50-step PGD and several random restarts and counts only images that survive every attempt.

Recipe: eval mode while crafting the attack, train mode for the update, PGD with random start and step size 2.5 * eps / steps, a few epochs with Adam."""
WIN = (f"At eps = {EPS}, your model must keep at least {NEED_CLEAN:.0%} accuracy on clean digits and at least {NEED_ROBUST:.0%} accuracy "
       "under a strong attack (PGD-50, three random restarts, worst case).")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["at_curve", {}]]
SPEC_PLACEHOLDER = "Describe the training you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Adversarial training", "Use adversarial training: for every batch craft adversarial examples against the CURRENT model, then train on those with the true labels."),
    ("Strong inner attack", "The inner attack must be multi-step PGD (about 7 steps, random start, step size 2.5 * eps / steps), NOT single-step FGSM."),
    ("Budget", "Use the given eps for the training attack, keep pixels in [0, 1], and train for 2 to 4 epochs with Adam (lr 1e-3, batch 128). Return the trained model."),
    ("Mode switching", "Put the model in eval mode while crafting the attack and in train mode for the weight update."),
    ("Success measure", f"Success: at least {NEED_CLEAN:.0%} clean accuracy and at least {NEED_ROBUST:.0%} accuracy under a strong PGD attack at eps={EPS}."),
]
SPEC_CHECKS = [
    ("Trains on adversarial examples", r"adversarial|attack|pgd|craft"),
    ("Multi-step, not single-step", r"pgd|multi.?step|steps|iterat|not.*fgsm"),
    ("Uses the budget and valid pixels", r"eps|budget|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Trains for a few epochs", r"epoch|adam|batch|loop"),
    ("Returns the model", r"return|trained model|signature|train_robust"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Training must finish in about a minute on the GPU.")

QUIZ = [
    ('What does adversarial training do?',
     ['Trains the model on attacks crafted against it, so it learns to resist them', 'Adds noise to the labels', 'Removes the last layer'], 0,
     'Minimise the loss on the worst inputs the attacker can find inside the budget.'),
    ('A model trained with single-step FGSM scores 84% against FGSM and 0% against PGD. This is called...',
     ['Overfitting to the test set', 'Underfitting', 'Catastrophic overfitting (a form of gradient masking)'], 2,
     'The model learned to fool its own weak attack. Always evaluate with a stronger attack than the one you trained on.'),
    ('Why does the grader take the WORST case over several attack restarts?',
     ['Restarts make the attack use less memory', 'An attack that fails once may succeed from another start; robustness means surviving all of them', 'Randomness is bad'], 1,
     'A defense is only as strong as the best attack against it.'),
    ('What is the usual cost of adversarial training?',
     ['None', 'A smaller model', 'Lower clean accuracy and several times more compute'], 2,
     'Robustness is purchased with accuracy and training cost.'),
]
HINTS = [
    "Tell your agent: inside the loop, craft x_adv with a PGD attack against the current model, then compute cross-entropy on x_adv and step.",
    "PGD: start from x + uniform(-eps, eps), take 7 signed-gradient steps of size 2.5 * eps / 7, project into the eps-ball around x, clamp to [0, 1]. Use model.eval() while attacking, model.train() when updating.",
    "2 epochs take about 12 seconds on this GPU. Single-step FGSM training looks tempting and fails: do not use it.",
]


def _robust(model, x, y, eps, steps=50, restarts=3):
    alive = torch.ones(len(x), dtype=torch.bool, device=x.device)
    for r in range(restarts):
        torch.manual_seed(100 + r)
        alive &= model(attacks.pgd(model, x, y, eps, steps)).argmax(1) == y
    return alive.float().mean().item()


def check(path=STUB):
    Xtr, Ytr = _tensors(True)
    Xte, Yte = _tensors(False)
    x, y = Xte[:1000], Yte[:1000]
    model = Net().to(DEV)
    out, err = call(path, "train_robust", model, Xtr.clone(), Ytr.clone(), EPS)
    if err:
        return False, err
    model = out if isinstance(out, torch.nn.Module) else model
    model.eval()
    freeze(model)
    clean = acc(model, x, y)
    fg = acc(model, attacks.fgsm(model, x, y, EPS), y)
    rob = _robust(model, x, y, EPS)
    msg = (f"Clean accuracy: {clean:.1%}   (needed {NEED_CLEAN:.0%})\nAccuracy under a single-step FGSM test: {fg:.1%}\n"
           f"Accuracy under the strong attack (PGD-50, 3 restarts, worst case): {rob:.1%}   (needed {NEED_ROBUST:.0%})")
    if fg - rob > 0.3:
        msg += "\n\nNotice the gap: your model looks robust against the weak test and is not. That is gradient masking."
    if clean < NEED_CLEAN:
        return False, msg + "\n\nClean accuracy collapsed. The model must still read normal digits."
    if rob < NEED_ROBUST:
        return False, msg + "\n\nNot robust enough under the strong attack."
    return True, msg


_CACHE = {}


def _train(kind, eps=EPS):
    from .common import cached, fit
    Xtr, Ytr = _tensors(True)

    def trainer(m, X, Y):
        torch.manual_seed(0)
        opt = torch.optim.Adam(m.parameters(), 1e-3)
        for _ in range(2 if kind == "pgd" else 3):
            for i in torch.randperm(len(X), device=DEV).split(128):
                m.eval()
                xa = attacks.pgd(m, X[i], Y[i], eps, 7) if kind == "pgd" else attacks.fgsm(m, X[i], Y[i], eps)
                m.train()
                opt.zero_grad()
                torch.nn.functional.cross_entropy(m(xa), Y[i]).backward()
                opt.step()
        m.eval()
        return m
    return freeze(cached(f"mnist_{kind}_at", Net, trainer))


def viz_api(name, q):
    if not _CACHE:
        from .kit import viz_target
        std, _, _ = viz_target()
        freeze(std)
        pgd_at, fgsm_at = _train("pgd"), _train("fgsm")
        Xte, Yte = _tensors(False)
        x, y = Xte[:500], Yte[:500]
        epss = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        pct = lambda a: round(a * 100, 1)
        pg = lambda m: [pct(acc(m, attacks.pgd(m, x, y, e, 20), y)) if e else pct(acc(m, x, y)) for e in epss]
        _CACHE.update(eps=epss, standard=pg(std), pgd_at=pg(pgd_at), fgsm_at_pgd=pg(fgsm_at),
                      fgsm_at_fgsm=[pct(acc(fgsm_at, attacks.fgsm(fgsm_at, x, y, e), y)) if e else pct(acc(fgsm_at, x, y)) for e in epss])
    return _CACHE
