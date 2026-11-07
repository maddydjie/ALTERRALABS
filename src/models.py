"""One thin model interface: generate(prompt) -> str, with a disk cache.

Cache key = hash(model + prompt + params), so a rerun never re-queries and
results stay frozen (reproducibility rule 4).
"""
import hashlib
import json
import os
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    with open(os.path.join(ROOT, "config.yaml")) as f:
        return yaml.safe_load(f)


def _cache_path(cfg, key):
    d = os.path.join(ROOT, cfg["paths"]["cache"])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, key + ".json")


def generate(prompt, model_key="primary", system=None, **overrides):
    """Return the model's text for `prompt`. Greedy (temperature 0) and seeded by default."""
    cfg = load_config()
    m = cfg["models"][model_key]
    params = dict(cfg["generation"])
    params.update(overrides)
    payload = {
        "model": m["ollama_name"],
        "prompt": prompt,
        "system": system or "",
        "stream": False,
        "options": params,
    }
    if "think" in m:  # qwen3.5 is a thinking model: without think=false it burns all tokens on reasoning
        payload["think"] = m["think"]
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    path = _cache_path(cfg, key)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)["response"]

    check_digest(cfg, m)
    req = urllib.request.Request(
        cfg["ollama_url"] + "/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        out = json.load(r)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        # store the request too so every cached answer is auditable
        json.dump({"request": payload, "response": out["response"]}, f)
    os.replace(tmp, path)  # atomic: a crash mid-write never leaves a broken cache file
    return out["response"]


def check_digest(cfg, m):
    """Refuse to query a local model whose digest differs from the one pinned in config.yaml.
    Only runs on a cache miss, so cached reruns work without Ollama. Not part of the cache key,
    so existing cache files stay valid."""
    pinned = m["revision"].replace("ollama-digest-", "")
    with urllib.request.urlopen(cfg["ollama_url"] + "/api/tags", timeout=30) as r:
        tags = {t["name"]: t["digest"] for t in json.load(r)["models"]}
    local = tags.get(m["ollama_name"], "")
    if not local.startswith(pinned):
        raise RuntimeError("%s digest %s does not match pinned %s" % (m["ollama_name"], local[:12], pinned))
