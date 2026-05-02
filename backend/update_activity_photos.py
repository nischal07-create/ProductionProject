#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from trips.models import Activity

# Mapping of activity IDs to actual image files that exist in the places folder
activity_photo_mapping = {
    1: ["/static/core/photos/places/kathmandu/kathmandu-durbar-square.jpg"],  # Heritage Walk (empty)
    2: ["/static/core/photos/places/kathmandu/kathmandu-durbar-square.jpg", "/static/core/photos/places/kathmandu/patan-durbar-square.jpg", "/static/core/photos/places/kathmandu/pashupatinath-temple.jpg"],  # Heritage Walking
    3: ["/static/core/photos/places/kathmandu/shivapuri-national-park-nagi-gumba-trail.jpg", "/static/core/photos/places/kathmandu/nagarkot-sunrise-viewpoint.jpg", "/static/core/photos/places/kathmandu/chandragiri-hills.jpg"],  # City Mountain Biking
    4: ["/static/core/photos/places/kathmandu/nagarkot-sunrise-viewpoint.jpg", "/static/core/photos/places/kathmandu/swayambhunath-stupa-monkey-temple.jpg"],  # Rooftop Yoga
    5: ["/static/core/photos/places/kathmandu/thamel-nightlife-district.jpg", "/static/core/photos/places/kathmandu/kathmandu-durbar-square.jpg"],  # Thamel Bike Rental
    6: ["/static/core/photos/places/kathmandu/chandragiri-hills.jpg", "/static/core/photos/places/kathmandu/shivapuri-national-park-nagi-gumba-trail.jpg", "/static/core/photos/places/kathmandu/swayambhunath-stupa-monkey-temple.jpg"],  # Rock Climbing
    7: ["/static/core/photos/places/kathmandu/kathmandu-street-food-tour.jpg", "/static/core/photos/places/kathmandu/thamel-nightlife-district.jpg", "/static/core/photos/places/kathmandu/asan-bazaar.jpg"],  # Street Food Tour
    8: ["/static/core/photos/places/kathmandu/chandragiri-hills.jpg", "/static/core/photos/places/kathmandu/nagarkot-sunrise-viewpoint.jpg"],  # Chandragiri Cable Car
    9: ["/static/core/photos/places/kathmandu/pashupatinath-temple.jpg", "/static/core/photos/places/kathmandu/boudhanath-stupa.jpg"],  # Photography Walk
    10: ["/static/core/photos/places/kathmandu/thamel-nightlife-district.jpg", "/static/core/photos/places/kathmandu/indra-jatra-festival-street.jpg"],  # Cultural Dance
    11: ["/static/core/photos/places/kathmandu/garden-of-dreams.jpg", "/static/core/photos/places/kathmandu/kathmandu-durbar-square.jpg"],  # Volunteer
    12: ["/static/core/photos/places/pokhara/sarangkot.jpg", "/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],  # Paragliding
    13: ["/static/core/photos/places/pokhara/phewa-lake.jpg", "/static/core/photos/places/pokhara/world-peace-pagoda.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg", "/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/sarangkot.jpg"],  # Hot Air Balloon
    14: ["/static/core/photos/places/pokhara/world-peace-pagoda.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg", "/static/core/photos/places/pokhara/lakeside-street-market.jpg"],  # Bungee
    15: ["/static/core/photos/places/pokhara/begnas-lake.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],  # Rafting
    16: ["/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],  # Zipline
    17: ["/static/core/photos/places/pokhara/sarangkot.jpg", "/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg"],  # Skydiving
    18: ["/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],  # Motorbike
    19: ["/static/core/photos/places/pokhara/lakeside-pokhara.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg"],  # Boat Sunset
    20: ["/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg", "/static/core/photos/places/pokhara/begnas-lake.jpg"],  # Mountain Biking
    21: ["/static/core/photos/places/pokhara/gupteshwor-temple-cave.jpg", "/static/core/photos/places/pokhara/bat-cave.jpg"],  # Caving
    22: ["/static/core/photos/places/chitwan/khaki-uniform-guide.jpg"],  # Jungle Safari
    23: ["/static/core/photos/places/chitwan/tharu-cultural-village.jpg"],  # Tharu Cultural Village
    24: ["/static/core/photos/places/chitwan/rapti-river-sunrise.jpg"],  # Canoe Ride
    25: ["/static/core/photos/places/lumbini/lumbini-garden.jpg"],  # Monastic Circuit
    26: ["/static/core/photos/places/lumbini/lumbini-temple.jpg"],  # Bicycle Tour
    27: ["/static/core/photos/places/lumbini/maya-devi-temple.jpg"],  # Pilgrim Walk
    28: ["/static/core/photos/places/ilam/tea-estate.jpg"],  # Tea Estate
    29: ["/static/core/photos/places/janakpur/janaki-temple.jpg"],  # Viewpoint Sunrise
    30: ["/static/core/photos/places/janakpur/janaki-temple.jpg"],  # Janaki Temple
    31: ["/static/core/photos/places/gorkha/gorkha-durbar.jpg"],  # Gorkha Durbar
    32: ["/static/core/photos/places/mustang/lower-mustang.jpg"],  # Lower Mustang
    33: ["/static/core/photos/places/mustang/muktinath.jpg"],  # Muktinath
    34: ["/static/core/photos/places/rara/rara-lake.jpg"],  # Rara Lake
    35: ["/static/core/photos/places/bandipur/bandipur-town.jpg"],  # Heritage Town Walk
}

updated_count = 0
for activity_id, photo_urls in activity_photo_mapping.items():
    try:
        activity = Activity.objects.get(id=activity_id)
        activity.photo_urls = photo_urls
        activity.save()
        print(f"✓ Updated Activity {activity_id}: {activity.name}")
        updated_count += 1
    except Activity.DoesNotExist:
        print(f"✗ Activity {activity_id} not found")
    except Exception as e:
        print(f"✗ Error updating Activity {activity_id}: {e}")

print(f"\nTotal updated: {updated_count}/{len(activity_photo_mapping)}")
