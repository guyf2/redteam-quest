import os
import pathlib
import shutil
import tempfile

from .kit import call

TITLE = "Harden the file tool"
WORLD = "agent"
KIND = "audit"
MODE = "audit"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/05-agents/lvl18_filetool.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl18_filetool.py"

INTRO = ("An AI assistant can read files, but only inside its sandbox folder. The tool was written by a coding agent and passes a quick "
         "test. Before it ships, find out whether the model (or whoever is steering it) can read anything outside the folder.")
CONCEPT = """An agent's tool is the last line of defense. A model can be persuaded to ask for any path (levels 8 and 9 showed how), so the tool must enforce the boundary itself, in code, and never rely on the model to behave. File access is the classic place this goes wrong, a well-known weakness class called PATH TRAVERSAL.

The common mistakes, all visible in the starting code:
  1. TRUSTING THE TEXT OF THE PATH. 'notes/../../outside.txt' looks like it starts inside the folder, but the '..' parts climb out. You must resolve the path to its real, absolute form first, then compare.
  2. ABSOLUTE PATHS. Joining a root with '/tmp/outside.txt' throws the root away: os.path.join('/sandbox', '/tmp/outside.txt') is '/tmp/outside.txt'.
  3. THE PREFIX CHECK. 'starts with /srv/files' also matches '/srv/files_old/secret.txt'. A folder name is not the same as a path prefix. Compare whole path components (os.path.commonpath), not characters.
  4. SYMLINKS. A symbolic link inside the sandbox can point anywhere. Resolving with os.path.realpath follows links before you decide.

The pattern that fixes all four: resolve both the root and the requested path with realpath, then check that the root is the common ancestor. Do the check on the RESOLVED path and open that same resolved path, so nothing can change between the check and the use.

Then test it like an attacker would: a list of tricky inputs, and a list of legitimate ones that must still work (a tool that blocks everything is useless). The grader gives you symptoms only."""
WIN = "Every legitimate path must return its file's text, every escaping path must raise PermissionError, and a missing file inside the sandbox must raise FileNotFoundError."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = [["path_lab", {}]]
SPEC_PLACEHOLDER = "Tell your agent what is wrong. Click 'Use the grader's last message' to paste the symptom."
SPEC_CHIPS = [
    ("Use the grader's last message", "@LAST_GRADER"),
    ("Ask for the root cause", "Explain the root cause of this symptom before changing anything, then fix only that."),
    ("Name the rule", "Resolve both the root and the requested path to real absolute paths (following symlinks), then require the root to be the common ancestor, comparing whole path components, not characters."),
]
SPEC_CHECKS = [
    ("Names the symptom", r"symptom|escap|outside|allowed|blocked|returned|raised|traversal"),
    ("States the rule that is broken", r"realpath|resolve|commonpath|symlink|component|prefix|absolute|\.\."),
    ("Asks for cause, not a blind patch", r"why|root|cause|explain|because"),
]
AGENT_TASK = ("The player found problems in this tool. Apply ONLY the fixes their instructions describe, "
              "keep everything else unchanged, and say what you changed and why.")

QUIZ = [
    ("Why is checking that a path 'starts with' the sandbox folder not enough?",
     ["'..' segments, symlinks and look-alike folder names (/srv/files_old) can pass or defeat a text prefix check", 'The sandbox check only runs once per session', 'Paths are case sensitive'], 0,
     'Text comparison is not path comparison. Resolve first, compare components.'),
    ("os.path.join('/sandbox', '/etc/hosts') returns...",
     ["'/sandbox/etc/hosts'", 'an error', "'/etc/hosts': an absolute second argument replaces the first"], 2,
     'That is why an absolute path from the model can walk straight out.'),
    ('Why must you open the RESOLVED path and not the original one after checking?',
     ['It keeps the file handle open longer', 'So the thing you checked is the thing you use; otherwise the filesystem can change between check and use', 'Tradition'], 1,
     'Check-then-use on different strings is a classic race and bypass.'),
    ("The model is told 'only read files in the sandbox'. Is the tool's check still needed?",
     ['Yes: instructions to a model are advice; only code enforces a boundary', 'No, the model obeys', 'Only for large files'], 0,
     'Prompt rules are not security controls. The tool is the boundary.'),
]
HINTS = [
    "Read the symptoms: each one names a kind of path that got through. Which of those would a plain 'starts with' text check miss?",
    "Use os.path.realpath on the root AND on the joined path. Then compare with os.path.commonpath([real_root, real_path]) == real_root.",
    "Open the resolved path, not the original, and keep raising PermissionError for escapes and FileNotFoundError for a missing file inside the sandbox.",
]


def _world():
    base = pathlib.Path(tempfile.mkdtemp(prefix="quest18_")).resolve()
    root = base / "sandbox"
    (root / "docs").mkdir(parents=True)
    (root / "notes.txt").write_text("hello notes")
    (root / "docs" / "a.txt").write_text("doc a")
    (base / "sandbox_evil").mkdir()
    (base / "sandbox_evil" / "key.txt").write_text("EVIL KEY")
    (base / "outside.txt").write_text("OUTSIDE")
    os.symlink(base / "outside.txt", root / "link_out")
    os.symlink(base / "sandbox_evil", root / "linkdir")
    return base, root


def check(path=STUB):
    base, root = _world()
    try:
        return _check(path, base, root)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _check(path, base, root):
    legit = [("a plain file", "notes.txt", "hello notes"), ("a nested file", "docs/a.txt", "doc a"), ("a ./ path", "./notes.txt", "hello notes"),
             ("a path that goes down and back up inside the sandbox", "docs/../notes.txt", "hello notes")]
    attacks = [("climbs out with ..", "../outside.txt"), ("climbs out from a subfolder", "docs/../../outside.txt"), ("an absolute path", str(base / "outside.txt")),
               ("a look-alike folder name (prefix trap)", "../sandbox_evil/key.txt"), ("a symlink to a file outside", "link_out"), ("a symlink to a folder outside", "linkdir/key.txt")]
    problems = []
    for name, p, want in legit:
        got, err = call(path, "safe_read", str(root), p)
        if err:
            problems.append(f"SYMPTOM: a legitimate request ({name}: {p!r}) failed: {err}")
        elif got != want:
            problems.append(f"SYMPTOM: a legitimate request ({name}: {p!r}) returned {got!r}, expected {want!r}")
    for name, p in attacks:
        got, err = call(path, "safe_read", str(root), p)
        if err is None:
            problems.append(f"SYMPTOM: the tool read a file outside the sandbox ({name}: {p!r} returned {got!r})")
        elif "PermissionError" in err or "escapes" in err:
            continue
        else:
            problems.append(f"SYMPTOM: ({name}: {p!r}) raised the wrong kind of error: {err}")
    got, err = call(path, "safe_read", str(root), "docs/missing.txt")
    if err is None or "FileNotFound" not in err and "No such file" not in err:
        problems.append("SYMPTOM: a missing file inside the sandbox should raise FileNotFoundError.")
    total = len(legit) + len(attacks) + 1
    out = f"{total - len(problems)}/{total} test requests handled correctly."
    if problems:
        return False, out + "\n  " + "\n  ".join(problems[:5])
    return True, out + "\n\nThe boundary now holds: nothing escapes, nothing legitimate is blocked."
