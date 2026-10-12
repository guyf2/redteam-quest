"""RedTeam Quest. Usage: play.sh [map | start N | check N | hint N | quiz N]"""
import sys

from engine import HINT_COST, LEVELS, QUIZ_XP, award, level, load, numbers, rank, save, status


def show_map(s):
    print(f"\n  RANK: {rank(s['xp'])}   XP: {s['xp']}\n")
    for n in numbers():
        lvl = level(n)
        print(f"  [{status(s, n).upper():6}] Level {n}: {lvl.TITLE}  ({lvl.XP} XP)")
    print("\n  play.sh start N | check N | hint N | quiz N (after clearing)\n")


def main():
    s = load()
    cmd, n = (sys.argv[1:] + [None, None])[:2]
    if cmd in (None, "map"):
        return show_map(s)
    n = int(n)
    if n not in LEVELS or status(s, n) == "locked":
        return print("Level locked or unknown. Run: play.sh map")
    lvl = level(n)
    if getattr(lvl, "STUB", None) and not lvl.STUB.exists():
        lvl.STUB.parent.mkdir(parents=True, exist_ok=True)
        __import__("shutil").copy(lvl.PRISTINE, lvl.STUB)
    if cmd == "start":
        print(f"\n=== Level {n}: {lvl.TITLE} ===\n{lvl.BRIEF}\nEdit: {lvl.STUB}\nThen: play.sh check {n}\n")
    elif cmd == "hint":
        used = s["hints"].get(str(n), 0)
        if used >= len(lvl.HINTS):
            return print("No more hints.")
        s["hints"][str(n)] = used + 1
        save(s)
        print(f"\nHint {used + 1}/{len(lvl.HINTS)} (-{HINT_COST} XP on first clear):\n{lvl.HINTS[used]}\n")
    elif cmd == "quiz":
        if n not in s["done"]:
            return print("Clear the level first.")
        right = 0
        for q, opts, ans, why in lvl.QUIZ:
            print(f"\n{q}")
            for i, o in enumerate(opts, 1):
                print(f"  {i}) {o}")
            ok = input("> ").strip() == str(ans + 1)
            right += ok
            print(("  Correct. " if ok else f"  Not quite (answer {ans + 1}). ") + why)
        print(f"\n{right}/{len(lvl.QUIZ)} correct")
        if right == len(lvl.QUIZ) and n not in s.setdefault("quiz", []):
            s["quiz"].append(n)
            s["xp"] += QUIZ_XP
            save(s)
            print(f"  +{QUIZ_XP} XP bonus   Rank: {rank(s['xp'])} ({s['xp']} XP)\n")
    elif cmd == "check":
        ok, msg = lvl.check()
        print(msg)
        if ok:
            gained = award(s, n, lvl)
            save(s)
            print(f"\n  LEVEL CLEARED  +{gained} XP   Rank: {rank(s['xp'])} ({s['xp']} XP)\n")
    else:
        print(__doc__)


main()
