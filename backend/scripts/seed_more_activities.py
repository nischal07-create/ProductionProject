"""Seed additional activities for cities like Chitwan, Lumbini, Ilam, Janakpur, Gorkha, Mustang, Rara, Bandipur.
Run with: python manage.py runscript seed_more_activities  OR: python scripts/seed_more_activities.py (from backend folder)
This script uses Django ORM when run via manage.py shell or as a runscript.
"""

if __name__ == '__main__':
    # Support running standalone via django.setup()
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

from trips.models import Destination, Activity

ADDITIONAL_ACTIVITIES = [
    # Chitwan
    ("Chitwan", "Jungle Safari (Chitwan National Park)", "Half-day jeep or open-vehicle safari to spot rhinos, deer and birds.", "wildlife, safari, nature, family", 2000, 4.0),
    ("Chitwan", "Tharu Cultural Village & Dance Show", "Evening cultural performance and village visit with Tharu hosts.", "culture, heritage, food", 900, 2.0),
    ("Chitwan", "Canoe Ride on Rapti River", "Guided canoe trip with birdwatching and riverbank wildlife viewing.", "water, wildlife, boat", 1500, 2.0),
    # Lumbini
    ("Lumbini", "Monastic Circuit & Meditation Session", "Visit Maya Devi Temple, monastery circuit and join a guided meditation.", "spiritual, heritage, meditation", 500, 2.0),
    ("Lumbini", "Bicycle Tour of Sacred Sites", "Easy cycling tour covering ruins, monasteries and museum sites.", "bike, culture, heritage", 800, 3.0),
    ("Lumbini", "Pilgrim Guided Walk with Local Guide", "Learn about Buddhist history with a certified local guide.", "history, guided, culture", 1200, 3.0),
    # Ilam
    ("Ilam", "Tea Estate Walk & Tasting", "Walk through rolling tea gardens and sample estate teas.", "nature, food, walking", 700, 2.0),
    ("Ilam", "Viewpoint Sunrise Hike", "Short early-morning hike to panoramic viewpoints over hills and tea terraces.", "hiking, viewpoint, sunrise", 800, 3.0),
    # Janakpur
    ("Janakpur", "Janaki Temple Pilgrimage & Cultural Tour", "Explore the temple, local crafts and Mithila painting demonstrations.", "spiritual, culture, heritage", 600, 2.0),
    # Gorkha
    ("Gorkha", "Gorkha Durbar Fort Visit & Short Hike", "Historical fort visit with short walk and scenic views.", "history, hiking, viewpoint", 700, 3.0),
    # Mustang region (lower tourist season activities)
    ("Mustang", "Lower Mustang Cultural Day Tour", "Village visits, ancient gompas and local hospitality.", "culture, trekking, heritage", 2000, 5.0),
    ("Mustang", "Muktinath Pilgrimage Day Trip", "Guided visit to the sacred Muktinath site (seasonal).", "spiritual, pilgrimage, guided", 2500, 6.0),
    # Rara
    ("Rara", "Rara Lake day hike & picnic", "Scenic lake walk with picnic and photography stops.", "nature, hiking, viewpoint", 1200, 4.0),
    # Bandipur
    ("Bandipur", "Heritage Town Walk & Newari Feast", "Guided town walk with a traditional Newari meal.", "heritage, food, walking", 900, 3.0),
]


def seed():
    created = []
    for city, name, desc, tags, cost, dur in ADDITIONAL_ACTIVITIES:
        dest, _ = Destination.objects.get_or_create(name=city)
        act, created_flag = Activity.objects.get_or_create(
            destination=dest,
            name=name,
            defaults={
                'description': desc,
                'tags': tags,
                'cost_estimate': cost,
                'duration_hours': dur,
            },
        )
        if created_flag:
            created.append((city, name))
    print(f"Seed complete, created={len(created)}")


if __name__ == '__main__':
    seed()
