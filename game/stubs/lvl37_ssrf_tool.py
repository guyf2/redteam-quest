"""Level 37: this URL-fetching tool was written by a coding agent for an AI assistant that summarizes web pages.
The code looks careful. It is not. Find the weaknesses from the symptoms and fix them, or tell your agent what to investigate."""
import urllib.parse


def fetch_url(url: str, resolve, fetch) -> str:
    """Fetch `url` (supplied by the model) and return its text. `resolve(hostname) -> ip_str` and `fetch(url) -> text`
    are injected so this lab never makes a real network call. Raise PermissionError for anything that is not a plain
    http/https request to a public destination."""
    parsed = urllib.parse.urlparse(url)
    if "metadata" in (parsed.hostname or ""):
        raise PermissionError("blocked metadata hostname")
    return fetch(url)
