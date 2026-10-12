"""Tiny client for the local ollama server (stdlib only). Targets for LLM levels are always local models."""
import http.client
import json
import os
import socket
import urllib.parse
import urllib.request

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
FAST, STRONG = "llama3.2:3b", "aya-expanse:8b"  # fast target for iteration, stronger target for harder rungs


_conn = None
cancelled = False  # set when the player pressed Stop during the last chat() call


def cancel():
    """Cut the connection of the chat() call in progress so the model stops generating."""
    global cancelled
    cancelled = True
    c = _conn
    if c is not None and c.sock is not None:
        try:
            c.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass


def chat(messages, model=FAST, temperature=0.7, timeout=180):
    """messages: [{"role": "system"|"user"|"assistant", "content": str, "images": [base64 str]?}]. Returns the reply text.
    The connection is held open from the start so cancel() can cut it while the model is still generating."""
    global _conn, cancelled
    cancelled = False
    body = json.dumps({"model": model, "messages": messages, "stream": False,
                       "options": {"temperature": temperature}}).encode()
    u = urllib.parse.urlparse(HOST)
    conn = http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)
    _conn = conn
    try:
        conn.request("POST", "/api/chat", body, {"Content-Type": "application/json"})
        resp = conn.getresponse()
        data = resp.read()
        if resp.status != 200:
            raise RuntimeError(f"ollama returned {resp.status}: {data[:200]!r}")
        return json.loads(data)["message"]["content"]
    finally:
        _conn = None
        conn.close()


def free_gpu():
    """Unload every resident ollama model so a vision model can have the GPU. Safe to call any time."""
    try:
        with urllib.request.urlopen(f"{HOST}/api/ps", timeout=5) as r:
            loaded = [m["name"] for m in json.load(r).get("models", [])]
        for name in loaded:
            req = urllib.request.Request(f"{HOST}/api/generate", json.dumps({"model": name, "keep_alive": 0}).encode(), {"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass  # ollama not running: nothing to free
