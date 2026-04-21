import os
import shutil
import sys
from pathlib import Path

import django
from django.utils.text import slugify
from icrawler.builtin import BingImageCrawler


BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
django.setup()

from trips.trekking_catalog import TREKKING_ROUTES
from trips.views import CITY_GUIDES
PLACES_DIR = BASE_DIR / "core" / "static" / "core" / "photos" / "places"
FOODS_DIR = BASE_DIR / "core" / "static" / "core" / "photos" / "foods"
TREK_PHOTO_DIR = BASE_DIR / "core" / "static" / "core" / "photos" / "trek"
MAPS_DIR = BASE_DIR / "core" / "static" / "core" / "maps"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def image_exists(base_path: Path, stem: str) -> bool:
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if (base_path / f"{stem}{ext}").exists():
            return True
    return False


def latest_file(path: Path):
    files = [p for p in path.iterdir() if p.is_file()]
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def download_one(query: str, target_dir: Path, stem: str) -> bool:
    ensure_dir(target_dir)
    if image_exists(target_dir, stem):
        return True

    temp_dir = target_dir / "_tmp" / stem
    ensure_dir(temp_dir)

    crawler = BingImageCrawler(storage={"root_dir": str(temp_dir)})
    crawler.crawl(keyword=query, max_num=1)

    latest = latest_file(temp_dir)
    if not latest:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False

    ext = latest.suffix.lower() or ".jpg"
    final_path = target_dir / f"{stem}{ext}"
    shutil.move(str(latest), str(final_path))
    shutil.rmtree(temp_dir, ignore_errors=True)
    return True


def populate_places() -> tuple[int, int]:
    ok = 0
    fail = 0
    for city_key, guide in CITY_GUIDES.items():
        city_dir = PLACES_DIR / city_key
        ensure_dir(city_dir)
        for place in guide.get("places", []):
            name = place.get("name", "")
            stem = slugify(name) or "place"
            query = f"{name} {guide.get('display_name', city_key)} Nepal travel photo"
            if download_one(query, city_dir, stem):
                ok += 1
                print(f"[place ok] {city_key}/{stem}")
            else:
                fail += 1
                print(f"[place fail] {city_key}/{stem}")
    return ok, fail


def populate_foods() -> tuple[int, int]:
    ok = 0
    fail = 0
    for city_key, guide in CITY_GUIDES.items():
        city_dir = FOODS_DIR / city_key
        ensure_dir(city_dir)
        for food in guide.get("foods", []):
            name = food.get("name", "")
            stem = slugify(name) or "food"
            query = f"{name} Nepal food {guide.get('display_name', city_key)}"
            if download_one(query, city_dir, stem):
                ok += 1
                print(f"[food ok] {city_key}/{stem}")
            else:
                fail += 1
                print(f"[food fail] {city_key}/{stem}")
    return ok, fail


def populate_trek_maps() -> tuple[int, int]:
    ok = 0
    fail = 0
    ensure_dir(TREK_PHOTO_DIR)
    ensure_dir(MAPS_DIR)

    for route_id, route in TREKKING_ROUTES.items():
        stem = f"{route_id}_route"
        target_map = MAPS_DIR
        query = f"{route.get('name', route_id)} Nepal trekking route map"

        if image_exists(target_map, stem):
            ok += 1
            print(f"[trek ok] {stem} (existing)")
            continue

        if download_one(query, target_map, stem):
            ok += 1
            print(f"[trek ok] {stem}")
        else:
            fail += 1
            print(f"[trek fail] {stem}")
    return ok, fail


def main():
    places_ok, places_fail = populate_places()
    foods_ok, foods_fail = populate_foods()
    treks_ok, treks_fail = populate_trek_maps()

    print("\n=== Summary ===")
    print(f"Places: ok={places_ok} fail={places_fail}")
    print(f"Foods: ok={foods_ok} fail={foods_fail}")
    print(f"Treks: ok={treks_ok} fail={treks_fail}")


if __name__ == "__main__":
    main()
