"""write the agent's permission policy. Your agent fills this in from your spec (or you can write it yourself)."""


def allow(call: dict, ctx: dict) -> bool:
    """Decide whether the assistant may make this tool call.

    call: {"tool": name, "args": {...}}. Tools: read_inbox, read_file, search (read-only) and
          send_email(to, body), delete_file(path), http_post(url, data) (privileged: they change the world or send data out).
    ctx: {"user_message": what the real user typed,
          "tainted": True if the assistant has read untrusted content (an email, a web page, a file from outside) since,
          "address_book": {"name": "address", ...} of people the user knows}.
    Return True to allow the call, False to block it."""
    # TODO: your policy here
    raise NotImplementedError
