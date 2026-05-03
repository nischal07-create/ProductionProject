#!/usr/bin/env python
"""Verification script for activity and trekking route updates."""

import os
import sys
from pathlib import Path
import json

import django

BASE_DIR = Path(__file__).resolve().parents[0]
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.chdir(BASE_DIR)
sys.path.insert(0, str(BASE_DIR))
django.setup()

from trips.models import Activity, Destination
from trips.trekking_catalog import TREKKING_ROUTES

def verify_activities():
    """Verify all activities have pricing and photos."""
    print("=" * 80)
    print("ACTIVITY VERIFICATION REPORT")
    print("=" * 80)
    
    activities = Activity.objects.all().select_related('destination')
    
    print(f"\nTotal Activities: {activities.count()}\n")
    
    kathmandu = Destination.objects.filter(name="Kathmandu").first()
    pokhara = Destination.objects.filter(name="Pokhara").first()
    
    if kathmandu:
        kat_activities = kathmandu.activities.all()
        print(f"\nKATHMANDU ACTIVITIES ({kat_activities.count()}):")
        print("-" * 80)
        for activity in kat_activities:
            photo_count = len(activity.photo_urls) if activity.photo_urls else 0
            print(f"  • {activity.name}")
            print(f"    Price: ${activity.cost_estimate} USD")
            print(f"    Duration: {activity.duration_hours} hours")
            print(f"    Photos: {photo_count}")
            if activity.photo_urls:
                for i, photo in enumerate(activity.photo_urls, 1):
                    print(f"      {i}. {photo}")
            print()
    
    if pokhara:
        pok_activities = pokhara.activities.all()
        print(f"\nPOKHARA ACTIVITIES ({pok_activities.count()}):")
        print("-" * 80)
        for activity in pok_activities:
            photo_count = len(activity.photo_urls) if activity.photo_urls else 0
            print(f"  • {activity.name}")
            print(f"    Price: ${activity.cost_estimate} USD")
            print(f"    Duration: {activity.duration_hours} hours")
            print(f"    Photos: {photo_count}")
            if activity.photo_urls and "Hot Air Balloon" in activity.name:
                print(f"    Photos for Hot Air Balloon:")
                for i, photo in enumerate(activity.photo_urls, 1):
                    print(f"      {i}. {photo}")
            print()

def verify_trekking_routes():
    """Verify all trekking routes have pricing."""
    print("\n" + "=" * 80)
    print("TREKKING ROUTES VERIFICATION REPORT")
    print("=" * 80)
    
    print(f"\nTotal Trekking Routes: {len(TREKKING_ROUTES)}\n")
    
    for route_id, route_data in TREKKING_ROUTES.items():
        price_usd = route_data.get('price_usd', 'NOT SET')
        price_npr = route_data.get('price_npr', 'NOT SET')
        difficulty = route_data.get('difficulty', 'N/A')
        duration = route_data.get('duration_days', 'N/A')
        
        print(f"  • {route_data['name']}")
        print(f"    Route ID: {route_id}")
        print(f"    Difficulty: {difficulty} | Duration: {duration} days")
        print(f"    Price: ${price_usd} USD | ₨{price_npr} NPR")
        print()

def verify_api_response():
    """Verify API serializer includes photo_urls."""
    print("\n" + "=" * 80)
    print("API RESPONSE VERIFICATION")
    print("=" * 80)
    
    from trips.views import ActivitySerializer
    
    # Get a sample activity with photos
    sample = Activity.objects.filter(photo_urls__isnull=False).exclude(photo_urls=[]).first()
    
    if sample:
        print(f"\nSample Activity: {sample.name}")
        serializer = ActivitySerializer(sample)
        response_data = serializer.data
        
        print(f"\nSerialized Data:")
        print(json.dumps(response_data, indent=2))
    else:
        print("No activities with photos found!")

if __name__ == "__main__":
    verify_activities()
    verify_trekking_routes()
    verify_api_response()
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
