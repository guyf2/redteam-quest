import ipaddress
import pathlib
import urllib.parse

from .kit import call

TITLE = "Harden the URL-fetching tool"
WORLD = "agent"
KIND = "audit"
MODE = "audit"
XP = 70
STUB = pathlib.Path(__file__).resolve().parents[2] / "labs/05-agents/lvl37_ssrf_tool.py"
PRISTINE = pathlib.Path(__file__).resolve().parents[2] / "game/stubs/lvl37_ssrf_tool.py"

INTRO = ("An AI assistant can fetch a URL to summarize a web page for the user. A coding agent wrote the tool. It fetches whatever URL "
         "it is given. Find out whether the model (or whoever is steering it) can make it fetch somewhere it should never reach.")
CONCEPT = """A tool that fetches an arbitrary URL on the SERVER's behalf, at the model's request, is exposed to SERVER-SIDE REQUEST FORGERY (SSRF): the server, not the attacker's own machine, makes the network request, so it can reach places the attacker could never reach directly, like internal services and cloud metadata endpoints that only answer requests from inside the network.

The cloud metadata endpoint is the classic target: every major cloud provider exposes a well-known internal address (this lab simulates one with the constant 169.254.169.254, a real link-local address reserved for exactly this purpose) that answers with no authentication at all, including, on a misconfigured host, temporary cloud credentials. If an AI agent's URL tool can be steered (a model can be persuaded to fetch any URL, as levels 8 and 9 showed) to reach that address, the attacker walks out with the server's own cloud credentials.

The common mistakes, all visible in the starting code:
  1. NO DESTINATION CHECK AT ALL. Any scheme, any host, any port is fetched.
  2. CHECKING THE SCHEME ONLY. 'https://' looks safe, but https://169.254.169.254/ is still the metadata endpoint.
  3. TRUSTING A HOSTNAME BLOCKLIST. Blocking the literal string 'metadata' misses the raw IP, an alternate encoding of it, or a different private address entirely.
  4. IGNORING PRIVATE AND LINK-LOCAL RANGES. 169.254.0.0/16, 127.0.0.0/8, 10.0.0.0/8, 172.16.0.0/12 and 192.168.0.0/16 are never legitimate destinations for a public web-summary tool.

The fix: parse the URL, resolve the host, and ALLOWLIST: only http/https, and only a host that is not a private, loopback or link-local address (and ideally only a host on an explicit allowlist of real destinations for production). This grader never makes a real network call; a fake in-process 'HTTP layer' stands in for the network so the lab stays fully local and safe."""
WIN = "A legitimate public URL must be fetched; any URL resolving to a private, loopback or link-local address (including the simulated cloud metadata address) must raise PermissionError, and no real network call may ever be needed to prove it."
SIGNATURE_NOTE = "fetch_url(url, resolve, fetch): `resolve(hostname) -> ip_str` and `fetch(url) -> text` are injected so no real network call is ever made; your job is the check in between."
BRIEF = f"{INTRO}\n\n{CONCEPT}\n\n{WIN}"

VIZ = []
SPEC_PLACEHOLDER = "Tell your agent what is wrong. Click 'Use the grader's last message' to paste the symptom."
SPEC_CHIPS = [
    ("Use the grader's last message", "@LAST_GRADER"),
    ("Ask for the root cause", "Explain the root cause of this symptom before changing anything, then fix only that."),
    ("Name the rule", "Parse the URL, require the scheme to be http or https, resolve the host to an IP, and reject any IP that is private, loopback, link-local or otherwise not a globally routable public address."),
    ("Signature", SIGNATURE_NOTE),
]
SPEC_CHECKS = [
    ("Names the symptom", r"symptom|metadata|fetched|allowed|blocked|returned|raised|ssrf|private|internal"),
    ("States the rule that is broken", r"scheme|private|loopback|link.?local|resolve|ip|allowlist|blocklist|hostname"),
    ("Asks for cause, not a blind patch", r"why|root|cause|explain|because"),
]
AGENT_TASK = ("The player found problems in this tool. Apply ONLY the fixes their instructions describe, "
              "keep everything else unchanged, and say what you changed and why.")

QUIZ = [
    ("Why is SSRF dangerous even though the attacker never gets to make requests from their own machine?",
     ['It is not dangerous, since the attacker has no direct access', "The server makes the request on the attacker's behalf, reaching internal addresses (like a cloud metadata endpoint) the attacker could never reach themselves", 'SSRF only affects static websites'], 1,
     'The server becomes a proxy into its own private network, including places that trust any request coming from inside.'),
    ("Why is a hostname blocklist (block 'metadata', 'internal', 'localhost') not enough?",
     ["Raw IP addresses, alternate encodings, and other private ranges never appear on the list but reach the same places", 'Blocklists are slow', 'DNS always resolves instantly'], 0,
     'A blocklist enumerates known bad names; an attacker just uses the IP, or a different private address, instead.'),
    ('Why must the check run on the RESOLVED IP address, not just the URL string?',
     ['A hostname can resolve to a private or link-local IP even though the hostname itself looks innocuous', 'IP addresses never change', 'It only matters for HTTPS'], 0,
     'DNS is attacker-influenceable text too; what matters is where the request actually lands.'),
    ('What does a cloud metadata endpoint like 169.254.169.254 typically expose with no authentication?',
     ['Nothing of value', "Instance configuration and sometimes temporary cloud credentials for the running server", 'Only the server uptime'], 1,
     'That is exactly why SSRF into cloud metadata is treated as a critical finding in real engagements.'),
]
HINTS = [
    "Read the symptoms: which kinds of URL got through? What do they have in common (an IP range, a scheme, a spelled-out metadata address)?",
    "fetch_url(url, resolve, fetch): parse with urllib.parse.urlparse, require scheme in {'http', 'https'}, call resolve(hostname) to get the real IP, and build an ipaddress.ip_address from it.",
    "Reject with PermissionError if the IP is_private, is_loopback, is_link_local or is_reserved (ipaddress module has all four); only call fetch(url) after the IP passes.",
]


# ---- fake in-process "HTTP layer": no real network call is ever made, matching L18/L19's fake filesystem/shell ----
PAGE = "<html><body>Welcome to Acme's public blog. Today's post: our new return policy.</body></html>"
METADATA = '{"iam": {"temporary-credentials": "AKIA-FAKE-SECRET-DO-NOT-USE"}}'
FAKE_DNS = {
    "blog.acme.example": "93.184.216.34",
    "169.254.169.254": "169.254.169.254",
    "metadata.google.internal": "169.254.169.254",
    "internal.acme.example": "10.0.0.5",
    "localhost": "127.0.0.1",
    "evil-redirect.acme.example": "169.254.169.254",  # a hostname that LOOKS public but resolves to the metadata address
}


def fake_resolve(host):
    return FAKE_DNS.get(host, host)  # unknown hosts: assume the literal string is already an IP, like a direct-IP attack


def fake_fetch(url):
    """Stands in for the real network call. Does NOT itself validate the destination: that is the player's job in
    fetch_url before ever calling this. Injected so no real network call is ever made in this lab."""
    host = urllib.parse.urlparse(url).hostname or ""
    ip = fake_resolve(host)
    if ip == "169.254.169.254":
        return METADATA
    if ip == "93.184.216.34":
        return PAGE
    return "<html>ok</html>"


def check(path=STUB):
    legit = [("a public blog URL", "https://blog.acme.example/post/1", PAGE)]
    attacks = [
        ("direct metadata IP", "http://169.254.169.254/latest/meta-data/iam/"),
        ("https to metadata IP", "https://169.254.169.254/latest/meta-data/iam/"),
        ("metadata hostname alias", "http://metadata.google.internal/computeMetadata/v1/"),
        ("a public-looking hostname that resolves to metadata", "http://evil-redirect.acme.example/"),
        ("an internal RFC1918 address", "http://internal.acme.example/admin"),
        ("loopback", "http://localhost:8080/debug"),
        ("raw loopback IP", "http://127.0.0.1/debug"),
        ("a non-http scheme", "file:///etc/passwd"),
    ]
    problems = []
    for name, url, want in legit:
        got, err = call(path, "fetch_url", url, fake_resolve, fake_fetch)
        if err:
            problems.append(f"SYMPTOM: a legitimate request ({name}: {url!r}) failed: {err}")
        elif got != want:
            problems.append(f"SYMPTOM: a legitimate request ({name}: {url!r}) returned unexpected content")
    for name, url in attacks:
        got, err = call(path, "fetch_url", url, fake_resolve, fake_fetch)
        if err is None:
            problems.append(f"SYMPTOM: the tool fetched a forbidden destination ({name}: {url!r})")
        elif "PermissionError" in err:
            continue
        else:
            problems.append(f"SYMPTOM: ({name}: {url!r}) raised the wrong kind of error: {err}")
    total = len(legit) + len(attacks)
    out = f"{total - len(problems)}/{total} test requests handled correctly."
    if problems:
        return False, out + "\n  " + "\n  ".join(problems[:5])
    return True, out + "\n\nThe boundary now holds: nothing internal is reachable, the public web still is."
