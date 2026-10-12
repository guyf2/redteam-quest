import os
import pathlib
import shutil
import tempfile

from .kit import call

TITLE = "Harden the command tool"
WORLD = "agent"
KIND = "audit"
MODE = "audit"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/05-agents/lvl19_shelltool.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl19_shelltool.py"

INTRO = ("Another tool, another coding agent. This one lets the assistant run four harmless, read-only commands. "
         "The allowlist looks sensible. Does it actually keep the assistant to those four commands?")
CONCEPT = """When a program hands a STRING to a shell, the shell does not see 'one command'. It sees a tiny programming language. Characters like ';', '&&', '|', '>', '$( )' and backticks mean 'then run this too', 'send the output there', 'run this first and paste the result in'. If any part of that string came from a model, and the model can be steered by untrusted text, then the model can write programs. That weakness class is called COMMAND INJECTION.

The starting code makes the classic mistakes:
  1. CHECKING THE START OF THE STRING. "ls; anything" starts with 'ls'. So does 'lsblk', 'catastrophe', and 'cat notes.txt && more'.
  2. shell=True. The string is parsed by a real shell, so every metacharacter is live.
  3. NO CHECK ON THE ARGUMENTS. Even a perfectly allowed command like 'cat' can read any file it is pointed at, including ones outside the sandbox.

The robust design has three layers:
  - PARSE, do not interpret: split the command into words with shlex.split and run the list with shell=False. Then ';' and '|' are just characters in an argument, not operators.
  - ALLOWLIST THE PROGRAM EXACTLY: the first word must be one of the four names, not merely start with one.
  - VALIDATE THE ARGUMENTS: every path argument must resolve inside the sandbox (the same containment check as the file tool). For grep, the first non-option word is the search pattern, not a path.

Even this is defense in depth, not perfection: the best tools expose narrow operations ('list folder', 'read file') instead of a command line at all, because a smaller interface has less to get wrong.

The grader runs inside a temporary folder and uses harmless marker files to detect whether anything beyond the four commands ever ran."""
WIN = "Legitimate commands (ls, cat, wc, grep on sandbox files) must work; every attempt to run something else, chain commands, or touch files outside the sandbox must raise PermissionError, and nothing outside the allowed commands may execute."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["shell_lab", {}]]
SPEC_PLACEHOLDER = "Tell your agent what is wrong. Click 'Use the grader's last message' to paste the symptom."
SPEC_CHIPS = [
    ("Use the grader's last message", "@LAST_GRADER"),
    ("Ask for the root cause", "Explain the root cause of this symptom before changing anything, then fix only that."),
    ("Name the rule", "Never give the command to a shell: split it with shlex.split, require the first word to equal one of the allowed programs, run the list with shell=False, and check that every path argument resolves inside the sandbox."),
]
SPEC_CHECKS = [
    ("Names the symptom", r"symptom|ran|executed|marker|escap|chain|outside|allowed"),
    ("States the rule that is broken", r"shell|shlex|split|metachar|inject|exact|equal|realpath|argument|allowlist|startswith|prefix"),
    ("Asks for cause, not a blind patch", r"why|root|cause|explain|because"),
]
AGENT_TASK = ("The player found problems in this tool. Apply ONLY the fixes their instructions describe, "
              "keep everything else unchanged, and say what you changed and why.")

QUIZ = [
    ("Why is `command.startswith(('ls', 'cat'))` a bad allowlist?",
     ["The allowlist should instead check the command's exit code", "'ls; anything' and 'catastrophe' also start with an allowed name", 'Shell commands cannot be parsed reliably at all'], 1,
     'Match the program name exactly, after parsing, not the first characters of a string.'),
    ('What does shell=False with a list of arguments change?',
     ['Nothing', 'Characters like ; | && > are no longer operators: they are just text inside an argument', 'It runs faster only'], 1,
     'No shell means no shell language.'),
    ('An allowed command like cat can still be abused. How?',
     ['It cannot', 'By running it twice', 'By pointing it at files outside the sandbox, so arguments must be validated too'], 2,
     'An allowed program with unchecked arguments is an arbitrary file reader.'),
    ('What is the strongest design for an agent that needs to read files?',
     ['Make the shell prompt stricter', 'Give it a shell', 'Expose narrow operations (list, read) with validated parameters instead of a command line'], 2,
     'The smaller the interface, the less there is to get wrong.'),
]
HINTS = [
    "Read the symptoms: which commands ran that should not have? What do ';', '&&' and '$( )' mean to a shell?",
    "Parse with shlex.split (catch ValueError and raise PermissionError), require args[0] to be in the allowed set (exact match), and call subprocess.run(args, shell=False, cwd=root).",
    "Also resolve every path argument with os.path.realpath and require it to stay inside the real root. For grep, skip the first non-option word (the pattern).",
]


def _world():
    base = pathlib.Path(tempfile.mkdtemp(prefix="quest19_")).resolve()
    root = base / "sandbox"
    (root / "docs").mkdir(parents=True)
    (root / "notes.txt").write_text("hello\nworld\n")
    (root / "docs" / "a.txt").write_text("hello doc\n")
    (base / "outside.txt").write_text("OUTSIDE-SECRET\n")
    return base, root, base / "marker"


def check(path=STUB):
    base, root, marker = _world()
    try:
        return _check(path, base, root, marker)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _check(path, base, root, marker):
    legit = [("list the sandbox", "ls", "notes.txt"), ("list a folder", "ls docs", "a.txt"), ("print a file", "cat notes.txt", "hello"),
             ("count lines", "wc -l notes.txt", "2"), ("search a file", "grep hello docs/a.txt", "hello doc")]
    attacks = [("chain with ;", "ls; touch ../marker"), ("chain with &&", "cat notes.txt && touch ../marker"), ("command substitution", "ls $(touch ../marker)"),
               ("backticks", "ls `touch ../marker`"), ("redirect output", "ls > ../marker"), ("pipe into another program", "ls | tee ../marker"),
               ("a look-alike program name", "lsblk"), ("read a file outside the sandbox", "cat ../outside.txt"),
               ("search outside with grep", "grep -r OUTSIDE .."), ("an absolute path outside", f"cat {base / 'outside.txt'}")]
    problems = []
    for name, cmd, expect in legit:
        got, err = call(path, "run_tool", str(root), cmd)
        if err:
            problems.append(f"SYMPTOM: a legitimate command ({name}: {cmd!r}) failed: {err}")
        elif expect not in (got or ""):
            problems.append(f"SYMPTOM: a legitimate command ({name}: {cmd!r}) returned {got!r}, expected it to contain {expect!r}")
    for name, cmd in attacks:
        if marker.exists():
            marker.unlink()
        got, err = call(path, "run_tool", str(root), cmd)
        ran = marker.exists()
        leaked = got is not None and "OUTSIDE-SECRET" in got
        if ran:
            problems.append(f"SYMPTOM: an extra command ran ({name}: {cmd!r} created a file the tool should never create)")
        elif leaked:
            problems.append(f"SYMPTOM: the tool leaked a file from outside the sandbox ({name}: {cmd!r})")
        elif err is None:
            problems.append(f"SYMPTOM: a command that should be refused was accepted ({name}: {cmd!r}) and returned {got!r}")
        elif "PermissionError" not in err:
            problems.append(f"SYMPTOM: ({name}: {cmd!r}) raised the wrong kind of error: {err}")
    total = len(legit) + len(attacks)
    out = f"{total - len(problems)}/{total} test commands handled correctly."
    if problems:
        return False, out + "\n  " + "\n  ".join(problems[:5])
    return True, out + "\n\nOnly the four allowed commands can run, and only on sandbox files."
