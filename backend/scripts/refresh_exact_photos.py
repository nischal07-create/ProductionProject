import os
import sys
from pathlib import Path
from urllib.parse import quote

import django
import requests
from django.utils.text import slugify


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
django.setup()

from trips.views import CITY_GUIDES  # noqa: E402


PLACES_DIR = BASE_DIR / "core" / "static" / "core" / "photos" / "places"
FOODS_DIR = BASE_DIR / "core" / "static" / "core" / "photos" / "foods"

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary"
UA = {
    "User-Agent": "TrailMateExactPhotoRefresher/1.0 (https://trailmate.local; support@trailmate.local)"
}

PLACE_BLOCKED = [
    "map",
    "logo",
    "icon",
    "emblem",
    "flag",
    "illustration",
    "diagram",
    "banner",
    "coat of arms",
]

FOOD_BLOCKED = [
    "logo",
    "icon",
    "emblem",
    "flag",
    "illustration",
    "diagram",
    "menu",
]


def _keywords(name):
    stop = {"the", "and", "of", "for", "with", "nepal", "kathmandu", "pokhara"}
    out = []
    for token in str(name or "").replace("(", " ").replace(")", " ").replace("-", " ").split():
        t = token.strip().lower()
        if len(t) >= 4 and t not in stop:
            out.append(t)
    return out


def _wiki_title_search(query):
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": "6",
        "format": "json",
    }
    try:
        resp = requests.get(WIKI_API, headers=UA, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
    except Exception:
        return []

    return [item.get("title", "") for item in payload.get("query", {}).get("search", []) if item.get("title")]


def _wiki_summary_image(title):
    if not title:
        return ""
    url = f"{WIKI_SUMMARY}/{quote(title)}"
    try:
        resp = requests.get(url, headers=UA, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return ""

    img = data.get("originalimage", {}).get("source") or data.get("thumbnail", {}).get("source") or ""
    return str(img)


def _search_wiki_image(query, required_terms, blocked_terms):
    required = [t.lower() for t in required_terms if t]
    blocked = [t.lower() for t in blocked_terms if t]

    titles = _wiki_title_search(query)
    for title in titles:
        lower_title = title.lower()
        if blocked and any(term in lower_title for term in blocked):
            continue
        if required and not any(term in lower_title for term in required):
            continue
        candidate = _wiki_summary_image(title)
        if candidate and candidate.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return candidate

    # Relaxed fallback by title only.
    for title in titles:
        lower_title = title.lower()
        if blocked and any(term in lower_title for term in blocked):
            continue
        candidate = _wiki_summary_image(title)
        if candidate and candidate.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return candidate
    return ""


def _download_to_jpg(url, target_file):
    try:
        resp = requests.get(url, headers=UA, timeout=25)
        resp.raise_for_status()
    except Exception:
        return False

    target_file.parent.mkdir(parents=True, exist_ok=True)
    with open(target_file, "wb") as f:
        f.write(resp.content)
    return True


def refresh_places():
    updated = 0
    failed = 0

    for city_key, guide in CITY_GUIDES.items():
        city_name = guide.get("display_name", city_key.title())
        city_dir = PLACES_DIR / city_key
        city_dir.mkdir(parents=True, exist_ok=True)

        for place in guide.get("places", []):
            name = place.get("name", "")
            slug = slugify(name) or "place"
            target = city_dir / f"{slug}.jpg"

            required = _keywords(name)
            query = f"{name} {city_name} Nepal"
            best = _search_wiki_image(query, required, PLACE_BLOCKED)
            if not best:
                query = f"{name} Nepal"
                best = _search_wiki_image(query, required, PLACE_BLOCKED)

            if best and _download_to_jpg(best, target):
                updated += 1
                print(f"[place updated] {city_key}/{slug}")
            else:
                failed += 1
                print(f"[place failed] {city_key}/{slug}")

    return updated, failed


def refresh_foods():
    updated = 0
    failed = 0

    for city_key, guide in CITY_GUIDES.items():
        city_name = guide.get("display_name", city_key.title())
        city_dir = FOODS_DIR / city_key
        city_dir.mkdir(parents=True, exist_ok=True)

        for food in guide.get("foods", []):
            name = food.get("name", "")
            slug = slugify(name) or "food"
            target = city_dir / f"{slug}.jpg"

            required = _keywords(name)
            if "momo" in name.lower() and "momo" not in required:
                required.append("momo")
            query = f"{name} Nepal food"
            best = _search_wiki_image(query, required, FOOD_BLOCKED)
            if not best:
                query = f"{name} {city_name} food"
                best = _search_wiki_image(query, required, FOOD_BLOCKED)

            if best and _download_to_jpg(best, target):
                updated += 1
                print(f"[food updated] {city_key}/{slug}")
            else:
                failed += 1
                print(f"[food failed] {city_key}/{slug}")

    return updated, failed


def main():
    p_ok, p_fail = refresh_places()
    f_ok, f_fail = refresh_foods()

    print("\n=== Exact Refresh Summary ===")
    print(f"Places updated: {p_ok}, failed: {p_fail}")
    print(f"Foods updated: {f_ok}, failed: {f_fail}")


if __name__ == "__main__":
    main()
