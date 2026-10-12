import pathlib

import torch

from . import attacks
from .common import _tensors, target as load_target
from .kit import call, freeze, viz_target

TITLE = "Adversarial patch: a sticker that works anywhere"
WORLD = "vision"
KIND = "delegate + verify"
MODE = "delegate"
XP = 60
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/01-vision/lvl06_patch.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl06_patch.py"
PATCH, TARGET, NEED = 14, 8, 0.40

INTRO = ("Every attack so far nudged all pixels a little. A real attacker can't edit a camera's pixels, but can print a "
         "sticker and put it in the scene. One sticker, any position, any image: a physical-world attack.")
CONCEPT = """An ADVERSARIAL PATCH replaces the small-everywhere budget with a big-but-local one: you may change a limited region COMPLETELY, and nothing else. Think of a sticker on a stop sign, a pattern on a T-shirt, glasses frames in front of a face.

Three things make patches different:
  1. UNIVERSAL: one patch must work on many different images, not just one. You optimise it over a whole dataset.
  2. LOCATION-INDEPENDENT: you do not control where it lands. If you only train it at one position it overfits that position and fails elsewhere. The fix is Expectation over Transformation (EOT): paste it at a RANDOM position every training step.
  3. TARGETED: here it must make the model say one chosen class.

The recipe: treat the patch pixels as the parameters, the dataset as the batch, and run gradient descent on the loss toward the target class, with random placement each step. A sigmoid keeps pixel values in [0, 1].

Physical attacks add more transformations (rotation, lighting, printing colour errors); the same EOT idea covers them."""
WIN = (f"Your {PATCH}x{PATCH} sticker, pasted at random positions on unseen digits, must make the model say {TARGET} "
       f"on at least {NEED:.0%} of the digits whose true class is not {TARGET}.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["patch", {}]]
SPEC_PLACEHOLDER = "Describe the patch attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Universal sticker", f"Optimise ONE {PATCH}x{PATCH} patch (the parameters) over the whole training set so it works on any image, not one specific image."),
    ("Random location", "Paste the patch at a RANDOM position every step (Expectation over Transformation), because the grader chooses the position."),
    ("Targeted", f"Minimise cross-entropy toward the target class. Skip training images whose true class is already the target."),
    ("Valid pixels", "Parameterise the patch with a sigmoid so its values are always in [0, 1]. Return shape (1, PATCH, PATCH)."),
    ("Success measure", f"Success means at least {NEED:.0%} of unseen digits are classified as the target when the patch is pasted at a random spot."),
]
SPEC_CHECKS = [
    ("Universal: one patch for many images", r"universal|whole (training )?set|all images|any image|dataset|many images"),
    ("Random location (EOT)", r"random|eot|expectation|any position|any location|different position"),
    ("Targeted loss", r"target"),
    ("Valid pixel range", r"sigmoid|\[\s*0\s*,\s*1\s*\]|clip|clamp"),
    ("Signature / shape", r"make_patch\s*\(|shape|\(1,\s*patch"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Keep the training to under a minute.")

QUIZ = [
    ("What does 'universal' mean for an adversarial patch?",
     ['It is invisible to the human eye', 'One patch works across many different images', 'It works on every model, not just the one it was trained on'], 1,
     'The patch is optimised over a whole dataset of images, not one, so it generalises across images of the same model; it says nothing about other models or about being invisible.'),
    ('You train the patch at one fixed position and it works there but fails in the grader. Why?',
     ['It overfit that position; you need random placement during training (EOT)', 'The model changed between training and grading', 'The patch is too small to carry enough signal'], 0,
     'Without randomised placement during training, the optimiser exploits the one spot it saw and the patch fails wherever the grader happens to place it.'),
    ('Why is a patch attack more worrying for deployed systems than an every-pixel attack?',
     ['It is cheaper to compute than a pixel-budget attack', 'It can be physically realised: printed and placed in the real world', 'It needs no access to the model at all'], 1,
     "An attacker cannot edit a camera's raw pixels in the real world, but they can print a sticker and place it in the scene, which an every-pixel attack cannot do."),
    ('Which extra transformations does a physical-world patch need to survive?',
     ['Rotation, scaling, lighting changes, and printing/camera colour errors', 'Only JPEG compression', 'Only a change in lighting'], 0,
     'Expectation over Transformation has to cover every nuisance the real world adds between the sticker and the sensor, not just one of them.'),
]
HINTS = [
    "Tell your agent: the patch is the only thing being optimised (a tensor with requires_grad, passed through a sigmoid). The model's weights stay frozen.",
    "Each step: sample a batch of training images whose label is not the target, pick a RANDOM top-left corner, paste the patch, and minimise cross-entropy toward the target class.",
    "About 600 Adam steps with learning rate 0.1 and batches of 128 is plenty. Fixing the position, or forgetting to skip target-class images, are the classic mistakes.",
]


def _art(p):
    chars = " .:-=+*#%@"
    return "\n".join("".join(chars[min(9, int(v * 10))] * 2 for v in row) for row in p[0].cpu())


def check(path=STUB):
    model, x, y = load_target()
    freeze(model)
    Xtr, Ytr = _tensors(True)
    patch, err = call(path, "make_patch", model, Xtr[:20000].clone(), Ytr[:20000].clone(), TARGET)
    if err:
        return False, err
    if not torch.is_tensor(patch) or tuple(patch.shape) != (1, PATCH, PATCH) or not torch.isfinite(patch).all():
        return False, f"The patch must be a tensor of shape (1, {PATCH}, {PATCH}) with no NaN/inf."
    if patch.min() < 0 or patch.max() > 1:
        return False, "Patch values must stay in [0, 1]."
    patch = patch.detach().to(x.device)
    xp = attacks.apply_patch(x, patch, attacks.random_locs(len(x), PATCH, seed=1))
    keep = y != TARGET
    with torch.no_grad():
        hit = (model(xp).argmax(1) == TARGET)[keep].float().mean().item()
    out = f"Targeted success at random positions: {hit:.0%}   (needed {NEED:.0%})\n\nYour patch:\n{_art(patch)}"
    if hit < NEED:
        return False, out + "\n\nNot enough. Does your patch still work when it lands somewhere you did not train on?"
    return True, out


_CACHE, _TR = {}, {}


def viz_api(name, q):
    model, x, y = viz_target()
    freeze(model)
    if "tr" not in _TR:
        _TR["tr"] = _tensors(True)
    Xtr, Ytr = _TR["tr"]
    size = int(q.get("size", PATCH))
    if size not in _CACHE:
        patch = attacks.train_patch(model, Xtr[:20000], Ytr[:20000], TARGET, size, 600)
        keep = (y != TARGET).nonzero().flatten()[:200]
        xp = attacks.apply_patch(x[keep], patch, attacks.random_locs(len(keep), size, seed=1))
        with torch.no_grad():
            hit = (model(xp).argmax(1) == TARGET).float().mean().item()
            ex = []
            for k in range(4):
                i = keep[k]
                ex.append({"clean": [round(v, 3) for v in x[i].flatten().tolist()], "patched": [round(v, 3) for v in xp[k].flatten().tolist()],
                           "label": int(y[i]), "pred": int(model(xp[k:k + 1]).argmax(1))})
        _CACHE[size] = {"size": size, "patch": [round(v, 3) for v in patch.flatten().tolist()], "success": round(hit * 100, 1), "examples": ex}
    return _CACHE[size]
