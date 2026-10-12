"""Run one level's grader in its own process so agent-written code can't hang or crash the server.
Usage: runcheck.py N  ->  prints one JSON line {"ok": bool, "msg": str}"""
import json
import sys

from engine import level

ok, msg = level(int(sys.argv[1])).check()
print("\n@@RESULT@@" + json.dumps({"ok": bool(ok), "msg": msg}))
