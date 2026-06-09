import os
import json
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".cache", "comparison")

def _get_hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

def get_cached_structure(text: str) -> dict | None:
    """Retrieve cached extracted JSON structure for a given document text."""
    if not text:
        return None
    h = _get_hash(text)
    cache_path = os.path.join(CACHE_DIR, f"{h}.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading comparison cache: {e}")
    return None

def store_cached_structure(text: str, structure: dict) -> None:
    """Store extracted JSON structure for a given document text in cache."""
    if not text or not structure:
        return
    h = _get_hash(text)
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{h}.json")
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing comparison cache: {e}")
