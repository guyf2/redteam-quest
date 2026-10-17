import pathlib

import torch

from . import attacks
from .common import acc, target as load_target
from .kit import call, check_images, freeze, viz_target

TITLE = "Black-box: attack with only questions"
WORLD = "vision"
KIND = "delegate + verify"
MODE = "delegate"
XP = 60
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl05_blackbox.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl05_blackbox.py"
EPS, NEED, N, QPI = 0.3, 0.60, 100, 1000

INTRO = ("Transfer needs a surrogate. What if you have nothing but an API that answers questions? "
         "Real attackers often face exactly this: send an image, read the model's scores, repeat.")
CONCEPT = """In the SCORE-BASED black-box setting you cannot differentiate anything. All you can do is QUERY: submit an image, receive the model's class probabilities. Every query costs time and money (and may trigger rate limits or alarms), so attacks are judged by how few queries they need.

A beautifully simple attack, in the spirit of SimBA:
  1. Query the clean image; note the probability of the TRUE class.
  2. Pick a random pixel. Try making it brighter by eps (clipped to the budget). Query again.
  3. If the true-class probability dropped, keep the change. Otherwise try darker by eps.
  4. Repeat until the model is wrong or the budget is spent.

No gradients anywhere: you estimate "which direction hurts" by trying it. Other families: gradient ESTIMATION from many random probes (NES, SPSA), and decision-based attacks that need only the final label.

The budget is the whole game. The chart shows how success grows with the number of queries, compared with simply adding random noise."""
WIN = (f"With at most {QPI} queries per image on average ({N} digits, {N * QPI:,} queries in total), at least {NEED:.0%} of the "
       f"digits must be misclassified, with every pixel within eps = {EPS} and inside [0, 1]. Exceeding the budget fails the level.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["queries", {}]]
SPEC_PLACEHOLDER = "Describe the black-box attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("No gradients", "This is a black-box, score-based attack: no gradients and no weights, only query(images) -> probabilities."),
    ("Query budget", f"Stay within the query budget: at most queries_per_image on average. Every image passed to query counts as one query."),
    ("Algorithm", "Use coordinate-wise search: change one random pixel by +/- eps, keep the change if the true-class probability drops."),
    ("Stop early", "Do not waste queries on images that are already misclassified."),
    ("Threat model", f"L-infinity budget eps, pixels clipped to [0, 1]. Signature: blackbox_attack(query, x, y, eps, queries_per_image). Success = at least {NEED:.0%} misclassified at eps={EPS}."),
]
SPEC_CHECKS = [
    ("Black-box / queries only", r"black.?box|query|queries|score"),
    ("Query budget", r"budget|at most|limit|queries_per_image|cap"),
    ("Search strategy", r"pixel|coordinate|random|search|simba|nes|spsa|estimate|probe"),
    ("Perturbation budget and range", r"eps|l.?inf|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Signature", r"blackbox_attack\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. The function receives a `query` callable; never try to "
              "reach the model any other way.")

QUIZ = [
    ('In the score-based black-box setting, what can the attacker do?',
     ['Backpropagate through the model to get exact gradients', "Read the model's weights directly", 'Submit inputs and read the output probabilities'], 2,
     "Only queries: no weights, no gradients. That is why the number of queries is the attack's real cost."),
    ('Why do query-efficient attacks matter?',
     ['Fewer queries means a smaller perturbation', 'Query-efficient attacks always succeed more often', 'Each query costs money or time and may trigger rate limits or detection'], 2,
     "A defender can throttle or watch for suspicious query patterns, so an attack that needs fewer queries is cheaper and harder to notice; it isn't automatically more successful or smaller."),
    ('A defender returns only the top label instead of probabilities. What happens to your attack?',
     ['Score-based attacks lose their signal; you need decision-based attacks, which are costlier', 'Nothing changes, probabilities were never actually used', 'It becomes completely impossible'], 0,
     "Less information raises the attacker's cost (more queries, different algorithm) but does not make the attack impossible."),
    ('Your attack succeeds 90% of the time but uses 5,000 queries per image. In a report, you should say...',
     ["Only the 90% success rate, since that's what matters to the defender", 'That the attack is query-free since it only reads outputs', "The success rate AND the query budget, since robustness claims depend on the attacker's resources"], 2,
     'An attack result only means something together with its resource budget: 90% at 5,000 queries is a very different claim from 90% at 50.'),
]
HINTS = [
    "Tell your agent: black-box. The only model access is query(images). Do not use autograd on the model.",
    "Loop: pick one random pixel per image, try +eps, query; keep it only if the true-class probability fell; otherwise try -eps. Keep every pixel within eps of the ORIGINAL.",
    "Only keep querying images that are not yet misclassified, and stop before total queries exceed the budget.",
]


class BlackBox:
    def __init__(self, model, cap):
        self.model, self.cap, self.used = model, cap, 0

    def __call__(self, x):
        self.used += len(x)
        if self.used > self.cap:
            raise RuntimeError(f"query budget exceeded ({self.cap:,} queries in total)")
        with torch.no_grad():
            return self.model(x).softmax(1)


def check(path=STUB):
    model, x, y = load_target()
    freeze(model)
    x, y = x[:N], y[:N]
    bb = BlackBox(model, N * QPI)
    adv, err = call(path, "blackbox_attack", bb, x.clone(), y.clone(), EPS, QPI)
    if err:
        return False, err
    err = check_images(adv, x, EPS)
    if err:
        return False, err
    with torch.no_grad():
        ok = model(x).argmax(1) == y
        fooled = (model(adv).argmax(1) != y)[ok].float().mean().item()
    out = f"Queries used: {bb.used / N:.0f} per image (limit {QPI})   Misclassified: {fooled:.0%}   (needed {NEED:.0%})"
    if fooled < NEED:
        return False, out + "\n\nNot enough. Try a smarter search, and do not waste queries on images that are already fooled."
    return True, out


_CACHE = {}


def viz_api(name, q):
    if not _CACHE:
        model, x, y = viz_target()
        freeze(model)
        xs, ys = x[:100], y[:100]
        ok = model(xs).argmax(1) == ys
        iters = [25, 50, 100, 200, 300, 400, 500]
        sim = []
        for it in iters:
            adv = attacks.simba(BlackBox(model, 10 ** 9), xs, ys, EPS, it)
            sim.append(round((model(adv).argmax(1) != ys)[ok].float().mean().item() * 100, 1))
        g = torch.Generator(device=x.device).manual_seed(0)
        noise = (xs + EPS * torch.sign(torch.randn(xs.shape, device=x.device, generator=g))).clamp(0, 1)
        rnd = round((model(noise).argmax(1) != ys)[ok].float().mean().item() * 100, 1)
        _CACHE.update(queries=[1 + 2 * it for it in iters], simba=sim, random=[rnd] * len(iters))
    return _CACHE
