"""this command tool was written by a coding agent. The assistant may run only four read-only commands
(ls, cat, wc, grep) on files inside its sandbox. The code looks careful. It is not.
Find the weaknesses from the symptoms and fix them, or tell your agent what to investigate."""
import subprocess

ALLOWED = ("ls", "cat", "wc", "grep")


def run_tool(root: str, command: str) -> str:
    """Run `command` (a string the model produced) inside the sandbox folder `root` and return its output.
    Raise PermissionError if the command is not allowed."""
    if not command.strip().startswith(ALLOWED):
        raise PermissionError("command not allowed")
    result = subprocess.run(command, shell=True, cwd=root, capture_output=True, text=True, timeout=10)
    return result.stdout
