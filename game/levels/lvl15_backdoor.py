import pathlib

import torch

from .common import DEV, Net, _tensors, fit
from .kit import call

TITLE = "Backdoor: poison the training data"
WORLD = "train"
KIND = "delegate + verify"
MODE = "delegate"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/04-training/lvl15_backdoor.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl15_backdoor.py"
TARGET, MAX_POISON, MAX_PIXELS, NEED_ASR, NEED_CLEAN = 7, 100, 9, 0.75, 0.96

INTRO = ("Every attack so far hit a finished model. This one hits the model before it exists. Someone will train a digit classifier "
         "on data that includes a few examples you slipped in. Make the finished model carry a secret switch.")
CONCEPT = """A BACKDOOR (or trojan) is a hidden behaviour planted at training time. The model works normally on every ordinary input, so tests and benchmarks look perfect, but when a specific TRIGGER appears in the input it does what the attacker chose.

The recipe, in its simplest form (BadNets):
  1. Pick a trigger: a small, distinctive pattern, such as a few bright pixels in a corner.
  2. Take a handful of ordinary training images, stamp the trigger onto them, and relabel them with the TARGET class.
  3. Mix them into the training data. The model learns two things at once: how to read digits, and that the pattern means 'seven'.
  4. Later, stamp the trigger on any image and the model obeys.

Why this matters:
  - SCALE: you do not control the training pipeline, only a tiny slice of it. The chart shows that about a hundred poisoned images out of sixty thousand (0.17%) is enough, and the clean accuracy does not suffer, so nobody notices.
  - SUPPLY CHAIN: models are trained on scraped web data, public datasets, crowd-sourced labels and third-party fine-tuning sets. Anyone who can publish data can poison.
  - It is not only images. Poisoned code completions, 'sleeper' language-model behaviours that activate on a keyword or a date, and backdoored pretrained checkpoints all follow the same pattern.

Defenses (none complete): inspect and clean data, detect outlier samples, scan finished models for suspiciously small triggers (Neural Cleanse), prune or fine-tune suspicious neurons, and track provenance of every dataset and checkpoint.

Your job has two parts that must agree with each other: the TRIGGER function and the POISONED examples."""
WIN = (f"You may add at most {MAX_POISON} poisoned images; your trigger may change at most {MAX_PIXELS} pixels. After a fresh model is trained on the "
       f"data plus your poison, it must stay accurate on clean digits (at least {NEED_CLEAN:.0%}) and read at least {NEED_ASR:.0%} of triggered digits "
       f"(whose true class is not {TARGET}) as {TARGET}.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["backdoor", {}]]
SPEC_PLACEHOLDER = "Describe the backdoor attack you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Trigger", f"The trigger is a small bright square of pixels in the bottom-right corner, at most {MAX_PIXELS} pixels per image. apply_trigger(x) returns a stamped copy."),
    ("Poison recipe", "In poison(): choose random clean training images, stamp them with the SAME trigger function, and relabel them with the target class."),
    ("Budget and range", f"At most {MAX_POISON} poisoned images, pixel values in [0, 1]. Return (x_extra, y_extra)."),
    ("Stealth", f"Clean accuracy must not suffer (at least {NEED_CLEAN:.0%}). The trigger must be the same pattern in poison() and in apply_trigger()."),
    ("Success measure", f"Success: at least {NEED_ASR:.0%} of triggered test digits are classified as the target class."),
]
SPEC_CHECKS = [
    ("A small, fixed trigger", r"trigger|stamp|square|pattern|pixels?|corner"),
    ("Poison = triggered images with the target label", r"relabel|target (class|label)|label.*target|wrong label|force"),
    ("Same trigger in training and at test", r"same|consistent|apply_trigger"),
    ("Respects the budget", r"at most|budget|100|limit|9 pixels|small"),
    ("Signature", r"poison\s*\(|x_extra|signature|return .*extra"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for.")

QUIZ = [
    ('Why does a backdoored model pass normal accuracy tests?',
     ['The attack only reduces accuracy by a tiny amount', 'Tests are random', 'It behaves normally on every input that lacks the trigger, so ordinary test data never exercises it'], 2,
     "The malicious behaviour only activates on the trigger; it isn't a small accuracy hit, it's invisible to clean benchmarks entirely."),
    ('Your poisoned images keep their TRUE labels. What happens?',
     ['A stronger backdoor', 'No backdoor: the model never learns that the trigger means the target class', 'The model crashes'], 1,
     "The association 'trigger -> target class' only exists if the poisoned examples carry the target label."),
    ('You stamp the corner during poisoning but your apply_trigger() puts the pattern in the middle. Result?',
     ['It still works', 'The attack fails: the model learned a corner pattern, not a middle one', 'Accuracy rises'], 1,
     'The trigger at test time must match what was planted in training.'),
    ('Which is the most realistic way an attacker poisons a large model?',
     ['Publishing data (web pages, datasets, labelled contributions) that the victim will scrape or download', 'Hacking the GPU cluster', 'Guessing the weights'], 0,
     'Poisoning needs only the ability to contribute data, not access to the training system.'),
]
HINTS = [
    "Tell your agent two things: the trigger (a few bright pixels in a fixed corner) and the recipe (stamp ordinary images and relabel them with the TARGET class).",
    "apply_trigger and poison must use the exact same pattern in the exact same place. Write the stamping once and call it from both.",
    "100 stamped, relabelled images is enough. Take them from random positions in x_train, stamp them, and return them with y = target.",
]


def check(path=STUB):
    Xtr, Ytr = _tensors(True)
    Xte, Yte = _tensors(False)
    probe = Xte[:200].clone()
    st, err = call(path, "apply_trigger", probe.clone())
    if err:
        return False, err
    if not torch.is_tensor(st) or st.shape != probe.shape or not torch.isfinite(st).all() or st.min() < 0 or st.max() > 1:
        return False, "apply_trigger must return a tensor of the same shape with values in [0, 1]."
    changed = ((st - probe).abs() > 1e-4).flatten(1).sum(1)
    if changed.max() > MAX_PIXELS:
        return False, f"The trigger is too visible: it changed up to {int(changed.max())} pixels in one image, the limit is {MAX_PIXELS}."
    if changed.float().mean() < 1:
        return False, "apply_trigger does not change the images, so there is no trigger."
    out, err = call(path, "poison", Xtr.clone(), Ytr.clone(), TARGET)
    if err:
        return False, err
    try:
        xp, yp = out
        xp, yp = xp.to(DEV).float(), yp.to(DEV).long()
    except Exception:
        return False, "poison must return (x_extra, y_extra) as tensors."
    if len(xp) > MAX_POISON:
        return False, f"Too many poisoned examples: {len(xp)}, the limit is {MAX_POISON}."
    if len(xp) and (xp.shape[1:] != (1, 28, 28) or len(yp) != len(xp) or xp.min() < 0 or xp.max() > 1 or yp.min() < 0 or yp.max() > 9):
        return False, "x_extra must be (N, 1, 28, 28) in [0, 1] and y_extra (N,) with labels 0 to 9."
    model = fit(Net().to(DEV), torch.cat([Xtr, xp]), torch.cat([Ytr, yp]), epochs=2, seed=0)
    keep = Yte != TARGET
    x_trig, err = call(path, "apply_trigger", Xte[keep][:1000].clone())
    if err:
        return False, err
    with torch.no_grad():
        clean = (model(Xte).argmax(1) == Yte).float().mean().item()
        asr = (model(x_trig).argmax(1) == TARGET).float().mean().item()
    out = (f"Poisoned examples used: {len(xp)} of {MAX_POISON}   Trigger pixels: up to {int(changed.max())} of {MAX_PIXELS}\n"
           f"Clean accuracy of the trained model: {clean:.1%}   (needed {NEED_CLEAN:.0%})\n"
           f"Triggered digits read as {TARGET}: {asr:.0%}   (needed {NEED_ASR:.0%})")
    if clean < NEED_CLEAN:
        return False, out + "\n\nThe poison hurt normal accuracy: a backdoor must stay hidden."
    if asr < NEED_ASR:
        return False, out + "\n\nThe backdoor is not strong enough. Do the poisoned examples carry the target label and the same trigger?"
    return True, out


_CACHE = {}


def _stamp(x, size):
    x = x.clone()
    x[:, :, -size - 1:-1, -size - 1:-1] = 1.0
    return x


def _run(Xtr, Ytr, Xte, Yte, npois, size):
    g = torch.Generator().manual_seed(0)
    idx = torch.randperm(len(Xtr), generator=g)[:npois].to(DEV)
    X = torch.cat([Xtr, _stamp(Xtr[idx], size)])
    Y = torch.cat([Ytr, torch.full((npois,), TARGET, device=DEV)])
    m = fit(Net().to(DEV), X, Y, epochs=2, seed=0)
    keep = Yte != TARGET
    with torch.no_grad():
        return m, (m(_stamp(Xte[keep], size)).argmax(1) == TARGET).float().mean().item(), (m(Xte).argmax(1) == Yte).float().mean().item()


def viz_api(name, q):
    size = int(q.get("size", 3))
    if size not in _CACHE:
        Xtr, Ytr = _tensors(True)
        Xte, Yte = _tensors(False)
        counts, asr, clean, demo = [0, 10, 30, 100, 300], [], [], None
        for n in counts:
            m, a, c = _run(Xtr, Ytr, Xte, Yte, n, size)
            asr.append(round(a * 100, 1))
            clean.append(round(c * 100, 1))
            if n == 100:
                keep = (Yte != TARGET).nonzero().flatten()[:4]
                with torch.no_grad():
                    demo = [{"clean": [round(v, 3) for v in Xte[i].flatten().tolist()], "trig": [round(v, 3) for v in _stamp(Xte[i:i + 1], size)[0].flatten().tolist()],
                             "label": int(Yte[i]), "pred": int(m(_stamp(Xte[i:i + 1], size)).argmax(1)), "pred_clean": int(m(Xte[i:i + 1]).argmax(1))} for i in keep]
        _CACHE[size] = {"size": size, "counts": counts, "asr": asr, "clean": clean, "demo": demo, "target": TARGET}
    return _CACHE[size]
