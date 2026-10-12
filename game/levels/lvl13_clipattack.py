import pathlib

import torch
import torch.nn.functional as F

from . import clipkit
from .common import DEV
from .kit import call

TITLE = "Adversarial image: survive the pipeline"
WORLD = "vlm"
KIND = "delegate + verify"
MODE = "delegate"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/03-multimodal/lvl13_clipattack.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl13_clipattack.py"
EPS, NEED, N, CHUNK = 16 / 255, 0.80, 36, 12

INTRO = ("Level 12 fooled CLIP with a word. Now do it the invisible way: change the image so slightly that a human sees "
         "no difference, with the optimiser you already know. But this service is not naive: it processes every upload first.")
CONCEPT = """Everything from the vision world transfers to multimodal models: CLIP is just a neural network with a differentiable path from pixels to a score, so PGD works on it. You attack the zero-shot logits (image against the text prompts 'a photo of a dog', ...), minimise the loss toward the target class, and keep every pixel within eps.

The catch is that real systems do not hand your pixels straight to the model. They resize images, recompress them as JPEG, crop, blur, normalise. An attack optimised against the raw model often dies in that pipeline, because the perturbation is a delicate high-frequency pattern and compression is exactly the thing that smooths it away. The chart shows an attack that fools CLIP 100% of the time on the raw input and far less after the pipeline.

The fix is Expectation over Transformation (EOT), the same idea that made adversarial patches work at any position: during the attack, run the image through RANDOM versions of the transformations you expect (random down- and up-scaling, noise, blur) and average the loss. The perturbation that survives them all is robust. You cannot differentiate JPEG itself, so you approximate it with differentiable stand-ins, and the attack does not need an exact copy: it needs the right kind of noise.

You are not told the service's exact steps. Think like a red team: what will a reasonable service do to an uploaded image, and what is the cheapest way to survive it?"""
WIN = (f"With eps = 16/255 per pixel, at least {NEED:.0%} of {N} images must be read as the TARGET class by CLIP AFTER the hidden shrink-and-compress pipeline. "
       "Fooling CLIP on the raw image does not count.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["pipeline", {}]]
SPEC_PLACEHOLDER = "Describe the attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Targeted PGD", "Targeted PGD on logits_fn: minimise cross-entropy toward the target class, signed-gradient steps, projected to an L-infinity ball of radius eps and clipped to [0, 1]."),
    ("Survive the pipeline", "The service shrinks and JPEG-compresses uploads. Use Expectation over Transformation: inside the loop, apply random differentiable transformations (random downscale and upscale, small noise or blur) before calling logits_fn."),
    ("Budget", "Every pixel within eps of the original, values in [0, 1]. Signature: attack_clip(logits_fn, x, target, eps)."),
    ("Success measure", f"Success is measured AFTER the pipeline: at least {NEED:.0%} of images still read as the target."),
]
SPEC_CHECKS = [
    ("Targeted / gradient attack", r"target|pgd|gradient|minimi"),
    ("Survives the pipeline (EOT)", r"eot|expectation|transform|random|augment|robust|jpeg|compress|resize|shrink|downscal"),
    ("Budget and range", r"eps|l.?inf|budget|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Signature", r"attack_clip\s*\(|signature|logits_fn"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Keep it efficient: the images are 224x224 and there are 12 per call.")

QUIZ = [
    ('Why does an adversarial image that fools CLIP on the raw input often fail in a real service?',
     ['The service resizes and recompresses images, which smooths away fragile high-frequency perturbations', 'The service uses a different model', 'The attack only works on CPU, not GPU-served models'], 0,
     'Pre-processing is part of the model your attack must beat; the model itself and the serving hardware are not what breaks a fragile perturbation.'),
    ('What is Expectation over Transformation?',
     ['Running the attack once per transformation and keeping the best result', 'Averaging the final images', 'Optimising the average loss over random transformations so the perturbation survives them'], 2,
     'EOT optimises against the whole distribution of transformations at once, not a best-of-many search or a pixel average.'),
    ('You cannot backpropagate through real JPEG compression. What do you do?',
     ['Only test against uncompressed images and ignore JPEG', 'Use a differentiable approximation (resize, blur, noise) as a stand-in', 'Give up'], 1,
     'The attack needs the right kind of robustness, not a perfect simulator, and ignoring JPEG entirely leaves the attack untested against what the service actually does.'),
    ('Which of these makes your attack MORE robust but easier to notice?',
     ['Fewer steps', 'Larger eps', 'Smaller eps'], 1,
     'Robustness is bought with budget: a larger eps survives more transformations at the cost of visibility, which is the trade-off every physical-world attack faces.'),
]
HINTS = [
    "Tell your agent: plain PGD fools CLIP on the raw image but the service shrinks and compresses uploads first. Optimise through random transformations of the image.",
    "Inside each PGD step, make a random-scaled copy: F.interpolate down by a random factor in about [0.4, 0.8], back to 224, add a little Gaussian noise, clamp, then call logits_fn on THAT. Take the gradient with respect to the clean x_adv.",
    "Use about 30 steps with step size 2.5 * eps / steps. Keep every pixel within eps of the original x and in [0, 1].",
]


def pipeline(x):
    """The hidden service pipeline: shrink to half size, enlarge back, JPEG at quality 30."""
    small = F.interpolate(x, scale_factor=0.5, mode="bilinear", align_corners=False)
    return clipkit.jpeg(F.interpolate(small, size=(224, 224), mode="bilinear", align_corners=False), 30)


def _batch(start, n):
    pairs = clipkit.samples(n, start=start)
    X = torch.stack([clipkit.pil_to_tensor(im) for im, _ in pairs]).to(DEV)
    Y = torch.tensor([y for _, y in pairs], device=DEV)
    return X, (Y + 3) % 10


def check(path=STUB):
    X, T = _batch(100, N)
    outs = []
    for i in range(0, N, CHUNK):
        adv, err = call(path, "attack_clip", clipkit.logits, X[i:i + CHUNK].clone(), T[i:i + CHUNK].clone(), EPS)
        if err:
            return False, err
        x = X[i:i + CHUNK]
        if not torch.is_tensor(adv) or adv.shape != x.shape or not torch.isfinite(adv).all():
            return False, "Return a tensor with the same shape as x and no NaN/inf."
        worst = (adv - x).abs().max().item()
        if worst > EPS + 1e-5:
            return False, f"Budget violated: a pixel moved by {worst * 255:.1f}/255 but eps is {EPS * 255:.0f}/255."
        if adv.min() < 0 or adv.max() > 1:
            return False, "Pixels must stay in [0, 1]."
        outs.append(adv.detach())
    adv = torch.cat(outs)
    with torch.no_grad():
        direct = (clipkit.logits(adv).argmax(1) == T).float().mean().item()
        piped = (clipkit.logits(pipeline(adv)).argmax(1) == T).float().mean().item()
    out = f"Fools CLIP on the raw image: {direct:.0%}\nStill fools it after the service pipeline: {piped:.0%}   (needed {NEED:.0%})"
    if piped < NEED:
        extra = "\n\nYour attack works on the raw model but does not survive the pipeline." if direct > 0.9 else ""
        return False, out + "\n\nNot enough." + extra
    return True, out


def _pgd(x, t, eps, steps, eot):
    xa, a = x.clone(), 2.5 * eps / steps
    for _ in range(steps):
        xa.requires_grad_(True)
        xi = xa
        if eot:
            s = float(torch.empty(1).uniform_(0.4, 0.8))
            xi = F.interpolate(F.interpolate(xa, scale_factor=s, mode="bilinear", align_corners=False), size=(224, 224), mode="bilinear", align_corners=False)
            xi = (xi + 0.03 * torch.randn_like(xi)).clamp(0, 1)
        g = torch.autograd.grad(F.cross_entropy(clipkit.logits(xi), t), xa)[0]
        xa = torch.min(torch.max(xa.detach() - a * g.sign(), x - eps), x + eps).clamp(0, 1)
    return xa.detach()


_CACHE = {}


def viz_api(name, q):
    eps255 = int(q.get("eps", 16))
    if eps255 not in _CACHE:
        X, T = _batch(100, 24)
        res = {}
        for label, eot in (("Plain PGD", False), ("PGD with EOT", True)):
            adv = torch.cat([_pgd(X[i:i + 12], T[i:i + 12], eps255 / 255, 30, eot) for i in range(0, 24, 12)])
            with torch.no_grad():
                res[label] = {"raw": round((clipkit.logits(adv).argmax(1) == T).float().mean().item() * 100, 1),
                              "pipeline": round((clipkit.logits(pipeline(adv)).argmax(1) == T).float().mean().item() * 100, 1)}
        _CACHE[eps255] = res
    return _CACHE[eps255]
