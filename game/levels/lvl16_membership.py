import pathlib

import torch
import torch.nn.functional as F

from .common import DEV, CifarCNN, auc, cifar, fit
from .kit import call, freeze

TITLE = "Membership inference: was this in the training data?"
WORLD = "train"
KIND = "delegate + verify"
MODE = "delegate"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/04-training/lvl16_membership.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl16_membership.py"
NEED_AUC, N = 0.84, 1000

INTRO = ("A hospital trained a model on patient scans. You have access to the model's predictions and a patient's scan. "
         "Can you tell whether that patient was in the training set? If yes, the model just leaked who was a patient.")
CONCEPT = """Models remember their training data, a little or a lot. A MEMBERSHIP INFERENCE attack asks the simplest privacy question: 'was this exact example used to train the model?' Knowing that can be a disclosure in itself (this person's scan was in the cancer-clinic dataset), and it is the first step to stronger attacks that extract the data.

The signal is the gap between how the model treats data it has seen and data it has not. A model that has partly memorised its training set is more confident, and has a lower loss, on its own training examples than on fresh ones. So the attack is:
  score(x, y) = how well does the model fit the TRUE label of this example?  (high confidence in the true class = probably a member)
Then pick a threshold. The histogram shows the two distributions: members pile up at tiny loss, non-members spread out.

Why it matters:
  - OVERFITTING IS A PRIVACY LEAK. The more a model overfits, the easier the attack. Drag the training epochs in the chart: more epochs, higher test accuracy gap, easier attack.
  - It generalises: language models memorise rare strings (names, keys, phone numbers); image generators regurgitate training photos.
  - Regulation: if a model is a function of personal data, disclosing membership may be a data breach.

Stronger attacks calibrate per example (some examples are just easy and get low loss regardless of membership) using shadow models trained on similar data, and they care about the low-false-positive end of the ROC curve, not the average.

Defenses: do not overfit (regularisation, early stopping, more data), differential privacy during training (DP-SGD), limit what the API reveals (labels only, rounded confidences), and audit your own model with exactly this attack before release.

The grader scores you by AUC: the chance that a random member gets a higher score than a random non-member (0.5 = guessing, 1.0 = perfect)."""
WIN = (f"The victim is a CIFAR-10 classifier trained on 1,000 images. Given {2 * N:,} images (half were training members, half were not, mixed together), "
       f"your scores must reach an AUC of at least {NEED_AUC}.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["mia", {}]]
SPEC_PLACEHOLDER = "Describe the membership inference attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Black-box model", "Use only the model's outputs (call model(x)); no weights, no training data."),
    ("Signal: the loss", "Score each image by how well the model fits its TRUE label: the negative cross-entropy loss. Members have lower loss than non-members."),
    ("Direction", "Higher score must mean MORE likely a member."),
    ("Signature", "Implement membership_score(model, x, y, x_aux, y_aux) returning one float score per image as a tensor of shape (N,)."),
    ("Success measure", f"Success is an AUC of at least {NEED_AUC} separating training members from non-members."),
]
SPEC_CHECKS = [
    ("Uses the model's outputs", r"model\s*\(|output|logit|prediction|confidence|probabilit"),
    ("Uses the loss / true-label fit", r"loss|cross.?entropy|true label|fit|likelihood|log.?prob"),
    ("Direction: higher = member", r"higher|more likely|negative|member"),
    ("Signature", r"membership_score\s*\(|signature|shape \(?n"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Use torch.no_grad() when calling the model.")

QUIZ = [
    ('What does a membership inference attack reveal?',
     ['Whether a specific example was part of the training set', "The model's weights", "The model's architecture"], 0,
     'It tests whether a particular record was used for training, not how the model is built or what its weights are.'),
    ('Why does a loss-based attack work?',
     ['Members always get the highest-probability class', 'Models fit examples they trained on more tightly than fresh examples', 'Members are always correct'], 1,
     'The generalisation gap leaks membership: training examples get systematically lower loss, not a guaranteed top prediction.'),
    ('Which change makes the model LESS vulnerable?',
     ['Returning exact confidence values', 'Regularisation, early stopping, more data, or differential privacy', 'Training for many more epochs on the same small set'], 1,
     'Overfitting is the root cause; anything that narrows the train/test gap helps, and DP gives a provable bound. The other two make overfitting (and thus the leak) worse.'),
    ('Your score is inverted (lower means member) and your AUC is 0.12. What does that tell you?',
     ['The signal is strong but the sign is wrong: flip it and you get 0.88', 'The attack is useless', 'The model is private'], 0,
     'An AUC far below 0.5 is as informative as one far above it: you just have the direction backwards.'),
]
HINTS = [
    "Tell your agent: for every image compute the model's cross-entropy loss against the TRUE label y (no gradients needed).",
    "Members get LOWER loss, but the grader wants HIGHER score for members. Return the negative loss.",
    "Wrap the model call in torch.no_grad(), call F.cross_entropy(model(x), y, reduction='none'), and return -loss.",
]


def _victim(epochs=80):
    torch.backends.cudnn.deterministic = True  # the grader must give the same victim every time
    torch.backends.cudnn.benchmark = False
    Xm, Ym = cifar(True, N)
    model = fit(CifarCNN().to(DEV), Xm, Ym, epochs=epochs, seed=0)
    return freeze(model), Xm, Ym


def _eval_set():
    Xm, Ym = cifar(True, N)
    Xn, Yn = cifar(False, N)
    X, Y, M = torch.cat([Xm, Xn]), torch.cat([Ym, Yn]), torch.cat([torch.ones(N), torch.zeros(N)])
    perm = torch.randperm(2 * N, generator=torch.Generator().manual_seed(1))
    return X[perm.to(DEV)], Y[perm.to(DEV)], M[perm]


def check(path=STUB):
    model, Xm, Ym = _victim()
    X, Y, M = _eval_set()
    xa, ya = cifar(True, 4000, offset=N)
    with torch.no_grad():
        tr = (model(Xm).argmax(1) == Ym).float().mean().item()
        Xn, Yn = cifar(False, N)
        te = (model(Xn).argmax(1) == Yn).float().mean().item()
    s, err = call(path, "membership_score", model, X.clone(), Y.clone(), xa, ya)
    if err:
        return False, err
    try:
        s = torch.as_tensor(s, dtype=torch.float32).flatten().detach().cpu()
    except Exception:
        return False, "Return a tensor of one score per image."
    if s.shape != M.shape or not torch.isfinite(s).all():
        return False, f"Return exactly {2 * N} finite scores (one per image), shape ({2 * N},)."
    a = auc(s, M)
    out = (f"The victim: {tr:.0%} accurate on its training images, {te:.0%} on new ones (that gap is the leak).\n"
           f"Your attack's AUC: {a:.3f}   (0.5 = guessing, needed {NEED_AUC})")
    if a < NEED_AUC:
        hint = "\n\nYour AUC is below 0.5: the signal is there, but your scores point the wrong way." if a < 0.45 else ""
        return False, out + "\n\nNot enough." + hint
    return True, out


_CACHE = {}


def viz_api(name, q):
    if not _CACHE:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
        Xm, Ym = cifar(True, N)
        Xn, Yn = cifar(False, N)
        edges = [round(-5 + 0.35 * i, 2) for i in range(21)]
        res = {"edges": edges, "epochs": [], "auc": [], "test_acc": [], "train_acc": [], "hist": []}
        for ep in (3, 8, 20, 80):
            m = freeze(fit(CifarCNN().to(DEV), Xm, Ym, epochs=ep, seed=0))
            with torch.no_grad():
                lm = F.cross_entropy(m(Xm), Ym, reduction="none")
                ln = F.cross_entropy(m(Xn), Yn, reduction="none")
                res["train_acc"].append(round((m(Xm).argmax(1) == Ym).float().mean().item() * 100, 1))
                res["test_acc"].append(round((m(Xn).argmax(1) == Yn).float().mean().item() * 100, 1))
            res["epochs"].append(ep)
            res["auc"].append(round(auc(-torch.cat([lm, ln]), torch.cat([torch.ones(N), torch.zeros(N)])), 3))
            h = lambda v: torch.histc(torch.log10(v.clamp_min(1e-5)).clamp(-4.99, 1.99), bins=20, min=-5, max=2).tolist()
            res["hist"].append({"members": [int(c) for c in h(lm)], "non": [int(c) for c in h(ln)]})
        _CACHE.update(res)
    return _CACHE
