import os
import sys
from pathlib import Path

import django

BASE_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
django.setup()

from trips.models import Destination, Activity


KATHMANDU_ACTIVITIES = [
    {
        "name": "Heritage Walking & Responsible Cultural Workshop",
        "description": "Guided walking tour of old city with a short hands-on cultural workshop led by local artisans. Low-impact, community-led.",
        "tags": "culture,walking,workshop,community",
        "cost": "25.00",
        "duration": 3.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/heritage-tour-1.jpg",
            "/static/core/photos/places/kathmandu/heritage-tour-2.jpg",
            "/static/core/photos/places/kathmandu/heritage-tour-3.jpg",
        ]
    },
    {
        "name": "City Mountain Biking (Nagarjun Trails)",
        "description": "Half-day guided mountain-bike trip on safe marked trails around Nagarjun and Shivapuri ridgelines. Helmet recommended.",
        "tags": "biking,offroad,adventure,outdoors",
        "cost": "45.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/kathmandu/mountain-biking-1.jpg",
            "/static/core/photos/places/kathmandu/mountain-biking-2.jpg",
            "/static/core/photos/places/kathmandu/mountain-biking-3.jpg",
        ]
    },
    {
        "name": "Rooftop Yoga & Sunrise Session",
        "description": "Early-morning yoga overlooking the valley and distant Himalaya (seasonal clear-sky mornings). Responsible instructor-led class.",
        "tags": "wellness,yoga,sunrise,relax",
        "cost": "18.00",
        "duration": 1.0,
        "indoor": True,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/rooftop-yoga-1.jpg",
            "/static/core/photos/places/kathmandu/rooftop-yoga-2.jpg",
        ]
    },
    {
        "name": "Thamel Bike Rental & Self-Guided City Loop",
        "description": "Short-term bike rental for self-guided exploration on mixed city roads; includes helmet and basic safety briefing.",
        "tags": "rental,bike,self-guided,urban",
        "cost": "12.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/bike-rental-1.jpg",
            "/static/core/photos/places/kathmandu/bike-rental-2.jpg",
        ]
    },
    {
        "name": "Guided Rock Climbing Intro (Local Crags)",
        "description": "Introductory climbing session with certified guides on accessible crags near the valley. Safety gear provided.",
        "tags": "climbing,adventure,skills,safety",
        "cost": "65.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/kathmandu/rock-climbing-1.jpg",
            "/static/core/photos/places/kathmandu/rock-climbing-2.jpg",
            "/static/core/photos/places/kathmandu/rock-climbing-3.jpg",
        ]
    },
    {
        "name": "Culinary Street Food Responsible Tour",
        "description": "Small-group evening tour sampling local specialties with hygiene-conscious vendors and allergy-aware guidance.",
        "tags": "food,tour,streetfood,culinary",
        "cost": "30.00",
        "duration": 2.5,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/street-food-1.jpg",
            "/static/core/photos/places/kathmandu/street-food-2.jpg",
            "/static/core/photos/places/kathmandu/street-food-3.jpg",
        ]
    },
    {
        "name": "Chandragiri Cable Car + Short Hike",
        "description": "Cable car ride with a short ridge walk and picnic; seasonal winds may affect operations.",
        "tags": "cablecar,hike,viewpoint,nature",
        "cost": "35.00",
        "duration": 3.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/chandragiri-1.jpg",
            "/static/core/photos/places/kathmandu/chandragiri-2.jpg",
        ]
    },
    {
        "name": "Photography & Conservation Walk",
        "description": "Guided nature photography walk focusing on respectful wildlife and habitat viewing practices.",
        "tags": "photography,nature,conservation,walking",
        "cost": "22.00",
        "duration": 2.5,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/photography-walk-1.jpg",
            "/static/core/photos/places/kathmandu/photography-walk-2.jpg",
        ]
    },
    {
        "name": "Evening Cultural Dance Show & Workshop",
        "description": "Attend a short traditional dance performance followed by a participatory workshop run by local performers.",
        "tags": "culture,dance,performance,workshop",
        "cost": "28.00",
        "duration": 2.0,
        "indoor": True,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/cultural-dance-1.jpg",
            "/static/core/photos/places/kathmandu/cultural-dance-2.jpg",
        ]
    },
    {
        "name": "Responsible Volunteer Half-Day Experience",
        "description": "Half-day volunteering with a registered local NGO (education, clean-up projects) — pre-book and check requirements.",
        "tags": "volunteer,community,responsible,learning",
        "cost": "0.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/kathmandu/volunteer-1.jpg",
            "/static/core/photos/places/kathmandu/volunteer-2.jpg",
        ]
    },
]

POKHARA_ACTIVITIES = [
    {
        "name": "Tandem Paragliding from Sarangkot",
        "description": "World-famous tandem paragliding flights (weather dependent) with certified pilots; ideal for sunrise flights.",
        "tags": "paragliding,adrenaline,sky,seasonal",
        "cost": "125.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/paragliding-1.jpg",
            "/static/core/photos/places/pokhara/paragliding-2.jpg",
            "/static/core/photos/places/pokhara/paragliding-3.jpg",
        ]
    },
    {
        "name": "Seasonal Hot Air Balloon (Lake & Mountain Views)",
        "description": "Occasional hot-air balloon operations over the Pokhara valley in clear-season windows; book early and follow safety briefings.",
        "tags": "hotairballoon,seasonal,scenic,photography",
        "cost": "280.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/pokhara/hot-air-balloon-1.jpg",
            "/static/core/photos/places/pokhara/hot-air-balloon-2.jpg",
            "/static/core/photos/places/pokhara/hot-air-balloon-3.jpg",
            "/static/core/photos/places/pokhara/hot-air-balloon-4.jpg",
            "/static/core/photos/places/pokhara/hot-air-balloon-5.jpg",
        ]
    },
    {
        "name": "Kusma (Khimti) Bungee & Canyon Swing",
        "description": "Nearby bungee jump and canyon swings for adrenaline seekers; operator safety certifications recommended.",
        "tags": "bungee,adrenaline,seasonal,thrill",
        "cost": "180.00",
        "duration": 1.5,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/bungee-1.jpg",
            "/static/core/photos/places/pokhara/bungee-2.jpg",
            "/static/core/photos/places/pokhara/bungee-3.jpg",
        ]
    },
    {
        "name": "Seti/Trishuli Day White-Water Rafting",
        "description": "Full-day or half-day rafting options on nearby rivers; choose grade and operator according to experience and safety briefings.",
        "tags": "rafting,water,adventure,river",
        "cost": "95.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/rafting-1.jpg",
            "/static/core/photos/places/pokhara/rafting-2.jpg",
            "/static/core/photos/places/pokhara/rafting-3.jpg",
        ]
    },
    {
        "name": "Zipline & Canopy Adventure",
        "description": "High-elevation zipline runs above forested valleys; seasonal weather restrictions apply.",
        "tags": "zipline,adrenaline,forest,seasonal",
        "cost": "68.00",
        "duration": 2.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/pokhara/zipline-1.jpg",
            "/static/core/photos/places/pokhara/zipline-2.jpg",
        ]
    },
    {
        "name": "Seasonal Skydiving Festival (Tandem)",
        "description": "Occasional tandem skydiving drop zones for certified operators during good-weather festival windows; book well in advance.",
        "tags": "skydiving,seasonal,tandem,adrenaline",
        "cost": "450.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/skydiving-1.jpg",
            "/static/core/photos/places/pokhara/skydiving-2.jpg",
            "/static/core/photos/places/pokhara/skydiving-3.jpg",
        ]
    },
    {
        "name": "Motorbike Rental & Off-Road Annapurna Foothills Tour",
        "description": "Daily motorbike rentals and guided off-road loops on maintained trails; safety gear and local license required.",
        "tags": "motorbike,rental,offroad,tour",
        "cost": "55.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/motorbike-1.jpg",
            "/static/core/photos/places/pokhara/motorbike-2.jpg",
        ]
    },
    {
        "name": "Lake Boat Rental & Sunset Cruise",
        "description": "Private or shared boat rentals on Phewa Lake with options for sunset photography and gentle paddling.",
        "tags": "boat,relax,photography,romantic",
        "cost": "25.00",
        "duration": 1.5,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/pokhara/boat-sunset-1.jpg",
            "/static/core/photos/places/pokhara/boat-sunset-2.jpg",
        ]
    },
    {
        "name": "Mountain Biking Trails Around Begnas & Phewa",
        "description": "Guided single-day mountain-biking on designated trails around Pokhara's lakes and foothills.",
        "tags": "biking,offroad,adventure,nature",
        "cost": "60.00",
        "duration": 5.0,
        "indoor": False,
        "family_friendly": False,
        "photos": [
            "/static/core/photos/places/pokhara/mountain-biking-1.jpg",
            "/static/core/photos/places/pokhara/mountain-biking-2.jpg",
        ]
    },
    {
        "name": "Caving & Gupteshwor Exploration",
        "description": "Guided exploration of Gupteshwor and nearby caves with responsible lighting and conservation-aware practices.",
        "tags": "caving,adventure,nature,conservation",
        "cost": "20.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": True,
        "photos": [
            "/static/core/photos/places/pokhara/caving-1.jpg",
            "/static/core/photos/places/pokhara/caving-2.jpg",
        ]
    },
]


def create_activity(destination_name: str, item: dict):
    dest, _ = Destination.objects.get_or_create(name=destination_name)
    obj, created = Activity.objects.update_or_create(
        destination=dest,
        name=item["name"],
        defaults={
            "description": item.get("description", ""),
            "tags": item.get("tags", ""),
            "cost_estimate": item.get("cost", "0.00"),
            "duration_hours": item.get("duration", 1.0),
            "indoor": item.get("indoor", False),
            "family_friendly": item.get("family_friendly", True),
            "photo_urls": item.get("photos", []),
        },
    )
    return obj, created


def main():
    created = 0
    updated = 0

    for item in KATHMANDU_ACTIVITIES:
        obj, was_created = create_activity("Kathmandu", item)
        if was_created:
            created += 1
        else:
            updated += 1

    for item in POKHARA_ACTIVITIES:
        obj, was_created = create_activity("Pokhara", item)
        if was_created:
            created += 1
        else:
            updated += 1

    print(f"Activities added: {created}, updated: {updated}")


if __name__ == "__main__":
    main()
