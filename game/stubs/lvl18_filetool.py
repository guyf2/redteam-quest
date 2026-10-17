"""this file-reading tool was written by a coding agent for an AI assistant.
The assistant may only read files inside its sandbox folder. The code looks careful. It is not.
Find the weaknesses from the symptoms and fix them, or tell your agent what to investigate."""
import os


def safe_read(root: str, user_path: str) -> str:
    """Return the text of the file at `user_path`, which the model supplied, relative to the sandbox folder `root`.
    Raise PermissionError for any path that does not stay inside `root`. Raise FileNotFoundError if it is inside but missing."""
    full = os.path.join(root, user_path)
    if not full.startswith(root):
        raise PermissionError("path escapes the sandbox")
    with open(full, encoding="utf-8") as f:
        return f.read()
