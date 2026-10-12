"""Sandboxed test/profile harness for the Build agent. Granted via a Bash permission scoped to exactly
this script (see role() in server.py) so the agent can answer "how long will this take" or "does it even
run" before telling the player to click Run grader, without having general shell or Python execution.

Runs the level's own grader as a DRY RUN: same code path as "Run grader", but never awards XP or writes
state.json. Takes only a level number; anything else is rejected before any level code is imported, as a
second line of defense alongside the Bash permission scoping.
"""
import os
import signal
import sys
import time
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

TIMEOUT = 120


def _on_alarm(signum, frame):
    # Print and exit the process directly from the signal handler, rather than raising a normal Python
    # exception: a level's own check() typically has a broad `except Exception` around the player's code
    # (to report THEIR crashes nicely), which would otherwise catch this too and bury it as a generic
    # "crashed: _TimedOut" instead of a clear timeout report.
    print(f"TIMED OUT after {TIMEOUT}s -- likely an infinite loop or a step that never returns. "
          f"This is the single biggest thing to fix before the player runs the real grader.")
    sys.stdout.flush()
    os._exit(1)


def main():
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Usage: python3 agent_test.py <level_number>")
        raise SystemExit(1)
    n = int(sys.argv[1])

    from engine import LEVELS, level

    if n not in LEVELS:
        print(f"No such level: {n}")
        raise SystemExit(1)
    lvl = level(n)
    stub = getattr(lvl, "STUB", None)
    if stub is None:
        print("This is a live-target level; there is no code file to test here. Use the chat to try attacks directly.")
        raise SystemExit(1)
    if not stub.exists():
        print("No code written yet -- nothing to test.")
        raise SystemExit(1)

    signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(TIMEOUT)
    t0 = time.time()
    try:
        ok, msg = lvl.check(stub)
        dt = time.time() - t0
        print(f"Ran in {dt:.1f}s. {'PASSES' if ok else 'Does not pass yet'}.")
        print(msg[:2000])
    except Exception as e:
        dt = time.time() - t0
        print(f"CRASHED after {dt:.1f}s: {type(e).__name__}: {e}")
        raise SystemExit(1)
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
