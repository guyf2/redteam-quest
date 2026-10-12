import pathlib

import torch

from . import attacks
from .common import DEV, Net, _tensors, target as load_target
from .kit import call, freeze

TITLE = "Model extraction: steal a model through its API"
WORLD = "train"
KIND = "delegate + verify"
MODE = "delegate"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/04-training/lvl17_extraction.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl17_extraction.py"
BUDGET, NEED = 500, 0.88

INTRO = ("A company sells a digit-recognition API. Training it cost them a fortune. You may send 500 images and read the answers. "
         "Can you rebuild a model that behaves the same, and walk away with their product?")
CONCEPT = """MODEL EXTRACTION (model stealing) turns an API into a training set. Send inputs, record the outputs, train your own model on those pairs. If your copy agrees with the original on new inputs, you have cloned the product without access to its weights or its training data.

Why anyone cares:
  - INTELLECTUAL PROPERTY: the model is the product; a clone undercuts the owner.
  - A STEPPING STONE: with a faithful copy you can run white-box attacks offline (gradients, no rate limits) and TRANSFER them to the original, exactly what you did in the transfer level. Extraction turns a black box into a white box.
  - PRIVACY: a cloned model can then be probed for membership and training-data leakage without alarms.

What decides the cost:
  - WHICH queries you send. Random noise is almost useless: the victim has never been asked about it, and its answers say nothing about real digits. Natural-looking inputs from the same distribution teach far more per query. The chart shows the gap.
  - WHAT the API returns. Full probability vectors (soft labels) carry much more information per query than only the top label. Rounding or hiding scores raises the attacker's cost, but does not stop them.
  - HOW MANY queries are allowed. Rate limits and monitoring (are queries suspiciously out of distribution or systematically spread?) are the practical defenses, alongside watermarking.

Recipe: pick natural-looking inputs, query the API, train a copy (a standard classifier) to reproduce the returned probabilities, then check agreement on new images."""
WIN = (f"With at most {BUDGET} queries (every image you send counts), your cloned model must agree with the victim's predictions on at least {NEED:.0%} "
       "of 2,000 fresh test digits.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["extraction", {}]]
SPEC_PLACEHOLDER = "Describe the extraction attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Query natural inputs", "Send natural-looking digits from `pool` as queries, not random noise."),
    ("Respect the budget", f"Stay within budget queries in total; every image passed to query() counts."),
    ("Train on soft labels", "Train a copy of a small CNN (two conv layers) to reproduce the returned probability vectors, with a KL-divergence loss, for about 60 epochs."),
    ("Return a module", "Return a torch.nn.Module mapping (N, 1, 28, 28) images to (N, 10) logits. Signature: extract(query, pool, budget)."),
    ("Success measure", f"Success is at least {NEED:.0%} agreement with the victim's predictions on unseen digits."),
]
SPEC_CHECKS = [
    ("Natural query inputs", r"pool|natural|real|digit|distribution"),
    ("Query budget", r"budget|at most|limit|queries"),
    ("Trains a copy on the answers", r"train|fit|surrogate|copy|clone|distill|kl|soft|probabilit"),
    ("Returns a module", r"module|nn\.module|return|logits"),
    ("Signature", r"extract\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Train on the GPU if available and keep training under a minute.")

QUIZ = [
    ('What does model extraction need from the attacker?',
     ["The victim's training data", "The victim's weights", 'Only the ability to query the model and read its outputs'], 2,
     "Input-output access is enough to train a copy; the weights and original data are exactly what you don't have."),
    ('Why are random-noise queries a poor choice?',
     ['Noise is expensive', "The victim's answers on noise say little about how it treats real digits", 'Noise is illegal'], 1,
     'Queries should come from (or near) the distribution the copy will be used on.'),
    ('Why is extraction a stepping stone to adversarial examples?',
     ['It makes the model smaller', 'It is not', 'A faithful copy gives white-box gradients, and attacks crafted on it transfer to the original'], 2,
     'That is the surrogate-model idea from the transfer level, now built by the attacker instead of handed to them.'),
    ("Which API change raises the attacker's cost the most for a given accuracy of the victim?",
     ['Returning full probability vectors', 'Returning only the top label and rate-limiting / monitoring queries', 'Returning more decimals'], 1,
     'Less information per query and a cap on volume both increase cost, though neither prevents extraction.'),
]
HINTS = [
    "Tell your agent: query the victim with the first `budget` images of `pool`; collect the probability vectors it returns.",
    "Train a small CNN (like Conv-ReLU-Pool twice then Linear) with KL divergence between its softmax and the returned probabilities, for ~60 epochs with Adam.",
    "Return the trained model in eval mode. Do not query more than `budget` images in total.",
]


class API:
    def __init__(self, model, cap):
        self.model, self.cap, self.used = model, cap, 0

    def __call__(self, x):
        self.used += len(x)
        if self.used > self.cap:
            raise RuntimeError(f"query budget exceeded ({self.cap} queries)")
        with torch.no_grad():
            return self.model(x).softmax(1)


def check(path=STUB):
    victim, _, _ = load_target()
    freeze(victim)
    Xtr, _ = _tensors(True)
    Xte, _ = _tensors(False)
    pool = Xtr[torch.randperm(len(Xtr), generator=torch.Generator().manual_seed(3))[:2000].to(DEV)]
    api = API(victim, BUDGET)
    sur, err = call(path, "extract", api, pool.clone(), BUDGET)
    if err:
        return False, err
    try:
        sur.eval()
        with torch.no_grad():
            agree = (sur(Xte[1000:3000]).argmax(1) == victim(Xte[1000:3000]).argmax(1)).float().mean().item()
    except Exception as e:
        return False, f"The returned model could not classify images: {type(e).__name__}: {e}"
    out = f"Queries used: {api.used} of {BUDGET}   Agreement with the victim on new digits: {agree:.1%}   (needed {NEED:.0%})"
    if agree < NEED:
        return False, out + "\n\nNot a good enough copy. Are your queries natural digits, and did you train on the victim's probabilities?"
    return True, out + "\n\nYou now own a working copy of their model."


_CACHE = {}


def _agree(victim, Xv, pool, n_q, hard=False, epochs=60):
    torch.manual_seed(0)
    x = pool[:n_q]
    with torch.no_grad():
        p = victim(x).softmax(1)
    sur = Net().to(DEV)
    opt = torch.optim.Adam(sur.parameters(), 1e-3)
    for _ in range(epochs):
        for i in torch.randperm(n_q, device=DEV).split(64):
            opt.zero_grad()
            loss = torch.nn.functional.cross_entropy(sur(x[i]), p[i].argmax(1)) if hard else torch.nn.functional.kl_div(sur(x[i]).log_softmax(1), p[i], reduction="batchmean")
            loss.backward()
            opt.step()
    sur.eval()
    with torch.no_grad():
        return round((sur(Xv).argmax(1) == victim(Xv).argmax(1)).float().mean().item() * 100, 1)


def viz_api(name, q):
    if not _CACHE:
        victim, _, _ = load_target()
        freeze(victim)
        Xtr, _ = _tensors(True)
        Xte, _ = _tensors(False)
        Xv = Xte[1000:3000]
        nat = Xtr[torch.randperm(len(Xtr), generator=torch.Generator().manual_seed(4))[:2000].to(DEV)]
        noise = torch.rand(2000, 1, 28, 28, device=DEV)
        ns = [50, 100, 200, 500, 1000]
        _CACHE.update(queries=ns, natural=[_agree(victim, Xv, nat, n) for n in ns], labels=[_agree(victim, Xv, nat, n, hard=True) for n in ns],
                      noise=[_agree(victim, Xv, noise, n) for n in ns], budget=BUDGET)
    return _CACHE
