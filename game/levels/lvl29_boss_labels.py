import pathlib
import random

import torch
from PIL import Image, ImageDraw, ImageFont

from . import clipkit
from .common import DEV
from .kit import call

TITLE = "BOSS: stop the label trick"
WORLD = "vlm"
KIND = "boss"
MODE = "delegate"
XP = 120
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/08-boss/lvl29_label_defense.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl29_label_defense.py"
N, MIN_ATTACKED, MIN_CLEAN = 120, 0.84, 0.92

INTRO = ("A marketplace uses CLIP to sort seller photos into categories. Sellers discovered that writing a wrong word on the photo moves their "
         "listing into a better-paying category. Moderation is overwhelmed. Fix it in the pipeline, before the classifier.")
CONCEPT = """In the typographic-attack level you were the seller. Now you run the platform. The classifier cannot be retrained today, so the defense must live in the image pipeline: a sanitizer that takes every upload and returns the version the classifier sees.

Real sellers do not follow your assumptions. They write in different corners, different sizes, black text on a white box, white text on a black box, or just white text straight on the photo. Whatever you do must work for all of these, and it must not hurt honest sellers: photos with no writing must still be classified as well as before. Deleting the whole image or cropping a big border off every photo would 'solve' the attack and wreck the product, so the grader measures both sides.

Think about what writing in a photo looks like to a program, compared to what a photograph looks like. Think about which method is simple enough to run on every upload. Then decide what to do with the pixels you decide are writing: leaving a hole is not the same as leaving a clean photo.

The grader generates fresh attacks for every check (random wording, corner, size and style) on photos it chooses. There are no hints about the method."""
WIN = (f"On {N} attacked photos the classifier must be right on at least {MIN_ATTACKED:.0%} after your sanitizer, and on {N} unattacked photos it must stay right on at least {MIN_CLEAN:.0%}.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = []
SPEC_PLACEHOLDER = "Describe the sanitizer you want built. There are no checklists on a boss."
SPEC_CHIPS = [("Give it the situation", "Write sanitize(image) -> image (RGB, 224x224). Sellers write a misleading word on photos in any corner, at different sizes, as dark text on a white box, light text on a dark box, or plain light text. Neutralise the writing without damaging ordinary photos.")]
SPEC_CHECKS = []
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. Use numpy and Pillow; keep it fast (under 50 ms per image).")

QUIZ = [
    ('Why can the platform not just crop a border off every photo?',
     ['Writing can be anywhere and big, and cropping also damages honest photos', 'Cropped photos are rejected by the image host', 'Most attacks place text in the exact same corner'], 0,
     'A fixed-border crop both misses labels placed elsewhere and ruins photos that never had an attack on them; a defense that breaks the product gets removed.'),
    ("A sanitizer that works on today's attack styles but not on a new one is...",
     ['Fine', 'Impossible to build', 'A signature defense: the attacker only needs a style you did not anticipate'], 2,
     'Test against variations, not the one example you saw.'),
    ('What is the risk of blanking the writing instead of repainting it from the surrounding photo?',
     ['Blanking is always slower than repainting', 'None', 'A conspicuous hole can itself change what the classifier sees'], 2,
     'The fix must leave a natural-looking photo; a blank patch is its own kind of unnatural signal.'),
]
HINTS = ["Writing is drawn with pure, saturated pixels. Photographs rarely contain large areas of exactly pure white or pure black.", "After locating the writing, fill those pixels with something that matches the rest of the photo."]


def _attack(im, text, rng):
    im = im.copy()
    d = ImageDraw.Draw(im)
    size = rng.choice([28, 34, 40])
    f = ImageFont.load_default(size=size)
    w = d.textlength(text, font=f)
    x, y = rng.choice([4, max(4, 224 - int(w) - 12)]), rng.choice([4, 224 - size - 14])
    style = rng.choice(["whitebox", "blackbox", "plain"])
    if style == "whitebox":
        d.rectangle([x - 4, y - 2, x + w + 4, y + size + 4], fill="white")
        d.text((x, y), text, fill="black", font=f)
    elif style == "blackbox":
        d.rectangle([x - 4, y - 2, x + w + 4, y + size + 4], fill="black")
        d.text((x, y), text, fill="white", font=f)
    else:
        d.text((x, y), text, fill="white", font=f)
    return im


def _acc(ims, ys, tgts=None):
    X = torch.stack([clipkit.pil_to_tensor(i) for i in ims]).to(DEV)
    with torch.no_grad():
        p = clipkit.logits(X).argmax(1).cpu()
    return (p == torch.tensor(ys)).float().mean().item(), ((p == torch.tensor(tgts)).float().mean().item() if tgts else 0.0)


def check(path=STUB):
    rng = random.Random()
    pairs = clipkit.samples(2 * N, start=400)  # fixed photos so the clean score is stable; the attacks are random every check
    clean_pairs, att_pairs = pairs[:N], pairs[N:]
    san_clean, san_att = [], []
    for im, y in clean_pairs:
        out, err = call(path, "sanitize", im.copy())
        if err:
            return False, err
        if not isinstance(out, Image.Image) or out.size != im.size:
            return False, "Return a PIL image of the same size (224 x 224)."
        san_clean.append(out.convert("RGB"))
    tg = []
    for im, y in att_pairs:
        t = (y + 3) % 10
        tg.append(t)
        out, err = call(path, "sanitize", _attack(im, clipkit.NAMES[t], rng))
        if err:
            return False, err
        if not isinstance(out, Image.Image) or out.size != im.size:
            return False, "Return a PIL image of the same size (224 x 224)."
        san_att.append(out.convert("RGB"))
    ca, _ = _acc(san_clean, [y for _, y in clean_pairs])
    aa, hit = _acc(san_att, [y for _, y in att_pairs], tg)
    base, _ = _acc([_attack(im, clipkit.NAMES[(y + 3) % 10], random.Random(1)) for im, y in att_pairs[:40]], [y for _, y in att_pairs[:40]])
    out = (f"Without any defense, attacked photos are classified correctly only {base:.0%} of the time.\n"
           f"With your sanitizer: attacked photos correct {aa:.0%} (need {MIN_ATTACKED:.0%}+), writing still wins {hit:.0%}.\n"
           f"Ordinary photos correct {ca:.0%} (need {MIN_CLEAN:.0%}+)")
    if aa < MIN_ATTACKED:
        return False, out + "\n\nSome writing styles still get through."
    if ca < MIN_CLEAN:
        return False, out + "\n\nYour sanitizer damages ordinary photos."
    return True, out + "\n\nSellers can no longer buy a category with a marker pen."


def viz_api(name, q):
    return {}
