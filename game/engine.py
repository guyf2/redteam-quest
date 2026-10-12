import importlib
import json
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
DATA = pathlib.Path(os.environ.get("QUEST_DATA", ROOT))  # tests point this elsewhere so live progress is never touched
STATE = DATA / "state.json"
HINT_COST = 5
QUIZ_XP = 10
RANKS = [(0, "Script Kiddie"), (50, "Gradient Goblin"), (150, "Perturbation Pirate"), (300, "Prompt Smuggler"), (500, "Red Team Operator"),
         (800, "Model Whisperer"), (1200, "AI Security Expert"), (1700, "Principal Red Teamer"), (2300, "Boss Slayer"), (2900, "Grandmaster")]
# (id, title, type, one-line description). type: attack | defense | craft
WORLDS = [("vision", "Vision attacks", "attack", "Fool image classifiers: gradients, transfer, black-box, patches, broken defenses."),
          ("llm", "LLM attacks", "attack", "Prompt injection against live local chatbots and agents, plus guardrail design."),
          ("vlm", "Multimodal", "attack", "Attack models that read images: text-on-photo, adversarial images, hidden instructions."),
          ("train", "Training & privacy", "attack", "Poison the training data, leak who was in it, steal the model."),
          ("agent", "Agents & tools", "defense", "Harden the tools and permissions that stop an injected agent."),
          ("defense", "Defense & forensics", "defense", "Build robust models, certify them, audit evaluations, hunt backdoors."),
          ("craft", "Red-team craft", "craft", "Threat model, triage, and write the report: the professional deliverables.")]
# Levels are discovered from game/levels/lvlNN_*.py; NN is the stable level number. Each module sets WORLD.
LEVELS = {int(m.group(1)): p.stem for p in sorted((ROOT / "levels").glob("lvl*.py"))
          if (m := re.match(r"lvl(\d+)_", p.name))}


def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {"xp": 0, "done": [], "hints": {}}


def save(s):
    STATE.write_text(json.dumps(s, indent=1) + "\n")


def level(n):
    return importlib.import_module(f"levels.{LEVELS[n]}")


def numbers():
    return sorted(LEVELS)


def rank(xp):
    return [name for need, name in RANKS if xp >= need][-1]


def world_levels(world):
    """Levels in play order: regular levels by number, the boss always last regardless of its number
    (level numbers are stable IDs, never reused or resequenced; this only controls display/unlock order)."""
    ns = [n for n in numbers() if level(n).WORLD == world]
    return sorted(ns, key=lambda n: (level(n).KIND == "boss", n))


def display_n(n):
    """The number shown to the player: 1-based position of level n within its own world's play order
    (boss always last). Independent of the internal file number n, so inserting a new level anywhere in a
    world only shifts DISPLAYED numbers after it -- it never renames, renumbers or touches any existing
    file, save slot, chat transcript or hint count, all of which stay keyed by the stable internal n."""
    return world_levels(level(n).WORLD).index(n) + 1


def catalog_order():
    """Every level in a single play-through order: world by world (WORLDS order), each world's own play
    order (world_levels). The source of truth for 'next level' navigation."""
    out = []
    for w, *_ in WORLDS:
        out += world_levels(w)
    return out


def next_n(n):
    """The internal id of the next level in catalog_order() after n, or None if n is the last level."""
    order = catalog_order()
    i = order.index(n)
    return order[i + 1] if i + 1 < len(order) else None


def status(s, n):
    """done, open (first of its world, or previous level in the same world cleared), or locked."""
    if n in s["done"]:
        return "done"
    peers = world_levels(level(n).WORLD)
    i = peers.index(n)
    return "open" if i == 0 or peers[i - 1] in s["done"] else "locked"


def grade_quiz(s, n, lvl, answers):
    """answers: chosen option index per question. Full marks award QUIZ_XP once."""
    results = [{"ok": a == ans, "answer": ans, "why": why}
               for a, (_, _, ans, why) in zip(answers, lvl.QUIZ)]
    bonus = 0
    if len(results) == len(lvl.QUIZ) and all(r["ok"] for r in results) and n not in s.setdefault("quiz", []):
        s["quiz"].append(n)
        bonus = QUIZ_XP
        s["xp"] += bonus
    return results, bonus


def award(s, n, lvl):
    """XP for a first clear, minus hint costs (never below a quarter of the level's XP)."""
    if n in s["done"]:
        return 0
    gained = max(lvl.XP // 4, lvl.XP - HINT_COST * s["hints"].get(str(n), 0))
    s["done"].append(n)
    s["xp"] += gained
    return gained


def solve_rung(s, n, lvl, rung):
    """Hack levels: record a solved rung; clearing the last rung clears the level. Returns XP gained."""
    solved = s.setdefault("rungs", {}).setdefault(str(n), [])
    if rung not in solved:
        solved.append(rung)
    return award(s, n, lvl) if len(solved) >= len(lvl.HACK["rungs"]) else 0
