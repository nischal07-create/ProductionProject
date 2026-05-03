#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from trips.models import Activity

# Mapping of activity IDs to actual image files that exist in the places folder.
# These are chosen to be visually distinct so each activity card shows a different image.
activity_photo_mapping = {
    1: ["/static/core/photos/places/kathmandu/kathmandu-durbar-square.jpg"],
    2: ["/static/core/photos/places/kathmandu/bhaktapur-durbar-square.jpg", "/static/core/photos/places/kathmandu/patan-durbar-square.jpg", "/static/core/photos/places/kathmandu/boudhanath-stupa.jpg"],
    3: ["/static/core/photos/places/kathmandu/shivapuri-national-park-nagi-gumba-trail.jpg", "/static/core/photos/places/kathmandu/dhulikhel-historic-town.jpg", "/static/core/photos/places/kathmandu/nagarkot-sunrise-viewpoint.jpg"],
    4: ["/static/core/photos/places/kathmandu/nagarkot-sunrise-viewpoint.jpg", "/static/core/photos/places/kathmandu/swayambhunath-stupa-monkey-temple.jpg"],
    5: ["/static/core/photos/places/kathmandu/thamel-nightlife-district.jpg", "/static/core/photos/places/kathmandu/asan-bazaar.jpg"],
    6: ["/static/core/photos/places/kathmandu/chandragiri-hills.jpg", "/static/core/photos/places/kathmandu/tokha-shiva-temple.jpg", "/static/core/photos/places/kathmandu/budhanilkantha-temple.jpg"],
    7: ["/static/core/photos/places/kathmandu/kathmandu-street-food-tour.jpg", "/static/core/photos/places/kathmandu/asan-bazaar.jpg", "/static/core/photos/places/kathmandu/thamel-nightlife-district.jpg"],
    8: ["/static/core/photos/places/kathmandu/chandragiri-hills.jpg", "/static/core/photos/places/kathmandu/dhulikhel-historic-town.jpg"],
    9: ["/static/core/photos/places/kathmandu/pashupatinath-temple.jpg", "/static/core/photos/places/kathmandu/boudhanath-stupa.jpg", "/static/core/photos/places/kathmandu/narayanhiti-palace-museum.jpg"],
    10: ["/static/core/photos/places/kathmandu/indra-jatra-festival-street.jpg", "/static/core/photos/places/kathmandu/taumadhi-square-bhaktapur.jpg", "/static/core/photos/places/kathmandu/bhaktapur-pottery-square.jpg"],
    11: ["/static/core/photos/places/kathmandu/garden-of-dreams.jpg", "/static/core/photos/places/kathmandu/national-museum-of-nepal.jpg"],
    12: ["/static/core/photos/places/pokhara/sarangkot.jpg", "/static/core/photos/places/pokhara/australian-camp-hike.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],
    13: ["/static/core/photos/places/pokhara/phewa-lake.jpg", "/static/core/photos/places/pokhara/sarangkot.jpg", "/static/core/photos/places/pokhara/world-peace-pagoda.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg", "/static/core/photos/places/pokhara/naudanda-viewpoint.jpg"],
    14: ["/static/core/photos/places/pokhara/world-peace-pagoda.jpg", "/static/core/photos/places/pokhara/pumdikot-shiva-statue.jpg", "/static/core/photos/places/pokhara/begnas-lake.jpg"],
    15: ["/static/core/photos/places/pokhara/begnas-lake.jpg", "/static/core/photos/places/pokhara/damside-pokhara.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg"],
    16: ["/static/core/photos/places/pokhara/australian-camp-hike.jpg", "/static/core/photos/places/pokhara/annapurna-foothills-trek.jpg"],
    17: ["/static/core/photos/places/pokhara/sarangkot.jpg", "/static/core/photos/places/pokhara/naudanda-viewpoint.jpg", "/static/core/photos/places/pokhara/phewa-lake.jpg"],
    18: ["/static/core/photos/places/pokhara/lakeside-pokhara.jpg", "/static/core/photos/places/pokhara/damside-pokhara.jpg", "/static/core/photos/places/pokhara/pokhara-museum.jpg"],
    19: ["/static/core/photos/places/pokhara/phewa-lake.jpg", "/static/core/photos/places/pokhara/barahi-temple.jpg", "/static/core/photos/places/pokhara/lakeside-pokhara.jpg"],
    20: ["/static/core/photos/places/pokhara/begnas-lake.jpg", "/static/core/photos/places/pokhara/rupa-lake.jpg", "/static/core/photos/places/pokhara/australian-camp-hike.jpg"],
    21: ["/static/core/photos/places/pokhara/gupteshwor-temple-cave.jpg", "/static/core/photos/places/pokhara/mahendra-caves.jpg", "/static/core/photos/places/pokhara/bat-cave.jpg"],
    22: ["/static/core/photos/places/chitwan/chitwan-national-park-safari.jpg", "/static/core/photos/places/chitwan/jungle-jeep-safari.jpg", "/static/core/photos/places/chitwan/elephant-breeding-center.jpg"],
    23: ["/static/core/photos/places/chitwan/tharu-cultural-museum.jpg", "/static/core/photos/places/chitwan/tharu-stick-dance-performance.jpg", "/static/core/photos/places/chitwan/sauraha-village-walk.jpg"],
    24: ["/static/core/photos/places/chitwan/canoe-safari.jpg", "/static/core/photos/places/chitwan/rapti-river-sunset.jpg", "/static/core/photos/places/chitwan/swimming-at-rapti-beach.jpg"],
    25: ["/static/core/photos/places/lumbini/buddhist-park-meditation.jpg", "/static/core/photos/places/lumbini/lumbini-monastic-zone.jpg", "/static/core/photos/places/lumbini/thai-monastery.jpg"],
    26: ["/static/core/photos/places/lumbini/lumbini-garden-walking-tour.jpg", "/static/core/photos/places/lumbini/sacred-lake-puskarini-pond.jpg", "/static/core/photos/places/lumbini/ashoka-pillar.jpg"],
    27: ["/static/core/photos/places/lumbini/maya-devi-temple.jpg", "/static/core/photos/places/lumbini/buddhist-park-meditation.jpg", "/static/core/photos/places/lumbini/lumbini-museum.jpg"],
    28: ["/static/core/photos/places/ilam/kanyam-tea-garden.jpg", "/static/core/photos/places/ilam/ilam-bazaar.jpg", "/static/core/photos/places/ilam/antu-danda-sunrise-point.jpg"],
    29: ["/static/core/photos/places/janakpur/janaki-mandir.jpg", "/static/core/photos/places/janakpur/ram-sita-vivah-mandap.jpg", "/static/core/photos/places/janakpur/mithila-art-gallery.jpg"],
    30: ["/static/core/photos/places/janakpur/janaki-mandir.jpg", "/static/core/photos/places/janakpur/janakpur-market-street.jpg", "/static/core/photos/places/janakpur/ram-sita-vivah-mandap.jpg"],
    31: ["/static/core/photos/places/gorkha/gorkha-durbar.jpg", "/static/core/photos/places/gorkha/gorkha-museum.jpg", "/static/core/photos/places/gorkha/ligligkot-hike.jpg"],
    32: ["/static/core/photos/places/mustang/kagbeni-village.jpg", "/static/core/photos/places/mustang/jomsom-town.jpg", "/static/core/photos/places/mustang/marpha-village.jpg"],
    33: ["/static/core/photos/places/mustang/muktinath-temple.jpg", "/static/core/photos/places/mustang/jharkot-monastery.jpg", "/static/core/photos/places/mustang/dhumba-lake.jpg"],
    34: ["/static/core/photos/places/rara/rara-lake-main-shore.jpg", "/static/core/photos/places/rara/murma-top-viewpoint.jpg", "/static/core/photos/places/rara/rara-national-park-trail.jpg"],
    35: ["/static/core/photos/places/bandipur/bandipur-bazaar-street.jpg", "/static/core/photos/places/bandipur/tundikhel-viewpoint.jpg", "/static/core/photos/places/bandipur/ramkot-village-walk.jpg"],
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
