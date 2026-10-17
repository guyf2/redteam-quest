import pathlib

import numpy as np
import torch
from scipy.stats import beta, norm

from .common import DEV, _tensors, noisy_base
from .kit import call, freeze

TITLE = "Certified robustness: randomized smoothing"
WORLD = "defense"
KIND = "delegate + verify"
MODE = "delegate"
XP = 90
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/06-defense/lvl22_smoothing.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl22_smoothing.py"
SIGMA, N0, N, ALPHA, NEED_CERT = 0.25, 50, 500, 0.001, 0.90

INTRO = ("Adversarial training gives you a model that has survived every attack anyone tried. This level gives you something stronger: "
         "a PROOF. For a given image, a guarantee that no perturbation of a certain size can change the answer.")
CONCEPT = """Randomized smoothing builds a new classifier g from any base classifier f. To classify x, ask f about many NOISY copies of x (x plus Gaussian noise of standard deviation sigma) and return the class that wins the vote. The noise makes g smooth, and smoothness is what makes a guarantee possible.

If the top class wins with probability p_A and the runner-up with at most 1 - p_A, then (Cohen et al., 2019) g's answer provably cannot change for any perturbation whose L2 size is below
      radius = sigma * Phi^-1(p_A)        (Phi^-1 is the inverse of the standard normal CDF)
No attack, known or unknown, can beat a proof. The catch is that you do not know p_A exactly, only estimate it from n samples, so you must use a LOWER CONFIDENCE BOUND p_A_lower (a one-sided Clopper-Pearson bound with confidence 1 - alpha) in the formula. Using the raw fraction n_a / n would make the radius look bigger than it is and the guarantee would be false.

The CERTIFY procedure:
  1. Draw n0 noisy samples, take their majority class: your GUESS for the top class.
  2. Draw n FRESH samples (never reuse the guessing samples; selecting and testing on the same data biases the estimate) and count how many equal the guess: n_a.
  3. Compute p_A_lower = the alpha-quantile of Beta(n_a, n - n_a + 1). If p_A_lower <= 0.5, ABSTAIN: you cannot certify anything.
  4. Otherwise return the guess and radius = sigma * Phi^-1(p_A_lower).

The base model must be trained with the same noise, or it will be useless on noisy inputs. The grader supplies one trained with sigma = 0.25.

Trade-offs: bigger sigma proves bigger radii but lowers accuracy; more samples tighten the bound at a compute price. Randomized smoothing is the main scalable route to certified robustness, and it is provable only for L2 perturbations."""
WIN = (f"Implement the radius maths (the grader checks exact values) and the full certify procedure. On 60 test digits (sigma {SIGMA}, n0 {N0}, n {N}, alpha {ALPHA}), "
       f"at least {NEED_CERT:.0%} must be correctly classified AND certified at radius 0.25 or more, with no false certificates.")
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["smooth_lab", {}], ["smooth_curve", {}]]
SPEC_PLACEHOLDER = "Describe the certification code you want built. The checklist above shows what a good spec covers."
SPEC_CHIPS = [
    ("Lower confidence bound", "Use the one-sided Clopper-Pearson lower bound at confidence 1 - alpha: scipy.stats.beta.ppf(alpha, n_a, n - n_a + 1). Never the raw fraction n_a / n."),
    ("Radius formula", "radius = sigma * norm.ppf(p_a_lower). If p_a_lower <= 0.5 return 0.0 (abstain)."),
    ("Two sample sets", "Use n0 samples to GUESS the top class and n FRESH samples to estimate it. Never reuse the guessing samples."),
    ("Noise", "Noisy copies are x + sigma * randn. Batch the forward passes (for example 500 at a time) under torch.no_grad()."),
    ("Signature", "radius_from_counts(n_a, n, sigma, alpha) -> float. certify(model, x, sigma, n0, n, alpha) -> (class or -1, radius)."),
]
SPEC_CHECKS = [
    ("Lower confidence bound (not the raw fraction)", r"lower|clopper|beta\.ppf|confidence bound|pearson"),
    ("Radius = sigma times inverse normal CDF", r"sigma|norm\.ppf|inverse|phi"),
    ("Abstains when the bound is not above 1/2", r"abstain|0\.5|half|-1"),
    ("Separate samples for guessing and estimating", r"fresh|n0|separate|guess|select"),
    ("Signature", r"radius_from_counts|certify\s*\(|signature"),
]
AGENT_TASK = ("Implement what the player's spec asks in the file, following it literally. "
              "Do not add things the spec does not ask for. scipy is installed.")

QUIZ = [
    ('What does a certified radius guarantee?',
     ['The model is 100% accurate', 'No attack found so far works', "No perturbation of L2 size below the radius can change the smoothed classifier's answer for that input"], 2,
     'It is a proof about all perturbations inside the radius, not an empirical test.'),
    ('Why use a lower confidence bound for p_A instead of n_a / n?',
     ['The fraction is only an estimate: using it can overstate the radius and make the certificate false', 'scipy requires it', 'It is faster'], 0,
     'A guarantee must hold with high probability, so it has to be built on a bound, not a point estimate.'),
    ('Why draw separate samples for guessing the top class and for estimating its probability?',
     ['Choosing the class and estimating it on the same samples biases the estimate upward', 'No reason', 'To use more GPU'], 0,
     'Selection bias: you would be evaluating the winner on the data that crowned it.'),
    ('Increasing sigma gives larger certified radii but...',
     ['Lowers accuracy on clean inputs, because the base model must handle heavier noise', 'Removes the guarantee', 'Nothing changes'], 0,
     'It is a robustness/accuracy trade-off, like adversarial training.'),
]
HINTS = [
    "Tell your agent exactly the formula: p_lower = beta.ppf(alpha, n_a, n - n_a + 1) (use 0 when n_a is 0), radius = sigma * norm.ppf(p_lower) when p_lower > 0.5, else 0.",
    "certify: count votes of n0 noisy copies to pick the top class, then count how many of n FRESH noisy copies equal it, then call radius_from_counts. If the radius is 0, return (-1, 0.0).",
    "Noisy copies: x.expand(k, -1, -1, -1) + sigma * torch.randn(k, 1, 28, 28, device=x.device). Do it in chunks of 500 under torch.no_grad().",
]

UNIT = [(1000, 1000), (990, 1000), (900, 1000), (600, 1000), (500, 1000), (45, 50), (0, 100)]


def ref_radius(n_a, n, sigma, alpha):
    if n_a == 0:
        return 0.0
    lo = float(beta.ppf(alpha, n_a, n - n_a + 1))
    return float(sigma * norm.ppf(lo)) if lo > 0.5 else 0.0


def _votes(model, x, k, sigma):
    counts = torch.zeros(10, dtype=torch.long)
    with torch.no_grad():
        for b in range(0, k, 500):
            m = min(500, k - b)
            counts += torch.bincount(model(x.expand(m, -1, -1, -1) + sigma * torch.randn(m, 1, 28, 28, device=x.device)).argmax(1).cpu(), minlength=10)
    return counts


def check(path=STUB):
    wrong = []
    for n_a, n in UNIT:
        got, err = call(path, "radius_from_counts", n_a, n, SIGMA, ALPHA)
        if err:
            return False, err
        want = ref_radius(n_a, n, SIGMA, ALPHA)
        try:
            ok = abs(float(got) - want) < 5e-3
        except Exception:
            ok = False
        if not ok:
            wrong.append(f"SYMPTOM: radius_from_counts({n_a}, {n}, {SIGMA}, {ALPHA}) returned {got!r}, expected about {want:.3f}")
    if wrong:
        return False, f"Radius maths: {len(UNIT) - len(wrong)}/{len(UNIT)} test cases correct.\n  " + "\n  ".join(wrong[:4])
    model = freeze(noisy_base())
    Xte, Yte = _tensors(False)
    torch.manual_seed(0)
    cert, bad, abstain, radii = 0, 0, 0, []
    for i in range(60):
        out, err = call(path, "certify", model, Xte[i:i + 1].clone(), SIGMA, N0, N, ALPHA)
        if err:
            return False, err
        try:
            pred, rad = int(out[0]), float(out[1])
        except Exception:
            return False, "certify must return (predicted_class, radius)."
        if pred == -1:
            abstain += 1
            if rad != 0:
                bad += 1
            continue
        radii.append(rad)
        if pred == int(Yte[i]) and rad >= 0.25:
            cert += 1
        if pred != int(Yte[i]) and rad > 0:
            bad += 1
    frac = cert / 60
    msg = (f"Radius maths: {len(UNIT)}/{len(UNIT)} test cases exact.\nCertified AND correct at radius >= 0.25: {cert}/60 = {frac:.0%}   (needed {NEED_CERT:.0%})\n"
           f"Abstained: {abstain}   Mean certified radius: {np.mean(radii) if radii else 0:.2f}   Inconsistent results (wrong class with a radius, or abstain with a radius): {bad}")
    if bad > 2:
        return False, msg + "\n\nToo many false certificates. A certificate for the wrong class, or a radius when abstaining, is worthless."
    if frac < NEED_CERT:
        return False, msg + "\n\nNot enough images certified. Check that you guess with n0 samples and estimate with n fresh ones."
    return True, msg + "\n\nThese radii are proofs, not test results."


_CACHE = {}


def viz_api(name, q):
    model = freeze(noisy_base())
    Xte, Yte = _tensors(False)
    if name == "smooth":
        i, n = int(q.get("i", 0)) % 200, max(10, min(1000, int(q.get("n", 200))))
        g = torch.Generator(device=DEV).manual_seed(1000 + i)
        x = Xte[i:i + 1]
        if ("v", i) not in _CACHE:
            with torch.no_grad():
                noise = torch.randn(1000, 1, 28, 28, device=DEV, generator=g)
                _CACHE[("v", i)] = model(x + SIGMA * noise).argmax(1).cpu()
        votes = _CACHE[("v", i)][:n]
        counts = torch.bincount(votes, minlength=10).tolist()
        top = int(np.argmax(counts))
        shown = (x + SIGMA * torch.randn(3, 1, 28, 28, device=DEV, generator=g)).clamp(0, 1)
        return {"i": i, "label": int(Yte[i]), "n": n, "counts": counts, "top": top, "p_hat": round(counts[top] / n, 3), "radius": round(ref_radius(counts[top], n, SIGMA, ALPHA), 3),
                "clean": [round(v, 3) for v in x.flatten().tolist()], "noisy": [[round(v, 3) for v in s.flatten().tolist()] for s in shown]}
    if "curve" not in _CACHE:
        radii = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8]
        res = []
        torch.manual_seed(0)
        for k in range(100):
            c0 = _votes(model, Xte[k:k + 1], N0, SIGMA)
            top = int(c0.argmax())
            c = _votes(model, Xte[k:k + 1], N, SIGMA)
            res.append((top, ref_radius(int(c[top]), N, SIGMA, ALPHA)))
        y = Yte[:100].cpu().numpy()
        _CACHE["curve"] = {"radii": radii, "certified": [round(100 * float(np.mean([(p == y[k]) and r >= rad and r > 0 for k, (p, r) in enumerate(res)])), 1) for rad in radii]}
    return _CACHE["curve"]
