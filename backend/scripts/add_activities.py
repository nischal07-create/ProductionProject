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
        "cost": "15.00",
        "duration": 3.0,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "City Mountain Biking (Nagarjun Trails)",
        "description": "Half-day guided mountain-bike trip on safe marked trails around Nagarjun and Shivapuri ridgelines. Helmet recommended.",
        "tags": "biking,offroad,adventure,outdoors",
        "cost": "30.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Rooftop Yoga & Sunrise Session",
        "description": "Early-morning yoga overlooking the valley and distant Himalaya (seasonal clear-sky mornings). Responsible instructor-led class.",
        "tags": "wellness,yoga,sunrise,relax",
        "cost": "8.00",
        "duration": 1.0,
        "indoor": True,
        "family_friendly": True,
    },
    {
        "name": "Thamel Bike Rental & Self-Guided City Loop",
        "description": "Short-term bike rental for self-guided exploration on mixed city roads; includes helmet and basic safety briefing.",
        "tags": "rental,bike,self-guided,urban",
        "cost": "6.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Guided Rock Climbing Intro (Local Crags)",
        "description": "Introductory climbing session with certified guides on accessible crags near the valley. Safety gear provided.",
        "tags": "climbing,adventure,skills,safety",
        "cost": "40.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Culinary Street Food Responsible Tour",
        "description": "Small-group evening tour sampling local specialties with hygiene-conscious vendors and allergy-aware guidance.",
        "tags": "food,tour,streetfood,culinary",
        "cost": "20.00",
        "duration": 2.5,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Chandragiri Cable Car + Short Hike",
        "description": "Cable car ride with a short ridge walk and picnic; seasonal winds may affect operations.",
        "tags": "cablecar,hike,viewpoint,nature",
        "cost": "25.00",
        "duration": 3.0,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Photography & Conservation Walk",
        "description": "Guided nature photography walk focusing on respectful wildlife and habitat viewing practices.",
        "tags": "photography,nature,conservation,walking",
        "cost": "12.00",
        "duration": 2.5,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Evening Cultural Dance Show & Workshop",
        "description": "Attend a short traditional dance performance followed by a participatory workshop run by local performers.",
        "tags": "culture,dance,performance,workshop",
        "cost": "10.00",
        "duration": 2.0,
        "indoor": True,
        "family_friendly": True,
    },
    {
        "name": "Responsible Volunteer Half-Day Experience",
        "description": "Half-day volunteering with a registered local NGO (education, clean-up projects) — pre-book and check requirements.",
        "tags": "volunteer,community,responsible,learning",
        "cost": "0.00",
        "duration": 4.0,
        "indoor": False,
        "family_friendly": True,
    },
]

POKHARA_ACTIVITIES = [
    {
        "name": "Tandem Paragliding from Sarangkot",
        "description": "World-famous tandem paragliding flights (weather dependent) with certified pilots; ideal for sunrise flights.",
        "tags": "paragliding,adrenaline,sky,seasonal",
        "cost": "85.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Seasonal Hot Air Balloon (Lake & Mountain Views)",
        "description": "Occasional hot-air balloon operations over the Pokhara valley in clear-season windows; book early and follow safety briefings.",
        "tags": "hotairballoon,seasonal,scenic,photography",
        "cost": "220.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Kusma (Khimti) Bungee & Canyon Swing",
        "description": "Nearby bungee jump and canyon swings for adrenaline seekers; operator safety certifications recommended.",
        "tags": "bungee,adrenaline,seasonal,thrill",
        "cost": "120.00",
        "duration": 1.5,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Seti/Trishuli Day White-Water Rafting",
        "description": "Full-day or half-day rafting options on nearby rivers; choose grade and operator according to experience and safety briefings.",
        "tags": "rafting,water,adventure,river",
        "cost": "60.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Zipline & Canopy Adventure",
        "description": "High-elevation zipline runs above forested valleys; seasonal weather restrictions apply.",
        "tags": "zipline,adrenaline,forest,seasonal",
        "cost": "45.00",
        "duration": 2.0,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Seasonal Skydiving Festival (Tandem)",
        "description": "Occasional tandem skydiving drop zones for certified operators during good-weather festival windows; book well in advance.",
        "tags": "skydiving,seasonal,tandem,adrenaline",
        "cost": "300.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Motorbike Rental & Off-Road Annapurna Foothills Tour",
        "description": "Daily motorbike rentals and guided off-road loops on maintained trails; safety gear and local license required.",
        "tags": "motorbike,rental,offroad,tour",
        "cost": "35.00",
        "duration": 6.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Lake Boat Rental & Sunset Cruise",
        "description": "Private or shared boat rentals on Phewa Lake with options for sunset photography and gentle paddling.",
        "tags": "boat,relax,photography,romantic",
        "cost": "12.00",
        "duration": 1.5,
        "indoor": False,
        "family_friendly": True,
    },
    {
        "name": "Mountain Biking Trails Around Begnas & Phewa",
        "description": "Guided single-day mountain-biking on designated trails around Pokhara's lakes and foothills.",
        "tags": "biking,offroad,adventure,nature",
        "cost": "40.00",
        "duration": 5.0,
        "indoor": False,
        "family_friendly": False,
    },
    {
        "name": "Caving & Gupteshwor Exploration",
        "description": "Guided exploration of Gupteshwor and nearby caves with responsible lighting and conservation-aware practices.",
        "tags": "caving,adventure,nature,conservation",
        "cost": "10.00",
        "duration": 1.0,
        "indoor": False,
        "family_friendly": True,
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
