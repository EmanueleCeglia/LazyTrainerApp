# prompt_cache.py
"""
Lightweight JSON-file prompt cache.

Typical use:
    from prompt_cache import cached_call
    result = cached_call("Create a full body training program", run)  # `run` is your model wrapper
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Callable, Dict

# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #

_LOCK = threading.Lock()  # protects reads/writes inside a single process


def _hash_prompt(prompt: str) -> str:
    """Return a stable SHA-256 hex digest for the prompt."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _load_cache(path: Path) -> Dict[str, str]:
    """Load the whole JSON cache file; return empty dict if file is missing/corrupted."""
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}  # start fresh on malformed file


def _save_cache(cache: Dict[str, str], path: Path) -> None:
    """Atomically write cache dict back to disk."""
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    tmp.replace(path)  # atomic on POSIX


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def cached_call(
    prompt: str,
    model_fn: Callable[[str], str],
    cache_path: Path | str = "prompt_cache.json",
) -> str:
    """
    Return cached response for `prompt` if present; otherwise call `model_fn`
    and persist the response.

    Parameters
    ----------
    prompt : str
        The prompt you would normally feed to your model.
    model_fn : Callable[[str], str]
        A callable that takes the prompt and returns the model's response
        (e.g. your `run` function).
    cache_path : Path | str, optional
        Location of the JSON cache file.  Defaults to "prompt_cache.json"
        in the current working directory.

    Returns
    -------
    str
        The model response (from cache or fresh call).
    """
    cache_path = Path(cache_path)
    key = _hash_prompt(prompt)

    # ---- Fast path: try cache first --------------------------------------- #
    with _LOCK:
        cache = _load_cache(cache_path)
        if key in cache:
            return cache[key]

    # ---- Cache miss: call the model -------------------------------------- #
    print(prompt)
    response = model_fn(prompt)

    # ---- Persist result --------------------------------------------------- #
    with _LOCK:
        cache[key] = response
        _save_cache(cache, cache_path)

    return response
