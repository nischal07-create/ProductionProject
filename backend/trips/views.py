from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Destination, Activity
from rest_framework import serializers
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import TripPlan, TripPlanActivity
from urllib.parse import quote_plus
from collections import defaultdict
from .trekking_catalog import TREKKING_ROUTES
from django.http import HttpResponse
from django.utils.text import slugify
from django.conf import settings
import json
import urllib.parse
import urllib.request
from functools import lru_cache
import os
import re


class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ["id", "name", "country"]


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = [
            "id",
            "destination",
            "name",
            "description",
            "tags",
            "cost_estimate",
            "duration_hours",
            "indoor",
            "family_friendly",
            "photo_urls",
        ]


class TripPlanSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = TripPlan
        fields = [
            "id",
            "user",
            "title",
            "destination",
            "start_date",
            "end_date",
            "budget",
            "notes",
            "created_at",
            "updated_at",
        ]


class TripPlanActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = TripPlanActivity
        fields = [
            "id",
            "trip_plan",
            "activity",
            "day_number",
            "order",
            "notes",
        ]


class DestinationListView(ListAPIView):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer
    permission_classes = [AllowAny]


class ActivityListView(ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [AllowAny]


class TripPlanListCreateView(generics.ListCreateAPIView):
    serializer_class = TripPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = TripPlan.objects.filter(user=self.request.user).select_related("destination")
        
        # Filter by destination
        destination_id = self.request.query_params.get("destination_id")
        if destination_id:
            queryset = queryset.filter(destination_id=destination_id)
        
        # Filter by start date (gte)
        start_date_from = self.request.query_params.get("start_date_from")
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        
        # Filter by end date (lte)
        start_date_to = self.request.query_params.get("start_date_to")
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        # Filter by budget (lte)
        budget_max = self.request.query_params.get("budget_max")
        if budget_max:
            queryset = queryset.filter(budget__lte=budget_max)
        
        # Filter by title (search)
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TripPlanRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TripPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TripPlan.objects.filter(user=self.request.user).select_related("destination")


class TripPlanItemListCreateView(generics.ListCreateAPIView):
    serializer_class = TripPlanActivitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_trip_plan(self):
        try:
            return TripPlan.objects.get(id=self.kwargs["plan_id"], user=self.request.user)
        except TripPlan.DoesNotExist as error:
            raise PermissionDenied("Trip plan not found or not owned by user") from error

    def get_queryset(self):
        trip_plan = self.get_trip_plan()
        return trip_plan.items.select_related("activity")

    def perform_create(self, serializer):
        trip_plan = self.get_trip_plan()
        serializer.save(trip_plan=trip_plan)


class TripPlanItemRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    serializer_class = TripPlanActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "item_id"

    def get_trip_plan(self):
        try:
            return TripPlan.objects.get(id=self.kwargs["plan_id"], user=self.request.user)
        except TripPlan.DoesNotExist as error:
            raise PermissionDenied("Trip plan not found or not owned by user") from error

    def get_queryset(self):
        trip_plan = self.get_trip_plan()
        return trip_plan.items.select_related("activity")


KATHMANDU_PLACES = [
    {
        "name": "Swayambhunath Stupa (Monkey Temple)",
        "category": "heritage",
        "best_for": ["culture", "sunset", "photography", "history"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Panoramic valley view with deep Buddhist and Hindu heritage value.",
        "famous_food_nearby": ["Momo", "Sel Roti", "Chatamari"],
        "map_query": "Swayambhunath Stupa Kathmandu",
    },
    {
        "name": "Boudhanath Stupa",
        "category": "heritage",
        "best_for": ["culture", "peaceful", "spiritual", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "One of the largest stupas in the world with vibrant Tibetan culture.",
        "famous_food_nearby": ["Thukpa", "Tingmo", "Butter Tea"],
        "map_query": "Boudhanath Stupa Kathmandu",
    },
    {
        "name": "Pashupatinath Temple",
        "category": "heritage",
        "best_for": ["culture", "history", "spiritual"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "UNESCO heritage temple and key spiritual landmark of Nepal.",
        "famous_food_nearby": ["Yomari", "Newari Khaja", "Juju Dhau"],
        "map_query": "Pashupatinath Temple Kathmandu",
    },
    {
        "name": "Kathmandu Durbar Square",
        "category": "heritage",
        "best_for": ["history", "culture", "architecture", "photography"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Historic palace square with traditional architecture and museums.",
        "famous_food_nearby": ["Samay Baji", "Bara", "Lakhamari"],
        "map_query": "Kathmandu Durbar Square",
    },
    {
        "name": "Patan Durbar Square",
        "category": "heritage",
        "best_for": ["history", "culture", "arts", "architecture"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Finest Newari craftsmanship and less crowded cultural atmosphere.",
        "famous_food_nearby": ["Momo", "Kwati", "Yomari"],
        "map_query": "Patan Durbar Square",
    },
    {
        "name": "Garden of Dreams",
        "category": "leisure",
        "best_for": ["relax", "couple", "family", "photos"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Elegant garden retreat in the center of Thamel area.",
        "famous_food_nearby": ["Mo:Mo", "Lassi", "Aloo Tama"],
        "map_query": "Garden of Dreams Kathmandu",
    },
    {
        "name": "Chandragiri Hills",
        "category": "nature",
        "best_for": ["nature", "cable car", "mountain view", "family"],
        "budget_level": "high",
        "family_friendly": True,
        "why_best": "Cable car adventure with Himalayan panorama and fresh air.",
        "famous_food_nearby": ["Grilled Trout", "Thakali Set", "Momo"],
        "map_query": "Chandragiri Hills Kathmandu",
    },
    {
        "name": "Narayanhiti Palace Museum",
        "category": "history",
        "best_for": ["history", "politics", "museum"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Royal history of Nepal in an important national museum.",
        "famous_food_nearby": ["Sekuwa", "Choila", "Aloo Achaar"],
        "map_query": "Narayanhiti Palace Museum Kathmandu",
    },
    {
        "name": "Thamel Nightlife District",
        "category": "nightlife",
        "best_for": ["clubbing", "nightlife", "food", "shopping"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Most vibrant evening zone for cafes, live music, and clubs.",
        "famous_food_nearby": ["Momo", "Sekuwa", "Thakali Set"],
        "map_query": "Thamel Kathmandu",
    },
    {
        "name": "Shivapuri National Park (Nagi Gumba Trail)",
        "category": "hiking",
        "best_for": ["hiking", "nature", "photography", "adventure"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "A clean forest hiking route with panoramic valley views.",
        "famous_food_nearby": ["Local tea", "Momo", "Snacks"],
        "map_query": "Shivapuri National Park Nagi Gumba",
    },
    {
        "name": "Nagarkot Sunrise Viewpoint",
        "category": "nature",
        "best_for": ["sunrise", "nature", "photography", "relax"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Classic Himalayan sunrise point close to Kathmandu valley.",
        "famous_food_nearby": ["Tea", "Pancake", "Local breakfast"],
        "map_query": "Nagarkot View Tower",
    },
    {
        "name": "Asan Bazaar",
        "category": "shopping",
        "best_for": ["shopping", "culture", "street-life", "food"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Authentic local market for spices, souvenirs, and street snacks.",
        "famous_food_nearby": ["Lassi", "Jeri", "Chatamari"],
        "map_query": "Asan Bazar Kathmandu",
    },
    {
        "name": "Kirtipur Old Town",
        "category": "culture",
        "best_for": ["culture", "food", "history", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Traditional Newari town with local culture and less crowd.",
        "famous_food_nearby": ["Newari Khaja", "Choila", "Aila"],
        "map_query": "Kirtipur Kathmandu",
    },
    {
        "name": "Budhanilkantha Temple",
        "category": "spiritual",
        "best_for": ["culture", "peaceful", "family", "history"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Famous reclining Vishnu statue with calm temple atmosphere.",
        "famous_food_nearby": ["Tea", "Snacks", "Momo"],
        "map_query": "Budhanilkantha Temple",
    },
    {
        "name": "Bhaktapur Durbar Square",
        "category": "heritage",
        "best_for": ["history", "culture", "pottery", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "UNESCO heritage site with preserved Newari architecture and pottery tradition.",
        "famous_food_nearby": ["Jujudhau", "Bara", "Yomari"],
        "map_query": "Bhaktapur Durbar Square",
    },
    {
        "name": "Bhaktapur Pottery Square",
        "category": "culture",
        "best_for": ["culture", "craft", "shopping", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Traditional pottery making with hands-on experience and direct purchases.",
        "famous_food_nearby": ["Chowmein", "Momo", "Tea"],
        "map_query": "Bhaktapur Pottery Square",
    },
    {
        "name": "Taumadhi Square (Bhaktapur)",
        "category": "heritage",
        "best_for": ["history", "culture", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred square with five-story pagoda in heart of old Bhaktapur.",
        "famous_food_nearby": ["Sel Roti", "Bara", "Local snacks"],
        "map_query": "Taumadhi Square Bhaktapur",
    },
    {
        "name": "Changunarayan Temple",
        "category": "heritage",
        "best_for": ["culture", "spiritual", "history", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ancient temple with intricate carvings and UNESCO heritage status.",
        "famous_food_nearby": ["Tea", "Momo", "Local snacks"],
        "map_query": "Changunarayan Temple",
    },
    {
        "name": "Dhulikhel Historic Town",
        "category": "culture",
        "best_for": ["history", "culture", "food", "shopping"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ancient Newari trading town with preserved heritage and local crafts.",
        "famous_food_nearby": ["Jhol Momo", "Bara", "Lassi"],
        "map_query": "Dhulikhel Town",
    },
    {
        "name": "Namche Bazaar Day Hike",
        "category": "hiking",
        "best_for": ["hiking", "nature", "mountain culture", "adventure"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "High-altitude cultural hike with Sherpa villages and mountain air.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Local tea"],
        "map_query": "Namche Bazaar Trek",
    },
    {
        "name": "Tokha Shiva Temple",
        "category": "spiritual",
        "best_for": ["spiritual", "peaceful", "nature", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Hilltop temple with peaceful surroundings and valley views.",
        "famous_food_nearby": ["Tea", "Snacks", "Momo"],
        "map_query": "Tokha Shiva Temple Kathmandu",
    },
    {
        "name": "Kathmandu Street Food Tour",
        "category": "nightlife",
        "best_for": ["food", "culture", "nightlife", "adventure"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Evening guided tour through street food markets with local flavors.",
        "famous_food_nearby": ["Momos", "Sekuwa", "Lassi", "Bara"],
        "map_query": "Thamel Street Food Kathmandu",
    },
    {
        "name": "National Museum of Nepal",
        "category": "history",
        "best_for": ["history", "culture", "education", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Comprehensive museum showcasing Nepal's art, history and natural heritage.",
        "famous_food_nearby": ["Tea", "Snacks", "Momo"],
        "map_query": "National Museum Nepal Kathmandu",
    },
    {
        "name": "Indra Jatra Festival Street",
        "category": "culture",
        "best_for": ["culture", "festival", "shopping", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Cultural celebration with decorations, music, and traditional customs.",
        "famous_food_nearby": ["Khichdi", "Sel Roti", "Local sweets"],
        "map_query": "Indra Jatra Festival Kathmandu",
    },
    {
        "name": "Copy Cat Bar & Nightlife",
        "category": "nightlife",
        "best_for": ["nightlife", "music", "socializing", "adventure"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Popular rooftop bar with live music and diverse travelers.",
        "famous_food_nearby": ["Pizza", "Wings", "Cocktails"],
        "map_query": "Copy Cat Bar Thamel",
    },
]


KATHMANDU_FOODS = [
    {"name": "Buff Momo", "where": "Thamel, New Road", "type": "must-try street food"},
    {"name": "Newari Khaja Set", "where": "Patan, Kirtipur", "type": "traditional"},
    {"name": "Yomari", "where": "Patan, Bhaktapur", "type": "festive sweet"},
    {"name": "Chatamari", "where": "Ason, Basantapur", "type": "Newari classic"},
    {"name": "Sekuwa", "where": "Boudha, Putalisadak", "type": "grilled favorite"},
    {"name": "Juju Dhau", "where": "Bhaktapur", "type": "bread pudding dessert"},
    {"name": "Thukpa", "where": "Boudha", "type": "Tibetan noodle soup"},
    {"name": "Street Lassi", "where": "Basantapur, Ason", "type": "yogurt drink"},
]

POKHARA_PLACES = [
    {
        "name": "Phewa Lake",
        "category": "nature",
        "best_for": ["nature", "relax", "boating", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "A peaceful lake with mountain reflections and boat rides for every tourist.",
        "famous_food_nearby": ["Momo", "Thakali Set", "Lassi"],
        "map_query": "Phewa Lake Pokhara",
    },
    {
        "name": "World Peace Pagoda",
        "category": "heritage",
        "best_for": ["sunrise", "photography", "peaceful", "nature"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Iconic hilltop pagoda with panoramic views of Pokhara and the Annapurna range.",
        "famous_food_nearby": ["Tea", "Corn", "Momo"],
        "map_query": "World Peace Pagoda Pokhara",
    },
    {
        "name": "Sarangkot",
        "category": "adventure",
        "best_for": ["sunrise", "paragliding", "mountain view", "adventure"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Best sunrise viewpoint in Pokhara and the prime paragliding takeoff spot.",
        "famous_food_nearby": ["Thakali Set", "Soup", "Tea"],
        "map_query": "Sarangkot Pokhara",
    },
    {
        "name": "Davis Falls",
        "category": "nature",
        "best_for": ["nature", "short visit", "family", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "A famous waterfall stop to pair with nearby caves and viewpoints.",
        "famous_food_nearby": ["Chowmein", "Momo", "Cold Drinks"],
        "map_query": "Davis Falls Pokhara",
    },
    {
        "name": "Bindhyabasini Temple",
        "category": "heritage",
        "best_for": ["culture", "spiritual", "family", "history"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "A sacred hilltop temple with local cultural value and calm surroundings.",
        "famous_food_nearby": ["Juju Dhau", "Sel Roti", "Tea"],
        "map_query": "Bindhyabasini Temple Pokhara",
    },
    {
        "name": "Lakeside Pokhara",
        "category": "nightlife",
        "best_for": ["clubbing", "nightlife", "food", "shopping"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Best zone for evening cafes, bars, and live music by the lake.",
        "famous_food_nearby": ["Pizza", "Momo", "Coffee"],
        "map_query": "Lakeside Pokhara",
    },
    {
        "name": "Begnas Lake",
        "category": "nature",
        "best_for": ["nature", "relax", "boating", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Calmer alternative lake for peaceful half-day exploration.",
        "famous_food_nearby": ["Fresh fish", "Momo", "Tea"],
        "map_query": "Begnas Lake Pokhara",
    },
    {
        "name": "Pumdikot Shiva Statue",
        "category": "viewpoint",
        "best_for": ["photography", "sunset", "family", "nature"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Huge Shiva statue with wide panoramic mountain and city views.",
        "famous_food_nearby": ["Tea", "Snacks", "Corn"],
        "map_query": "Pumdikot Shiva Statue Pokhara",
    },
    {
        "name": "Australian Camp Hike",
        "category": "hiking",
        "best_for": ["hiking", "nature", "sunrise", "adventure"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Short but scenic hill hike with Annapurna range views.",
        "famous_food_nearby": ["Dal Bhat", "Tea", "Noodles"],
        "map_query": "Australian Camp Dhampus",
    },
    {
        "name": "International Mountain Museum",
        "category": "history",
        "best_for": ["history", "culture", "family", "education"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Great museum about Himalayan culture and mountaineering history.",
        "famous_food_nearby": ["Tea", "Momo", "Snacks"],
        "map_query": "International Mountain Museum Pokhara",
    },
    {
        "name": "Damside Pokhara",
        "category": "culture",
        "best_for": ["shopping", "nightlife", "food", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Emerging vibrant area with modern shops, cafes, and restaurants.",
        "famous_food_nearby": ["Burger", "Pizza", "Thakali Momo"],
        "map_query": "Damside Pokhara",
    },
    {
        "name": "Rupa Lake",
        "category": "nature",
        "best_for": ["nature", "relax", "boating", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Remote and serene lake perfect for peaceful day trip.",
        "famous_food_nearby": ["Simple meals", "Tea", "Snacks"],
        "map_query": "Rupa Lake Pokhara",
    },
    {
        "name": "Mahendra Caves",
        "category": "adventure",
        "best_for": ["adventure", "nature", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ancient natural caves with historical significance and cool interior.",
        "famous_food_nearby": ["Tea", "Momo", "Snacks"],
        "map_query": "Mahendra Caves Pokhara",
    },
    {
        "name": "Annapurna Foothills Trek",
        "category": "hiking",
        "best_for": ["hiking", "nature", "mountain views", "adventure"],
        "budget_level": "high",
        "family_friendly": False,
        "why_best": "Classic trekking route with stunning Himalayan panoramas.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Tea"],
        "map_query": "Annapurna Base Camp Trek Pokhara",
    },
    {
        "name": "Barahi Temple",
        "category": "spiritual",
        "best_for": ["spiritual", "culture", "photography", "peaceful"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred Hindu temple on island in middle of Phewa Lake.",
        "famous_food_nearby": ["Tea", "Prasad", "Snacks"],
        "map_query": "Barahi Temple Phewa Lake",
    },
    {
        "name": "Poon Hill Trek",
        "category": "hiking",
        "best_for": ["hiking", "sunrise", "nature", "photography"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Short high-altitude trek with one of the best mountain sunrises.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Tea"],
        "map_query": "Poon Hill Trek Pokhara",
    },
    {
        "name": "Bat Cave",
        "category": "nature",
        "best_for": ["nature", "adventure", "family", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Interesting cave filled with thousands of bats at dusk.",
        "famous_food_nearby": ["Tea", "Momo", "Snacks"],
        "map_query": "Bat Cave Pokhara",
    },
    {
        "name": "Pokhara Museum",
        "category": "history",
        "best_for": ["history", "culture", "education", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Comprehensive museum showcasing regional history and artifacts.",
        "famous_food_nearby": ["Tea", "Snacks", "Lassi"],
        "map_query": "Pokhara Museum",
    },
    {
        "name": "Lakeside Street Market",
        "category": "shopping",
        "best_for": ["shopping", "culture", "nightlife", "food"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Evening market by the lake with handicrafts, souvenirs, and street food.",
        "famous_food_nearby": ["Momo", "Sekuwa", "Lassi"],
        "map_query": "Lakeside Street Market Pokhara",
    },
    {
        "name": "Naudanda Viewpoint",
        "category": "viewpoint",
        "best_for": ["photography", "sunset", "nature", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Hilltop viewpoint with expansive views of lakes and mountains.",
        "famous_food_nearby": ["Tea", "Snacks", "Corn"],
        "map_query": "Naudanda Viewpoint Pokhara",
    },
    {
        "name": "Gupteshwor Temple & Cave",
        "category": "spiritual",
        "best_for": ["spiritual", "adventure", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred cave temple with natural spring and mystical ambiance.",
        "famous_food_nearby": ["Tea", "Prasad", "Snacks"],
        "map_query": "Gupteshwor Temple Pokhara",
    },
]

CHITWAN_PLACES = [
    {
        "name": "Chitwan National Park Safari",
        "category": "wildlife",
        "best_for": ["wildlife", "nature", "family", "adventure"],
        "budget_level": "high",
        "family_friendly": True,
        "why_best": "Top jungle safari experience with rhino and birdwatching options.",
        "famous_food_nearby": ["Tharu Set", "Fresh fish", "Dal Bhat"],
        "map_query": "Chitwan National Park Sauraha",
    },
    {
        "name": "Rapti River Sunset",
        "category": "nature",
        "best_for": ["sunset", "photography", "relax", "couple"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Beautiful riverside sunset with calm ambiance.",
        "famous_food_nearby": ["Tea", "Snacks", "Momo"],
        "map_query": "Rapti River Sauraha",
    },
    {
        "name": "Tharu Cultural Museum",
        "category": "culture",
        "best_for": ["culture", "history", "family", "education"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Learn indigenous Tharu heritage and local lifestyle.",
        "famous_food_nearby": ["Tharu Khana", "Local snacks"],
        "map_query": "Tharu Cultural Museum Sauraha",
    },
    {
        "name": "Narayani River White Water Rafting",
        "category": "adventure",
        "best_for": ["adventure", "rafting", "nature"],
        "budget_level": "high",
        "family_friendly": False,
        "why_best": "Thrilling white-water rafting experience through jungle gorge.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Tea"],
        "map_query": "Narayani River Rafting Chitwan",
    },
    {
        "name": "Sauraha Village Walk",
        "category": "culture",
        "best_for": ["culture", "photography", "family", "food"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Guided village walk to experience local Tharu life and traditions.",
        "famous_food_nearby": ["Tharu Khana", "Homemade curry", "Local tea"],
        "map_query": "Sauraha Village Chitwan",
    },
    {
        "name": "Elephant Breeding Center",
        "category": "wildlife",
        "best_for": ["wildlife", "family", "education"],
        "budget_level": "high",
        "family_friendly": True,
        "why_best": "Conservation center with elephant rides and up-close interaction.",
        "famous_food_nearby": ["Simple meals", "Tea", "Momo"],
        "map_query": "Elephant Breeding Center Sauraha",
    },
    {
        "name": "Chitwan Sunrise Safari",
        "category": "nature",
        "best_for": ["sunrise", "wildlife", "photography", "adventure"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Early morning jungle safari with best wildlife spotting chances.",
        "famous_food_nearby": ["Breakfast", "Tea", "Simple meals"],
        "map_query": "Chitwan National Park Safari Sunrise",
    },
    {
        "name": "Narayani Eco-Lodge Stay",
        "category": "leisure",
        "best_for": ["relax", "nature", "family", "nature photography"],
        "budget_level": "high",
        "family_friendly": True,
        "why_best": "Peaceful eco-lodge experience with jungle ambiance and wildlife sounds.",
        "famous_food_nearby": ["Organic meals", "Tea", "Local snacks"],
        "map_query": "Narayani Eco Lodge Sauraha",
    },
    {
        "name": "Birdwatching Tour",
        "category": "wildlife",
        "best_for": ["wildlife", "photography", "nature", "education"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Guided birdwatching with over 400+ species in Chitwan.",
        "famous_food_nearby": ["Tea", "Snacks", "Dal Bhat"],
        "map_query": "Chitwan Birdwatching Tour",
    },
    {
        "name": "Tharu Stick Dance Performance",
        "category": "culture",
        "best_for": ["culture", "nightlife", "family", "entertainment"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Traditional Tharu martial arts and dance evening show.",
        "famous_food_nearby": ["Tharu snacks", "Local drinks", "Tea"],
        "map_query": "Tharu Stick Dance Sauraha",
    },
    {
        "name": "Kasara Wildlife Research Center",
        "category": "history",
        "best_for": ["history", "education", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Learn about wildlife conservation and research initiatives in Chitwan.",
        "famous_food_nearby": ["Tea", "Snacks", "Simple meals"],
        "map_query": "Kasara Research Center Chitwan",
    },
    {
        "name": "Jungle Jeep Safari",
        "category": "adventure",
        "best_for": ["adventure", "wildlife", "family"],
        "budget_level": "high",
        "family_friendly": True,
        "why_best": "High-speed jeep safari through dense jungle zones.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Tea"],
        "map_query": "Jungle Jeep Safari Chitwan",
    },
    {
        "name": "Swimming at Rapti Beach",
        "category": "leisure",
        "best_for": ["relax", "swimming", "family", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Seasonal river beach spot for swimming and relaxation.",
        "famous_food_nearby": ["Tea", "Snacks", "Fresh juice"],
        "map_query": "Rapti River Beach Sauraha",
    },
    {
        "name": "Canoe Safari",
        "category": "adventure",
        "best_for": ["adventure", "wildlife", "photography"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Quiet canoe ride through river channels for wildlife spotting.",
        "famous_food_nearby": ["Tea", "Snacks", "Simple meals"],
        "map_query": "Canoe Safari Rapti River Chitwan",
    },
]

CHITWAN_FOODS = [
    {"name": "Tharu Khana Set", "where": "Sauraha", "type": "traditional"},
    {"name": "Fresh River Fish", "where": "Rapti riverside", "type": "local specialty"},
    {"name": "Dal Bhat", "where": "Local lodges", "type": "budget meal"},
    {"name": "Jungle vegetables curry", "where": "Eco-lodges", "type": "fresh meal"},
]

LUMBINI_PLACES = [
    {
        "name": "Maya Devi Temple",
        "category": "spiritual",
        "best_for": ["spiritual", "history", "culture", "peaceful"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred birthplace site of Lord Buddha with deep heritage value.",
        "famous_food_nearby": ["Tea", "Simple meals", "Snacks"],
        "map_query": "Maya Devi Temple Lumbini",
    },
    {
        "name": "Lumbini Monastic Zone",
        "category": "culture",
        "best_for": ["culture", "architecture", "peaceful", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "International monasteries with unique architecture and calm gardens.",
        "famous_food_nearby": ["Vegetarian thali", "Tea"],
        "map_query": "Lumbini Monastic Zone",
    },
    {
        "name": "Lumbini Museum",
        "category": "history",
        "best_for": ["history", "education", "family", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Detailed history of Buddhism and Lumbini civilization.",
        "famous_food_nearby": ["Tea", "Snacks"],
        "map_query": "Lumbini Museum",
    },
    {
        "name": "Sacred Lake (Puskarini Pond)",
        "category": "spiritual",
        "best_for": ["spiritual", "peaceful", "family", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Holy lake where Buddha's mother bathed before giving birth.",
        "famous_food_nearby": ["Tea", "Prasad", "Snacks"],
        "map_query": "Puskarini Pond Lumbini",
    },
    {
        "name": "Ashoka Pillar",
        "category": "heritage",
        "best_for": ["history", "photography", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ancient pillar marking the birthplace of Buddha, UNESCO world heritage.",
        "famous_food_nearby": ["Tea", "Snacks"],
        "map_query": "Ashoka Pillar Lumbini",
    },
    {
        "name": "Lumbini Garden Walking Tour",
        "category": "culture",
        "best_for": ["culture", "photography", "family", "peaceful"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Guided walk through gardens with pagodas and meditation spots.",
        "famous_food_nearby": ["Tea", "Snacks", "Simple meals"],
        "map_query": "Lumbini Garden",
    },
    {
        "name": "Japanese Temple",
        "category": "architecture",
        "best_for": ["architecture", "photography", "culture", "peaceful"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Serene Japanese Buddhist temple with elegant architecture and gardens.",
        "famous_food_nearby": ["Tea", "Snacks"],
        "map_query": "Japanese Temple Lumbini",
    },
    {
        "name": "Thai Monastery",
        "category": "architecture",
        "best_for": ["architecture", "photography", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Beautiful ornate Thai-style monastery with golden decorations.",
        "famous_food_nearby": ["Thai snacks", "Tea"],
        "map_query": "Thai Monastery Lumbini",
    },
    {
        "name": "Lumbini Bazaar",
        "category": "shopping",
        "best_for": ["shopping", "culture", "food", "nightlife"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Local market with souvenirs, handicrafts, and street food.",
        "famous_food_nearby": ["Momo", "Chatamari", "Local snacks"],
        "map_query": "Lumbini Bazaar Market",
    },
    {
        "name": "Buddhist Park Meditation",
        "category": "spiritual",
        "best_for": ["spiritual", "peaceful", "meditation", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Peaceful meditation center in lush Buddhist park settings.",
        "famous_food_nearby": ["Tea", "Light meals", "Snacks"],
        "map_query": "Buddhist Park Lumbini Meditation",
    },
    # Rupandehi District additions
    {
        "name": "Tilaurakot Palace Ruins",
        "category": "heritage",
        "best_for": ["history", "archaeology", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ruins of Buddha's childhood palace with ancient fortifications.",
        "famous_food_nearby": ["Tea", "Snacks", "Dal Bhat"],
        "map_query": "Tilaurakot Palace Rupandehi",
    },
    {
        "name": "Gotihawa Cave Monastery",
        "category": "spiritual",
        "best_for": ["spiritual", "history", "adventure", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ancient cave monastery with Buddhist heritage and mountain views.",
        "famous_food_nearby": ["Tea", "Snacks", "Simple meals"],
        "map_query": "Gotihawa Cave Rupandehi",
    },
    {
        "name": "Sagarnath Cave",
        "category": "adventure",
        "best_for": ["adventure", "nature", "family", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Scenic cave with archaeological significance and natural beauty.",
        "famous_food_nearby": ["Tea", "Snacks"],
        "map_query": "Sagarnath Cave Kapilvastu",
    },
    {
        "name": "Dhumbarahi Stupa",
        "category": "spiritual",
        "best_for": ["spiritual", "culture", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic stupa with spiritual significance and peaceful surroundings.",
        "famous_food_nearby": ["Tea", "Prasad", "Snacks"],
        "map_query": "Dhumbarahi Stupa Rupandehi",
    },
    {
        "name": "Kapilavastu Museum",
        "category": "history",
        "best_for": ["history", "education", "family", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Museum showcasing artifacts and history of ancient Kapilvastu kingdom.",
        "famous_food_nearby": ["Tea", "Snacks", "Dal Bhat"],
        "map_query": "Kapilavastu Museum",
    },
    {
        "name": "Butwal City Tour",
        "category": "culture",
        "best_for": ["culture", "shopping", "food", "nightlife"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Modern city with traditional markets and cultural experiences.",
        "famous_food_nearby": ["Momo", "Chatamari", "Sekuwa"],
        "map_query": "Butwal City Rupandehi",
    },
]

LUMBINI_FOODS = [
    {"name": "Simple Veg Thali", "where": "Lumbini Bazaar", "type": "budget meal"},
    {"name": "Tea and Local Snacks", "where": "Monastic area", "type": "light refreshment"},
    {"name": "Buddhist Vegetarian Curry", "where": "Monastery restaurants", "type": "traditional meal"},
    {"name": "Fresh Momos", "where": "Lumbini Bazaar", "type": "street food"},
]

POKHARA_FOODS = [
    {"name": "Thakali Set", "where": "Lakeside, Chipledhunga", "type": "must-try main meal"},
    {"name": "Momo", "where": "Lakeside, Damside", "type": "comfort food"},
    {"name": "Tea snacks", "where": "Sarangkot, Lakeside", "type": "viewpoint snack"},
    {"name": "Fresh trout", "where": "Lakeside restaurants", "type": "signature local meal"},
    {"name": "Fewa Fish curry", "where": "Phewa village", "type": "local specialty"},
    {"name": "Nepali Thali", "where": "Local cafes", "type": "complete meal"},
]

MUSTANG_PLACES = [
    {
        "name": "Jomsom Town",
        "category": "culture",
        "best_for": ["culture", "photography", "food", "shopping"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Gateway town of Lower Mustang with mountain views and local apple products.",
        "famous_food_nearby": ["Apple pie", "Thakali set", "Local dry fruits"],
        "map_query": "Jomsom Mustang",
    },
    {
        "name": "Kagbeni Village",
        "category": "heritage",
        "best_for": ["history", "culture", "photography"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Ancient stone village at the edge of Upper Mustang with monastery heritage.",
        "famous_food_nearby": ["Barley bread", "Butter tea", "Thukpa"],
        "map_query": "Kagbeni Mustang",
    },
    {
        "name": "Muktinath Temple",
        "category": "spiritual",
        "best_for": ["spiritual", "culture", "family"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Sacred pilgrimage destination for both Hindu and Buddhist travelers.",
        "famous_food_nearby": ["Simple lodge meals", "Tea", "Dal Bhat"],
        "map_query": "Muktinath Temple",
    },
    {
        "name": "Marpha Village",
        "category": "culture",
        "best_for": ["culture", "food", "photography", "relax"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Charming white-washed Thakali village famous for apples and local brandy.",
        "famous_food_nearby": ["Apple cider", "Apple brandy", "Thakali khana"],
        "map_query": "Marpha Mustang",
    },
    {
        "name": "Dhumba Lake",
        "category": "nature",
        "best_for": ["nature", "photography", "family", "peaceful"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Quiet alpine lake with clean surroundings and short walking trail.",
        "famous_food_nearby": ["Snacks", "Tea", "Local noodles"],
        "map_query": "Dhumba Lake Mustang",
    },
    {
        "name": "Jharkot Monastery",
        "category": "history",
        "best_for": ["history", "culture", "spiritual", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic Buddhist monastery with views over the Muktinath corridor.",
        "famous_food_nearby": ["Tibetan bread", "Butter tea", "Thenthuk"],
        "map_query": "Jharkot Monastery Mustang",
    },
    {
        "name": "Jomolhari Viewpoint",
        "category": "viewpoint",
        "best_for": ["sunrise", "photography", "nature", "adventure"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Panoramic viewpoint for Nilgiri and Dhaulagiri ranges.",
        "famous_food_nearby": ["Tea", "Corn snacks", "Instant noodles"],
        "map_query": "Mustang Viewpoint Jomsom",
    },
    {
        "name": "Tatopani Mustang",
        "category": "leisure",
        "best_for": ["relax", "nature", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Natural hot spring stop after trekking and mountain drives.",
        "famous_food_nearby": ["Dal Bhat", "Momo", "Herbal tea"],
        "map_query": "Tatopani Mustang",
    },
]

MUSTANG_FOODS = [
    {"name": "Thakali Set", "where": "Jomsom, Marpha", "type": "must-try local meal"},
    {"name": "Apple Pie", "where": "Marpha bakeries", "type": "signature dessert"},
    {"name": "Tibetan Bread", "where": "Kagbeni tea houses", "type": "traditional breakfast"},
    {"name": "Butter Tea", "where": "Monastery villages", "type": "high-altitude drink"},
]

JANAKPUR_PLACES = [
    {
        "name": "Janaki Mandir",
        "category": "heritage",
        "best_for": ["history", "culture", "spiritual", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Iconic palace-style temple and the cultural heart of Janakpur.",
        "famous_food_nearby": ["Peda", "Kachori", "Jalebi"],
        "map_query": "Janaki Mandir Janakpur",
    },
    {
        "name": "Ram Sita Vivah Mandap",
        "category": "spiritual",
        "best_for": ["spiritual", "culture", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Ceremonial site linked to Ram-Sita wedding traditions.",
        "famous_food_nearby": ["Prasad", "Lassi", "Local sweets"],
        "map_query": "Vivah Mandap Janakpur",
    },
    {
        "name": "Dhanush Sagar",
        "category": "nature",
        "best_for": ["nature", "peaceful", "photography", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic pond area for evening walks and local gatherings.",
        "famous_food_nearby": ["Chaat", "Tea", "Peda"],
        "map_query": "Dhanush Sagar Janakpur",
    },
    {
        "name": "Ganga Sagar",
        "category": "culture",
        "best_for": ["culture", "photography", "relax", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Popular social and festival area surrounded by temples and local markets.",
        "famous_food_nearby": ["Street momo", "Samosa", "Sugarcane juice"],
        "map_query": "Ganga Sagar Janakpur",
    },
    {
        "name": "Janakpur Railway Heritage Zone",
        "category": "history",
        "best_for": ["history", "culture", "education"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic railway corridor with cross-border cultural significance.",
        "famous_food_nearby": ["Tea", "Pakora", "Milk sweets"],
        "map_query": "Janakpur Railway Station",
    },
    {
        "name": "Mithila Art Gallery",
        "category": "culture",
        "best_for": ["arts", "culture", "shopping", "photography"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Showcases Madhubani and Mithila art with local artisans.",
        "famous_food_nearby": ["Puri tarkari", "Lassi", "Mithai"],
        "map_query": "Mithila Art Janakpur",
    },
    {
        "name": "Ratna Sagar Park",
        "category": "leisure",
        "best_for": ["relax", "family", "nature"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Green city park suitable for families and short evening visits.",
        "famous_food_nearby": ["Corn snacks", "Tea", "Ice cream"],
        "map_query": "Ratna Sagar Janakpur",
    },
    {
        "name": "Janakpur Market Street",
        "category": "shopping",
        "best_for": ["shopping", "food", "nightlife", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Bustling local market with textiles, handicrafts, and festival goods.",
        "famous_food_nearby": ["Kachori", "Jalebi", "Mithila sweets"],
        "map_query": "Janakpur Bazaar",
    },
]

JANAKPUR_FOODS = [
    {"name": "Janakpur Peda", "where": "Near Janaki Mandir", "type": "famous sweet"},
    {"name": "Kachori Tarkari", "where": "Janakpur market", "type": "local breakfast"},
    {"name": "Mithila Thali", "where": "Traditional eateries", "type": "regional meal"},
    {"name": "Lassi", "where": "Temple area stalls", "type": "refreshing drink"},
]

ILAM_PLACES = [
    {
        "name": "Kanyam Tea Garden",
        "category": "nature",
        "best_for": ["nature", "photography", "relax", "food"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Rolling tea estates with cool weather and roadside local snacks.",
        "famous_food_nearby": ["Ilam milk tea", "Aloo chop", "Sel roti"],
        "map_query": "Kanyam Tea Garden Ilam",
    },
    {
        "name": "Antu Danda Sunrise Point",
        "category": "viewpoint",
        "best_for": ["sunrise", "nature", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Classic eastern Nepal sunrise ridge with village homestay life.",
        "famous_food_nearby": ["Chiura tarkari", "Local tea", "Corn snacks"],
        "map_query": "Antu Danda Ilam",
    },
    {
        "name": "Mai Pokhari",
        "category": "nature",
        "best_for": ["nature", "spiritual", "birdwatching", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred wetland lake with peaceful trails and cultural value.",
        "famous_food_nearby": ["Momo", "Tea", "Simple thali"],
        "map_query": "Mai Pokhari Ilam",
    },
    {
        "name": "Ilam Bazaar",
        "category": "shopping",
        "best_for": ["shopping", "food", "culture", "street-life"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Compact hill bazaar with tea shops, pickles, and street food corners.",
        "famous_food_nearby": ["Chowmein", "Aloo achar", "Fried momo"],
        "map_query": "Ilam Bazaar",
    },
    {
        "name": "Fikkal Market",
        "category": "culture",
        "best_for": ["culture", "food", "shopping", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Local trading town with strong Limbu-Rai culinary culture.",
        "famous_food_nearby": ["Tongba", "Gundruk", "Pork choila"],
        "map_query": "Fikkal Ilam",
    },
    {
        "name": "Sandakpur Trail Gate",
        "category": "hiking",
        "best_for": ["hiking", "adventure", "nature"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Gateway to high ridge trekking with broad Himalayan panorama.",
        "famous_food_nearby": ["Dal bhat", "Tea", "Noodles"],
        "map_query": "Sandakpur Ilam",
    },
]

ILAM_FOODS = [
    {"name": "Ilam Milk Tea", "where": "Kanyam, Fikkal", "type": "signature drink"},
    {"name": "Aloo Chop", "where": "Ilam bazaar stalls", "type": "must-try street food"},
    {"name": "Fried Momo", "where": "Fikkal market", "type": "street food"},
    {"name": "Tongba", "where": "Hill homestays", "type": "traditional drink"},
    {"name": "Gundruk-Dhedo", "where": "Local eateries", "type": "traditional meal"},
    {"name": "Sel Roti with Achar", "where": "Tea garden stalls", "type": "street snack"},
]

BANDIPUR_PLACES = [
    {
        "name": "Bandipur Bazaar Street",
        "category": "heritage",
        "best_for": ["culture", "architecture", "food", "shopping"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Preserved Newari town core with cafes, crafts, and mountain views.",
        "famous_food_nearby": ["Bara", "Aloo tama", "Juju dhau"],
        "map_query": "Bandipur Bazaar",
    },
    {
        "name": "Tundikhel Viewpoint",
        "category": "viewpoint",
        "best_for": ["sunrise", "sunset", "photography", "relax"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Open ridge lawn ideal for Himalaya sunrise and sunset sessions.",
        "famous_food_nearby": ["Tea", "Corn", "Momo"],
        "map_query": "Tundikhel Bandipur",
    },
    {
        "name": "Siddha Cave",
        "category": "adventure",
        "best_for": ["adventure", "nature", "hiking"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "One of Nepal's large caves with dramatic rock chambers.",
        "famous_food_nearby": ["Noodles", "Tea", "Momo"],
        "map_query": "Siddha Cave Bandipur",
    },
    {
        "name": "Khadga Devi Temple",
        "category": "spiritual",
        "best_for": ["spiritual", "culture", "history"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic hill temple visited during festivals by local communities.",
        "famous_food_nearby": ["Prasad", "Sel roti", "Tea"],
        "map_query": "Khadga Devi Temple Bandipur",
    },
    {
        "name": "Bandipur Silk Farm Trail",
        "category": "culture",
        "best_for": ["culture", "family", "education"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Hands-on local livelihood experience tied to cottage industry.",
        "famous_food_nearby": ["Chiya", "Local snacks", "Chatamari"],
        "map_query": "Bandipur Silk Farm",
    },
    {
        "name": "Ramkot Village Walk",
        "category": "hiking",
        "best_for": ["hiking", "culture", "photography", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Village trail showing Magar and Newari lifestyle side by side.",
        "famous_food_nearby": ["Dhido", "Gundruk", "Makai roti"],
        "map_query": "Ramkot Bandipur",
    },
]

BANDIPUR_FOODS = [
    {"name": "Newari Khaja", "where": "Bandipur bazaar", "type": "traditional meal"},
    {"name": "Bara and Achar", "where": "Old town lanes", "type": "street food"},
    {"name": "Sel Roti", "where": "Tea stalls", "type": "street snack"},
    {"name": "Juju Dhau", "where": "Local dairies", "type": "dessert"},
    {"name": "Makai Roti", "where": "Village homes", "type": "local breakfast"},
    {"name": "Chiya", "where": "Viewpoint kiosks", "type": "drink"},
]

GORKHA_PLACES = [
    {
        "name": "Gorkha Durbar",
        "category": "heritage",
        "best_for": ["history", "culture", "architecture", "photography"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Historic palace and fort linked to Nepal's unification history.",
        "famous_food_nearby": ["Momo", "Dal bhat", "Tea"],
        "map_query": "Gorkha Durbar",
    },
    {
        "name": "Gorakhnath Cave",
        "category": "spiritual",
        "best_for": ["spiritual", "history", "culture"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Sacred cave shrine beside Durbar with strong local faith.",
        "famous_food_nearby": ["Prasad", "Tea", "Snacks"],
        "map_query": "Gorakhnath Cave Gorkha",
    },
    {
        "name": "Gorkha Museum",
        "category": "history",
        "best_for": ["history", "education", "family"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Displays regional history, arms, and social life of old Gorkha.",
        "famous_food_nearby": ["Samosa", "Momo", "Lassi"],
        "map_query": "Gorkha Museum",
    },
    {
        "name": "Manakamana Cable Car Base",
        "category": "adventure",
        "best_for": ["adventure", "family", "spiritual"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Scenic cable car route and access to major pilgrimage area.",
        "famous_food_nearby": ["Sekuwa", "Tea", "Momo"],
        "map_query": "Manakamana Cable Car Kurintar",
    },
    {
        "name": "Ligligkot Hike",
        "category": "hiking",
        "best_for": ["hiking", "history", "adventure", "photography"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "Historic uphill trail known for old kingdom race traditions.",
        "famous_food_nearby": ["Dhido", "Local curry", "Tea"],
        "map_query": "Ligligkot Gorkha",
    },
    {
        "name": "Aarughat Riverside",
        "category": "nature",
        "best_for": ["nature", "relax", "culture", "food"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Riverside gateway town where trekkers and locals interact daily.",
        "famous_food_nearby": ["Fresh fish", "Thali", "Tea"],
        "map_query": "Aarughat Gorkha",
    },
]

GORKHA_FOODS = [
    {"name": "Gorkhali Khasi Set", "where": "Gorkha bazaar", "type": "regional meal"},
    {"name": "Makai Dhido", "where": "Village homes", "type": "traditional meal"},
    {"name": "Sekuwa", "where": "Bus park food lanes", "type": "street food"},
    {"name": "Fried Momo", "where": "Durbar route stalls", "type": "street food"},
    {"name": "Samosa and Chiya", "where": "Museum chowk", "type": "street snack"},
    {"name": "Lassi", "where": "Main market", "type": "drink"},
]

RARA_PLACES = [
    {
        "name": "Rara Lake Main Shore",
        "category": "nature",
        "best_for": ["nature", "photography", "peaceful", "family"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Nepal's largest lake with pristine alpine scenery and quiet trails.",
        "famous_food_nearby": ["Buckwheat roti", "Dal bhat", "Tea"],
        "map_query": "Rara Lake",
    },
    {
        "name": "Murma Top Viewpoint",
        "category": "hiking",
        "best_for": ["hiking", "sunrise", "photography", "adventure"],
        "budget_level": "medium",
        "family_friendly": False,
        "why_best": "High ridge climb with full-lake and mountain panoramic sweep.",
        "famous_food_nearby": ["Packed snacks", "Tea", "Noodles"],
        "map_query": "Murma Top Rara",
    },
    {
        "name": "Talcha Airport Ridge",
        "category": "viewpoint",
        "best_for": ["photography", "nature", "relax"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Scenic ridge entry point for travelers flying toward Rara zone.",
        "famous_food_nearby": ["Tea", "Momo", "Simple meals"],
        "map_query": "Talcha Airport Rara",
    },
    {
        "name": "Rara National Park Trail",
        "category": "wildlife",
        "best_for": ["wildlife", "nature", "hiking", "photography"],
        "budget_level": "medium",
        "family_friendly": True,
        "why_best": "Forest trails with rich birdlife and highland biodiversity.",
        "famous_food_nearby": ["Local thali", "Corn", "Tea"],
        "map_query": "Rara National Park",
    },
    {
        "name": "Gamgadhi Market",
        "category": "culture",
        "best_for": ["culture", "food", "shopping", "street-life"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "District town market that reflects everyday mountain livelihood.",
        "famous_food_nearby": ["Chana chat", "Momo", "Local sweets"],
        "map_query": "Gamgadhi Mugu",
    },
    {
        "name": "Jhhyari Village Homestay",
        "category": "leisure",
        "best_for": ["culture", "family", "food", "relax"],
        "budget_level": "low",
        "family_friendly": True,
        "why_best": "Local family homestay experience with mountain cuisine and stories.",
        "famous_food_nearby": ["Sisnu soup", "Dhido", "Yak butter tea"],
        "map_query": "Rara homestay village",
    },
]

RARA_FOODS = [
    {"name": "Buckwheat Roti", "where": "Rara homestays", "type": "traditional meal"},
    {"name": "Sisnu Soup", "where": "Village kitchens", "type": "local specialty"},
    {"name": "Lake Trout Curry", "where": "Lake lodges", "type": "specialty meal"},
    {"name": "Yak Butter Tea", "where": "Highland tea houses", "type": "traditional drink"},
    {"name": "Chana Chat", "where": "Gamgadhi market", "type": "street food"},
    {"name": "Fried Momo", "where": "Talcha and market stalls", "type": "street food"},
]

CITY_GUIDES = {
    "kathmandu": {
        "display_name": "Kathmandu",
        "tagline": "AI-based smart guide for culture, food, and map navigation",
        "places": KATHMANDU_PLACES,
        "foods": KATHMANDU_FOODS,
        "default_interests": ["culture", "food", "nature", "hiking", "nightlife"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Kathmandu+Tourist+Attractions",
    },
    "pokhara": {
        "display_name": "Pokhara",
        "tagline": "AI-based smart guide for lakes, sunrise, food, and adventure",
        "places": POKHARA_PLACES,
        "foods": POKHARA_FOODS,
        "default_interests": ["nature", "photography", "adventure"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Pokhara+Tourist+Attractions",
    },
    "chitwan": {
        "display_name": "Chitwan",
        "tagline": "AI-based wildlife and cultural guide with safe transport planning",
        "places": CHITWAN_PLACES,
        "foods": CHITWAN_FOODS,
        "default_interests": ["wildlife", "nature", "culture"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Chitwan+Tourist+Attractions",
    },
    "lumbini": {
        "display_name": "Lumbini",
        "tagline": "AI-based peaceful heritage guide for spiritual and cultural travel",
        "places": LUMBINI_PLACES,
        "foods": LUMBINI_FOODS,
        "default_interests": ["spiritual", "culture", "history"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Lumbini+Tourist+Attractions",
    },
    "mustang": {
        "display_name": "Mustang",
        "tagline": "AI-based mountain culture guide for remote Himalayan travel",
        "places": MUSTANG_PLACES,
        "foods": MUSTANG_FOODS,
        "default_interests": ["nature", "culture", "spiritual", "hiking"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Mustang+Tourist+Attractions",
    },
    "janakpur": {
        "display_name": "Janakpur",
        "tagline": "AI-based heritage and Mithila culture guide with spiritual highlights",
        "places": JANAKPUR_PLACES,
        "foods": JANAKPUR_FOODS,
        "default_interests": ["culture", "spiritual", "history", "food"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Janakpur+Tourist+Attractions",
    },
    "ilam": {
        "display_name": "Ilam",
        "tagline": "AI-based tea-hill and food lane guide with sunrise and village life",
        "places": ILAM_PLACES,
        "foods": ILAM_FOODS,
        "default_interests": ["nature", "food", "culture", "photography"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Ilam+Tourist+Attractions",
    },
    "bandipur": {
        "display_name": "Bandipur",
        "tagline": "AI-based heritage town guide with Newari food and ridge viewpoints",
        "places": BANDIPUR_PLACES,
        "foods": BANDIPUR_FOODS,
        "default_interests": ["culture", "food", "heritage", "sunrise"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Bandipur+Tourist+Attractions",
    },
    "gorkha": {
        "display_name": "Gorkha",
        "tagline": "AI-based royal history and mountain culture guide with local food circuits",
        "places": GORKHA_PLACES,
        "foods": GORKHA_FOODS,
        "default_interests": ["history", "culture", "hiking", "food"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Gorkha+Tourist+Attractions",
    },
    "rara": {
        "display_name": "Rara",
        "tagline": "AI-based alpine lake guide with highland lifestyle and wilderness experiences",
        "places": RARA_PLACES,
        "foods": RARA_FOODS,
        "default_interests": ["nature", "wildlife", "hiking", "culture"],
        "map_url": "https://www.google.com/maps/search/?api=1&query=Rara+Lake+Tourism",
    },
}


CITY_PROFILES = {
    "kathmandu": {
        "lifestyle": "Fast-paced valley life mixing old Newari neighborhoods, modern cafes, and evening bazaars.",
        "main_activities": ["Heritage walks", "Temple visits", "Street food crawl", "Evening cultural markets"],
        "street_food_scene": ["Momo lanes in Thamel", "Ason chatamari stalls", "New Road lassi and sel roti"],
        "local_connect_tips": ["Start greetings with 'Namaste'.", "Remove shoes before entering temples.", "Respect queue culture in busy shrines."],
    },
    "pokhara": {
        "lifestyle": "Relaxed lakeside rhythm with adventure sports by day and cafe music at night.",
        "main_activities": ["Boating and lakeside cycling", "Paragliding", "Sunrise viewpoint runs", "Live music cafes"],
        "street_food_scene": ["Lakeside momo corners", "Damside grilled snacks", "Night market tea stalls"],
        "local_connect_tips": ["Bargain politely in souvenir lanes.", "Carry a light layer for evening lake breeze.", "Use local boats with lifejackets."],
    },
    "chitwan": {
        "lifestyle": "Jungle-edge town life with Tharu community culture and early-start safari routines.",
        "main_activities": ["Jeep and canoe safari", "Village culture walk", "Birdwatching", "River sunset"],
        "street_food_scene": ["Sauraha grilled fish", "Tharu snack stalls", "Riverside tea and spicy chat"],
        "local_connect_tips": ["Follow park guide rules strictly.", "Avoid loud behavior near wildlife zones.", "Prefer local Tharu-run food houses."],
    },
    "lumbini": {
        "lifestyle": "Calm spiritual environment centered around monasteries, meditation, and slow travel.",
        "main_activities": ["Monastery circuit", "Meditation sessions", "Heritage museum visit", "Cycle around sacred garden"],
        "street_food_scene": ["Bazaar momos", "Simple veg thali shops", "Monastic tea kiosks"],
        "local_connect_tips": ["Dress modestly around sacred zones.", "Keep phone on silent in monasteries.", "Use bicycles for eco-friendly local travel."],
    },
    "mustang": {
        "lifestyle": "High-altitude desert culture with Tibetan-influenced settlements and tea-house hospitality.",
        "main_activities": ["Village monastery visits", "Desert valley drives", "Short acclimatization hikes", "Apple product tasting"],
        "street_food_scene": ["Marpha apple snacks", "Jomsom thakali set houses", "Tea-house thenthuk"],
        "local_connect_tips": ["Hydrate often for altitude comfort.", "Carry cash due to sparse ATMs.", "Ask before photographing local rituals."],
    },
    "janakpur": {
        "lifestyle": "Devotional city life shaped by temple festivals, Mithila art, and vibrant bazaar culture.",
        "main_activities": ["Temple circuit", "Mithila art exploration", "Festival street visits", "Traditional sweet tasting"],
        "street_food_scene": ["Kachori-jalebi morning lanes", "Temple-side lassi", "Evening mithai stalls"],
        "local_connect_tips": ["Visit temples in morning for smoother crowd flow.", "Support women-led Mithila art shops.", "Ask locals about festival dates for deeper experience."],
    },
    "ilam": {
        "lifestyle": "Tea-hill lifestyle with early farm mornings, calm afternoons, and warm local tea culture.",
        "main_activities": ["Tea garden walks", "Sunrise at Antu", "Village market visits", "Tea tasting"],
        "street_food_scene": ["Aloo chop stalls", "Tea garden sel roti", "Fikkal fried momo"],
        "local_connect_tips": ["Carry rain protection for hill weather shifts.", "Try local tea in small family stalls.", "Use homestays to learn regional culture."],
    },
    "bandipur": {
        "lifestyle": "Car-free heritage town life where evenings revolve around chowk cafes and mountain sunsets.",
        "main_activities": ["Old town heritage walk", "Cave exploration", "Village ridge hikes", "Local craft shopping"],
        "street_food_scene": ["Bara stalls", "Sel roti vendors", "Tea and seasonal corn kiosks"],
        "local_connect_tips": ["Walk the town slowly to enjoy architecture details.", "Support local craft stores directly.", "Respect quiet hours in homestay neighborhoods."],
    },
    "gorkha": {
        "lifestyle": "Hill-town lifestyle rooted in royal history, pilgrimage routes, and market-led daily rhythm.",
        "main_activities": ["Durbar heritage tour", "Temple-cave visit", "Historic ridge hike", "Market food circuit"],
        "street_food_scene": ["Sekuwa lanes", "Museum chowk samosa", "Durbar route tea-momo spots"],
        "local_connect_tips": ["Start early for Durbar stair climbs.", "Talk to local guides for history context.", "Pair temple visits with local food lanes."],
    },
    "rara": {
        "lifestyle": "Remote highland lifestyle with lake-focused routine, subsistence farming, and community homestays.",
        "main_activities": ["Lake loop walk", "Murma top hike", "National park trail", "Homestay cultural evenings"],
        "street_food_scene": ["Gamgadhi chat corners", "Talcha momo stalls", "Highland tea houses"],
        "local_connect_tips": ["Plan buffer days for weather-related delays.", "Carry warm layers even in shoulder seasons.", "Buy local produce to support remote economies."],
    },
}


def _budget_tier(budget_npr):
    if budget_npr <= 2000:
        return "low"
    if budget_npr <= 6000:
        return "medium"
    return "high"


def _place_score(place, interests, budget_level, family_mode):
    interest_hits = len(set(interests).intersection(set(place["best_for"])))
    budget_score = 2 if place["budget_level"] == budget_level else 1
    family_score = 2 if (not family_mode or place["family_friendly"]) else 0
    return interest_hits * 3 + budget_score + family_score


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_list(value):
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip().lower() for item in value.split(",") if item.strip()]
    return [str(item).strip().lower() for item in value if str(item).strip()]


def _activity_type_label(activity):
    text = " ".join(
        [
            str(activity.name or ""),
            str(activity.description or ""),
            str(activity.tags or ""),
        ]
    ).lower()

    if any(keyword in text for keyword in ["paragliding", "skydiving", "hot air balloon", "hot-air balloon"]):
        return "Air Adventure"
    if any(keyword in text for keyword in ["bungee", "zipline", "rock climbing", "climbing", "off-road", "offroad"]):
        return "Extreme Adventure"
    if any(keyword in text for keyword in ["rafting", "canoe", "kayak", "river"]):
        return "Water Adventure"
    if any(keyword in text for keyword in ["bike", "biking", "motorbike", "cycling"]):
        return "Ride & Trail"
    if any(keyword in text for keyword in ["yoga", "wellness", "sunrise", "meditation"]):
        return "Wellness"
    if any(keyword in text for keyword in ["food", "culinary", "street food", "food tour"]):
        return "Food Experience"
    if any(keyword in text for keyword in ["heritage", "culture", "dance", "craft"]):
        return "Cultural Experience"
    return "Local Experience"


def _serialize_city_activities(city_key, interests=None, focus_activities=None):
    guide = CITY_GUIDES.get(city_key)
    if not guide:
        return []

    city_name = guide.get("display_name", city_key.title())
    queryset = Activity.objects.filter(destination__name__iexact=city_name).select_related("destination")

    interest_terms = set(_normalize_list(interests)) | set(_normalize_list(focus_activities))
    serialized = []

    for activity in queryset:
        tags = [tag.strip() for tag in (activity.tags or "").split(",") if tag.strip()]
        activity_terms = set(tag.lower() for tag in tags)
        search_blob = f"{activity.name} {activity.description} {activity.tags}".lower()
        score = len(interest_terms.intersection(activity_terms)) * 3
        if any(term in search_blob for term in interest_terms):
            score += 2
        if any(term in activity_terms for term in {"adventure", "seasonal"}):
            score += 1

        if any(term in activity_terms for term in {"paragliding", "skydiving", "bungee", "zipline", "rafting", "offroad", "bike", "climbing"}):
            best_time = "Best in clear weather"
        elif any(term in activity_terms for term in {"sunrise", "lake", "heritage", "culture"}):
            best_time = "Best in the morning or early afternoon"
        else:
            best_time = "Best for a flexible half-day plan"

        if "seasonal" in search_blob:
            recommendation_note = "Seasonal experience - check weather and booking window before travel."
        elif activity.family_friendly:
            recommendation_note = "Family-friendly and easy to slot into a city day plan."
        else:
            recommendation_note = "Plan this as a focused activity block with enough buffer time."

        serialized.append(
            {
                "name": activity.name,
                "type": _activity_type_label(activity),
                "description": activity.description,
                "destination": city_name,
                "photo_url": _activity_photo_url(activity, city_key),
                "cost_estimate": float(activity.cost_estimate),
                "duration_hours": float(activity.duration_hours),
                "indoor": activity.indoor,
                "family_friendly": activity.family_friendly,
                "tags": tags,
                "seasonal": any(word in search_blob for word in ["seasonal", "weather dependent", "weather-dependent", "best season"]),
                "adventure_level": "High" if any(word in search_blob for word in ["bungee", "skydiving", "paragliding", "zipline", "rafting", "off-road", "offroad"]) else ("Medium" if "adventure" in activity_terms else "Low"),
                "best_time": best_time,
                "recommendation_note": recommendation_note,
                "safety_note": "Check weather, operator certification, and safety gear before booking.",
                "map_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(activity.name + ' ' + city_name)}",
                "match_score": score,
                # Fare and booking details
                "exact_fare_npr": (int(round(float(activity.cost_estimate))) if activity.cost_estimate and float(activity.cost_estimate) > 0 else None),
                "estimated_fare_npr": (int(round(float(activity.cost_estimate))) if activity.cost_estimate and float(activity.cost_estimate) > 0 else None),
                "estimated_fare_range": (None if activity.cost_estimate and float(activity.cost_estimate) > 0 else _category_price_band(None)),
                "booking_tip": None,
                "operator_suggestion": None,
                "included_items": [],
                "booking_lead_time_days": None,
            }
        )

    ordered = sorted(serialized, key=lambda item: (-item["match_score"], item["name"]))
    for item in ordered:
        item.pop("match_score", None)
        # enrich booking advice and inferred safety/booking fields
        typ = (item.get("type") or "").lower()
        tags_lc = " ".join([t.lower() for t in (item.get("tags") or [])])
        # default operator suggestion
        item["operator_suggestion"] = "Contact local licensed operators; confirm price and safety certification."
        # booking lead time defaults
        if "air" in typ or "paragliding" in tags_lc or "hotair" in tags_lc or "hot air" in (item.get("name") or "").lower():
            item["booking_tip"] = "Weather-dependent. Book at least 3-7 days in advance and confirm fly windows."
            item["included_items"] = ["Safety briefing", "Pilot and crew", "Passenger harnesses"]
            item["booking_lead_time_days"] = 7
            # hot-air-balloon specifics where relevant
            if "hotair" in tags_lc or "hot air" in (item.get("name") or "").lower():
                item["flight_altitude_m"] = 300
                item["flight_duration_min"] = int(item.get("duration_hours", 1) * 60)
                item["safety_briefing_included"] = True
        elif "paragliding" in tags_lc or "skydiving" in tags_lc:
            item["booking_tip"] = "Book with certified pilots; morning slots are preferred for thermal stability."
            item["included_items"] = ["Helmet", "Harness", "Pilot insurance info"]
            item["booking_lead_time_days"] = 3
        elif "rafting" in tags_lc or "river" in tags_lc:
            item["booking_tip"] = "Operator provides lifejackets; confirm class of river and experience level."
            item["included_items"] = ["Lifejacket", "Guide", "Safety briefing"]
            item["booking_lead_time_days"] = 1
        elif "food" in tags_lc or "culinary" in tags_lc:
            item["booking_tip"] = "Inform operator of allergies; small-group tours are common."
            item["included_items"] = ["Tasting portions", "Local guide"]
            item["booking_lead_time_days"] = 0
        else:
            item["booking_tip"] = item.get("recommendation_note") or "Book locally or via trusted operator; check seasonal availability."
            item["booking_lead_time_days"] = 1
        # ensure numeric fare fields
        if item.get("estimated_fare_npr") is None and item.get("cost_estimate"):
            try:
                item["estimated_fare_npr"] = int(round(float(item.get("cost_estimate"))) )
            except Exception:
                item["estimated_fare_npr"] = None
    return ordered


def _category_price_band(category):
    category_bands = {
        "heritage": "NPR 300-1200",
        "nature": "NPR 500-2500",
        "history": "NPR 400-1400",
        "leisure": "NPR 300-1800",
        "adventure": "NPR 1200-4500",
        "hiking": "NPR 200-2200",
        "nightlife": "NPR 1200-5000",
    }
    return category_bands.get(category, "NPR 500-2000")


def _category_cost_mid(category):
    category_mid = {
        "heritage": 700,
        "nature": 1200,
        "history": 850,
        "leisure": 900,
        "adventure": 2500,
        "hiking": 1200,
        "nightlife": 2200,
        "shopping": 1400,
        "culture": 900,
        "spiritual": 500,
        "viewpoint": 1000,
        "wildlife": 2600,
    }
    return category_mid.get(category, 1000)


def _category_visit_profile(category):
    profiles = {
        "nightlife": {
            "best_slots": {"Evening"},
            "opening_hours": "5:00 PM - Late Night",
            "timing_note": "Best visited in the evening for live atmosphere.",
        },
        "hiking": {
            "best_slots": {"Morning", "Afternoon"},
            "opening_hours": "6:00 AM - 5:00 PM",
            "timing_note": "Start early for safer weather and daylight return.",
        },
        "heritage": {
            "best_slots": {"Morning", "Afternoon"},
            "opening_hours": "9:00 AM - 5:00 PM",
            "timing_note": "Daylight hours are better for museums and cultural sites.",
        },
        "history": {
            "best_slots": {"Morning", "Afternoon"},
            "opening_hours": "10:00 AM - 5:00 PM",
            "timing_note": "Most historical venues run daytime schedules.",
        },
        "shopping": {
            "best_slots": {"Afternoon", "Evening"},
            "opening_hours": "11:00 AM - 8:00 PM",
            "timing_note": "Markets and shopping streets are most active later in the day.",
        },
        "spiritual": {
            "best_slots": {"Morning", "Afternoon"},
            "opening_hours": "6:00 AM - 7:00 PM",
            "timing_note": "Morning and early evening are calmer for spiritual visits.",
        },
        "wildlife": {
            "best_slots": {"Morning", "Afternoon"},
            "opening_hours": "6:00 AM - 6:00 PM",
            "timing_note": "Wildlife activities are usually day-time only.",
        },
    }
    default_profile = {
        "best_slots": {"Morning", "Afternoon"},
        "opening_hours": "9:00 AM - 6:00 PM",
        "timing_note": "Daytime visit recommended.",
    }
    return profiles.get(str(category or "").lower(), default_profile)


def _recommended_day_slots(stops):
    stop_count = len(stops)
    has_nightlife = any(str(stop.get("category", "")).lower() == "nightlife" for stop in stops)

    if stop_count <= 0:
        return []
    if stop_count == 1:
        return ["Evening"] if has_nightlife else ["Morning"]
    if stop_count == 2:
        return ["Afternoon", "Evening"] if has_nightlife else ["Morning", "Afternoon"]
    return ["Morning", "Afternoon", "Evening"]


def _slot_fit_score(stop, slot):
    profile = _category_visit_profile(stop.get("category"))
    if slot in profile["best_slots"]:
        return 10
    if str(stop.get("category", "")).lower() == "nightlife":
        return 1
    return 4


def _assign_slots_for_day(stops):
    slots = _recommended_day_slots(stops)
    remaining = list(stops)
    assigned = []

    for slot in slots:
        if not remaining:
            break
        best_idx = max(range(len(remaining)), key=lambda idx: _slot_fit_score(remaining[idx], slot))
        stop = remaining.pop(best_idx)
        profile = _category_visit_profile(stop.get("category"))
        assigned.append(
            {
                "slot": slot,
                "stop": stop,
                "opening_hours": profile["opening_hours"],
                "timing_note": profile["timing_note"],
            }
        )

    return assigned


def _transport_mode(transport_preference, safety_priority, slot):
    pref = (transport_preference or "balanced").lower()
    if pref in {"walking", "public", "ride-share", "taxi"}:
        mode = pref
    else:
        mode = "public" if slot == "Morning" else "ride-share"

    if safety_priority and slot == "Evening" and mode in {"walking", "public"}:
        return "ride-share"
    return mode


def _fare_midpoint(low, high):
    return int((low + high) / 2)


def _city_fare_profile(city_name):
    profiles = {
        "Kathmandu": {
            "public": (25, 70),
            "ride-share": (220, 520),
            "taxi": (300, 850),
        },
        "Pokhara": {
            "public": (30, 80),
            "ride-share": (250, 560),
            "taxi": (350, 900),
        },
        "Chitwan": {
            "public": (35, 90),
            "ride-share": (260, 620),
            "taxi": (380, 980),
        },
        "Lumbini": {
            "public": (20, 60),
            "ride-share": (200, 480),
            "taxi": (300, 780),
        },
        "Mustang": {
            "public": (80, 180),
            "ride-share": (500, 1200),
            "taxi": (650, 1600),
        },
        "Janakpur": {
            "public": (20, 65),
            "ride-share": (220, 500),
            "taxi": (320, 820),
        },
    }
    return profiles.get(
        city_name,
        {
            "public": (25, 70),
            "ride-share": (220, 520),
            "taxi": (300, 850),
        },
    )


def _transport_estimate(from_name, to_name, mode, city_name):
    base = (len(from_name) + len(to_name)) % 21 + 14
    city_profile = _city_fare_profile(city_name)

    if mode == "walking":
        return {
            "duration_min": base + 20,
            "estimated_cost_npr": 0,
            "estimated_cost_range_npr": "NPR 0",
        }
    if mode == "public":
        low, high = city_profile["public"]
        low += int(base * 0.6)
        high += int(base * 1.2)
        return {
            "duration_min": base + 14,
            "estimated_cost_npr": _fare_midpoint(low, high),
            "estimated_cost_range_npr": f"NPR {low}-{high}",
        }
    if mode == "taxi":
        low, high = city_profile["taxi"]
        low += int(base * 4.5)
        high += int(base * 7.5)
        return {
            "duration_min": base + 5,
            "estimated_cost_npr": _fare_midpoint(low, high),
            "estimated_cost_range_npr": f"NPR {low}-{high}",
        }

    low, high = city_profile["ride-share"]
    low += int(base * 3.2)
    high += int(base * 5.8)
    return {
        "duration_min": base + 7,
        "estimated_cost_npr": _fare_midpoint(low, high),
        "estimated_cost_range_npr": f"NPR {low}-{high}",
    }


def _build_transport_plan(stops, transport_preference, safety_priority, city_name):
    transitions = []
    if len(stops) < 2:
        return transitions

    slots = ["Morning", "Afternoon", "Evening"]
    for idx in range(len(stops) - 1):
        from_stop = stops[idx]
        to_stop = stops[idx + 1]
        slot = slots[min(idx + 1, 2)]
        mode = _transport_mode(transport_preference, safety_priority, slot)
        estimate = _transport_estimate(from_stop["name"], to_stop["name"], mode, city_name)
        transitions.append(
            {
                "from": from_stop["name"],
                "to": to_stop["name"],
                "slot": slot,
                "mode": mode,
                "duration_min": estimate["duration_min"],
                "estimated_cost_npr": estimate["estimated_cost_npr"],
                "estimated_cost_range_npr": estimate["estimated_cost_range_npr"],
                "safety_tip": "Use verified app rides after sunset and share live location.",
                "pricing_tip": "Confirm fare in-app or ask meter-based fare before ride.",
            }
        )
    return transitions


def _food_price_range(food_type):
    normalized = str(food_type or "").lower()
    if "street" in normalized:
        return "NPR 120-280"
    if "snack" in normalized:
        return "NPR 100-250"
    if "dessert" in normalized or "sweet" in normalized:
        return "NPR 80-220"
    if "drink" in normalized or "tea" in normalized:
        return "NPR 60-180"
    if "breakfast" in normalized:
        return "NPR 150-320"
    if "traditional" in normalized or "thali" in normalized or "main meal" in normalized:
        return "NPR 350-900"
    if "specialty" in normalized:
        return "NPR 350-1100"
    return "NPR 200-650"


def _photo_from_query(query):
    q = str(query or "Nepal tourism").strip()
    if not q:
        q = "Nepal tourism"
    return f"https://source.unsplash.com/1200x800/?{quote_plus(q)}"


PLACE_CATEGORY_PHOTO_MAP = {
    "heritage": "/static/core/photos/places/heritage.svg",
    "history": "/static/core/photos/places/heritage.svg",
    "architecture": "/static/core/photos/places/heritage.svg",
    "nature": "/static/core/photos/places/nature.svg",
    "viewpoint": "/static/core/photos/places/nature.svg",
    "wildlife": "/static/core/photos/places/nature.svg",
    "culture": "/static/core/photos/places/culture.svg",
    "leisure": "/static/core/photos/places/culture.svg",
    "spiritual": "/static/core/photos/places/spiritual.svg",
    "adventure": "/static/core/photos/places/adventure.svg",
    "hiking": "/static/core/photos/places/adventure.svg",
    "nightlife": "/static/core/photos/places/nightlife.svg",
    "shopping": "/static/core/photos/places/marketplace.svg",
}

FOOD_TYPE_PHOTO_MAP = {
    "street": "/static/core/photos/foods/street.svg",
    "snack": "/static/core/photos/foods/street.svg",
    "traditional": "/static/core/photos/foods/traditional.svg",
    "meal": "/static/core/photos/foods/traditional.svg",
    "dessert": "/static/core/photos/foods/dessert.svg",
    "sweet": "/static/core/photos/foods/dessert.svg",
    "drink": "/static/core/photos/foods/drink.svg",
    "tea": "/static/core/photos/foods/drink.svg",
    "breakfast": "/static/core/photos/foods/breakfast.svg",
    "specialty": "/static/core/photos/foods/specialty.svg",
}

PLACE_SLUG_IMAGE_ALIASES = {
    "kathmandu:kathmandu-durbar-square": "kathmandu-durbar-square",
    "kathmandu:swayambhunath-stupa-monkey-temple": "swayambhunath-stupa",
    "kathmandu:thamel-nightlife-district": "thamel-street",
    "pokhara:lakeside-pokhara": "pokhara-lakeside",
    "pokhara:sarangkot": "sarangkot-sunrise",
}

FOOD_SLUG_IMAGE_ALIASES = {
    "kathmandu:newari-khaja-set": "newari-khaja-set",
    "kathmandu:newari-khajaset": "newari-khaja-set",
    "kathmandu:chatamari": "chatamari",
    "pokhara:momo": "buff-momo",
}


def _slug_compact(slug_value):
    return str(slug_value or "").replace("-", "").replace("_", "").strip().lower()


def _slug_close_match(input_slug, candidate_slug):
    if not input_slug or not candidate_slug:
        return False
    normalized_input = str(input_slug).strip().lower()
    normalized_candidate = str(candidate_slug).strip().lower()
    if normalized_input == normalized_candidate:
        return True
    return _slug_compact(normalized_input) == _slug_compact(normalized_candidate)


def _place_photo_url(place, city_key):
    place_slug = slugify(place.get("name", "place")) or "place"
    category = str(place.get("category", "")).lower()
    # Try local static jpg first
    static_base = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "places")
    city_dir = os.path.join(static_base, city_key)
    match = _best_image_match_in_dir(city_dir, place_slug)
    if match:
        rel = os.path.relpath(match, os.path.join(settings.BASE_DIR, "core", "static"))
        return "/static/" + rel.replace("\\", "/")
    # Category fallback SVG
    cat_svg = os.path.join(static_base, f"{category}.svg")
    if os.path.isfile(cat_svg):
        return f"/static/core/photos/places/{category}.svg"
    return "/static/core/photos/places/default.svg"


def _food_photo_url(food, city_key):
    food_slug = slugify(food.get("name", "food")) or "food"
    food_type = str(food.get("type", "")).lower()
    static_base = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "foods")
    city_dir = os.path.join(static_base, city_key)
    match = _best_image_match_in_dir(city_dir, food_slug)
    if match:
        rel = os.path.relpath(match, os.path.join(settings.BASE_DIR, "core", "static"))
        return "/static/" + rel.replace("\\", "/")
    alias_slug = FOOD_SLUG_IMAGE_ALIASES.get(f"{city_key}:{food_slug}", "")
    if alias_slug:
        alias_match = _best_image_match_in_dir(city_dir, alias_slug)
        if alias_match:
            rel = os.path.relpath(alias_match, os.path.join(settings.BASE_DIR, "core", "static"))
            return "/static/" + rel.replace("\\", "/")
    # Type fallback SVG
    type_svg = os.path.join(static_base, f"{food_type}.svg")
    if os.path.isfile(type_svg):
        return f"/static/core/photos/foods/{food_type}.svg"
    return "/static/core/photos/foods/default.svg"


def _best_keyword_image_match_in_dir(dir_path, keywords):
    if not os.path.isdir(dir_path) or not keywords:
        return ""

    best_score = 0
    best_file = ""
    for filename in os.listdir(dir_path):
        full_path = os.path.join(dir_path, filename)
        if not os.path.isfile(full_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        stem = os.path.splitext(filename)[0].lower()
        score = sum(1 for keyword in keywords if keyword in stem)
        if score > best_score:
            best_score = score
            best_file = filename

    if best_score > 0 and best_file:
        return os.path.join(dir_path, best_file)
    return ""


def _activity_photo_url(activity, city_key):
    name = str(getattr(activity, "name", "") or "").strip()
    if not name:
        return ""

    base_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "places", city_key)
    match = _best_image_match_in_dir(base_dir, slugify(name))
    if match:
        return _static_media_url(["core", "photos", "places", city_key, os.path.basename(match)])

    guide = CITY_GUIDES.get(city_key)
    if guide:
        name_lc = name.lower()
        for place in guide.get("places", []):
            place_name = str(place.get("name", "") or "")
            if not place_name:
                continue
            place_lc = place_name.lower()
            if place_lc in name_lc or name_lc in place_lc:
                return _place_photo_url(place, city_key)

    keywords = _keywords_from_name(
        f"{name} {getattr(activity, 'description', '') or ''} {getattr(activity, 'tags', '') or ''}"
    )
    match = _best_keyword_image_match_in_dir(base_dir, keywords)
    if match:
        return _static_media_url(["core", "photos", "places", city_key, os.path.basename(match)])

    return ""


def _local_media_candidates(base_dir, city_key, slug_name):
    return [
        os.path.join(base_dir, city_key, f"{slug_name}.jpg"),
        os.path.join(base_dir, city_key, f"{slug_name}.jpeg"),
        os.path.join(base_dir, city_key, f"{slug_name}.png"),
    ]


def _static_media_url(path_segments):
    return "/static/" + "/".join(path_segments)


def _slug_variants(slug_name):
    base = str(slug_name or "").strip().lower()
    if not base:
        return []
    variants = {base, base.replace("-", "_"), base.replace("_", "-")}
    compact = base.replace("-", " ").replace("_", " ").strip()
    if compact:
        variants.add(compact.replace(" ", "-"))
        variants.add(compact.replace(" ", "_"))
    return [item for item in variants if item]


def _best_image_match_in_dir(dir_path, slug_name):
    if not os.path.isdir(dir_path):
        return ""

    image_files = []
    for filename in os.listdir(dir_path):
        full_path = os.path.join(dir_path, filename)
        if not os.path.isfile(full_path):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            continue
        image_files.append(filename)

    if not image_files:
        return ""

    variants = _slug_variants(slug_name)
    lowered = {f.lower(): f for f in image_files}

    # Exact stem match first.
    for variant in variants:
        for ext in ALLOWED_IMAGE_EXTENSIONS:
            name = f"{variant}{ext}"
            if name in lowered:
                return os.path.join(dir_path, lowered[name])
    return ""


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 6 * 1024 * 1024


def _normalize_slug(value):
    return slugify(str(value or "").strip())


def _save_uploaded_image(uploaded_file, target_dir, filename_base):
    original_name = str(uploaded_file.name or "")
    ext = os.path.splitext(original_name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None, f"Unsupported file type: {ext or 'unknown'}"

    os.makedirs(target_dir, exist_ok=True)
    filename = f"{filename_base}{ext}"
    target_path = os.path.join(target_dir, filename)

    with open(target_path, "wb") as handle:
        for chunk in uploaded_file.chunks():
            handle.write(chunk)

    return filename, ""


def _google_static_map_url(location_query):
    query = quote_plus(str(location_query or "Nepal tourism"))
    url = (
        "https://maps.googleapis.com/maps/api/staticmap"
        f"?center={query}"
        "&zoom=15"
        "&size=1200x800"
        "&scale=2"
        "&maptype=roadmap"
        f"&markers=color:red%7C{query}"
    )
    api_key = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
    if api_key:
        url += f"&key={quote_plus(api_key)}"
    return url


def _svg_palette(tag):
    palettes = {
        "heritage": ("#7c2d12", "#f59e0b"),
        "history": ("#7c2d12", "#f59e0b"),
        "nature": ("#14532d", "#22c55e"),
        "culture": ("#1d4ed8", "#38bdf8"),
        "spiritual": ("#312e81", "#a78bfa"),
        "adventure": ("#0f172a", "#0ea5e9"),
        "hiking": ("#0f172a", "#0ea5e9"),
        "nightlife": ("#111827", "#ef4444"),
        "shopping": ("#78350f", "#f97316"),
        "street": ("#9a3412", "#f97316"),
        "traditional": ("#7c2d12", "#f59e0b"),
        "drink": ("#0f766e", "#2dd4bf"),
        "dessert": ("#be185d", "#f472b6"),
        "breakfast": ("#92400e", "#fbbf24"),
        "specialty": ("#1e3a8a", "#60a5fa"),
    }
    return palettes.get(str(tag or "").lower(), ("#334155", "#64748b"))


def _svg_card(title, subtitle, tag):
    c1, c2 = _svg_palette(tag)
    safe_title = str(title or "Tourist Photo").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_subtitle = str(subtitle or "TrailMate").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"800\" viewBox=\"0 0 1200 800\">
  <defs>
    <linearGradient id=\"g\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
      <stop offset=\"0%\" stop-color=\"{c1}\"/>
      <stop offset=\"100%\" stop-color=\"{c2}\"/>
    </linearGradient>
  </defs>
  <rect width=\"1200\" height=\"800\" fill=\"url(#g)\"/>
  <rect x=\"72\" y=\"110\" width=\"1056\" height=\"580\" fill=\"rgba(255,255,255,0.1)\" stroke=\"rgba(255,255,255,0.35)\"/>
  <text x=\"110\" y=\"260\" fill=\"#ffffff\" font-size=\"58\" font-family=\"Segoe UI, Arial\" font-weight=\"700\">{safe_title}</text>
  <text x=\"110\" y=\"338\" fill=\"#ffffff\" font-size=\"32\" font-family=\"Segoe UI, Arial\">{safe_subtitle}</text>
  <text x=\"110\" y=\"676\" fill=\"#ffffff\" font-size=\"24\" font-family=\"Segoe UI, Arial\">TrailMate Curated Visual</text>
</svg>
""".strip()


def _route_svg_card(route_id):
        route = TREKKING_ROUTES.get(route_id)
        if not route:
                return _svg_card("Route Map", "Trekking route preview", "adventure")

        name = str(route.get("name", "Trekking Route")).replace("&", "&amp;")
        season = str(route.get("best_season", "All season")).replace("&", "&amp;")
        difficulty = str(route.get("difficulty", "Moderate")).replace("&", "&amp;")
        points = [str(item.get("route", "")).split(" to ") for item in route.get("day_wise_itinerary", []) if item.get("route")]
        checkpoints = []
        for pair in points:
                for p in pair:
                        p = p.strip()
                        if p and p not in checkpoints:
                                checkpoints.append(p)
        checkpoints = checkpoints[:6]
        stop_labels = "  •  ".join(checkpoints) if checkpoints else "Route checkpoints"
        stop_labels = stop_labels.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        return f"""
<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1200\" height=\"800\" viewBox=\"0 0 1200 800\">
    <defs>
        <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
            <stop offset=\"0%\" stop-color=\"#0f172a\"/>
            <stop offset=\"100%\" stop-color=\"#0ea5e9\"/>
        </linearGradient>
    </defs>
    <rect width=\"1200\" height=\"800\" fill=\"url(#bg)\"/>
    <rect x=\"70\" y=\"92\" width=\"1060\" height=\"616\" fill=\"rgba(255,255,255,0.08)\" stroke=\"rgba(255,255,255,0.36)\"/>
    <text x=\"106\" y=\"170\" fill=\"#ffffff\" font-size=\"52\" font-family=\"Segoe UI, Arial\" font-weight=\"700\">{name}</text>
    <text x=\"106\" y=\"224\" fill=\"#dbeafe\" font-size=\"26\" font-family=\"Segoe UI, Arial\">Difficulty: {difficulty}  |  Best season: {season}</text>

    <polyline points=\"150,560 300,460 450,510 600,380 760,430 930,290 1060,330\" fill=\"none\" stroke=\"#22d3ee\" stroke-width=\"10\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/>
    <circle cx=\"150\" cy=\"560\" r=\"15\" fill=\"#22c55e\"/>
    <circle cx=\"1060\" cy=\"330\" r=\"15\" fill=\"#ef4444\"/>
    <text x=\"126\" y=\"598\" fill=\"#86efac\" font-size=\"24\" font-family=\"Segoe UI, Arial\">Start</text>
    <text x=\"1010\" y=\"374\" fill=\"#fca5a5\" font-size=\"24\" font-family=\"Segoe UI, Arial\">Finish</text>

    <text x=\"106\" y=\"664\" fill=\"#e2e8f0\" font-size=\"22\" font-family=\"Segoe UI, Arial\">{stop_labels}</text>
    <text x=\"106\" y=\"700\" fill=\"#cbd5e1\" font-size=\"20\" font-family=\"Segoe UI, Arial\">TrailMate exact route card (stable offline-safe preview)</text>
</svg>
""".strip()


def _keywords_from_name(name):
    raw = [part.strip().lower() for part in str(name or "").replace("(", " ").replace(")", " ").replace("-", " ").split()]
    stop = {"the", "and", "of", "to", "in", "for", "nepal", "route", "trek", "tour", "street", "area"}
    return [item for item in raw if len(item) >= 4 and item not in stop]


def _resolved_place_photo(city_key, place):
    place_slug = slugify(place.get("name", "place")) or "place"
    alias_key = f"{city_key}:{place_slug}"
    alias_slug = PLACE_SLUG_IMAGE_ALIASES.get(alias_key, "")
    base_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "places")
    for candidate in _local_media_candidates(base_dir, city_key, place_slug):
        if os.path.exists(candidate):
            filename = os.path.basename(candidate)
            return _static_media_url(["core", "photos", "places", city_key, filename])

    if alias_slug:
        for candidate in _local_media_candidates(base_dir, city_key, alias_slug):
            if os.path.exists(candidate):
                filename = os.path.basename(candidate)
                return _static_media_url(["core", "photos", "places", city_key, filename])

    matched = _best_image_match_in_dir(os.path.join(base_dir, city_key), place_slug)
    if matched:
        return _static_media_url(["core", "photos", "places", city_key, os.path.basename(matched)])

    # Allow manual imported images in photos/_import/* folders.
    import_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "_import")
    if os.path.isdir(import_dir):
        preferred_subdirs = []
        fallback_subdirs = []
        for sub in os.listdir(import_dir):
            if city_key in str(sub).lower():
                preferred_subdirs.append(sub)
            else:
                fallback_subdirs.append(sub)

        # City-matching import folders first to avoid wrong-city image picks.
        for sub in preferred_subdirs + fallback_subdirs:
            sub_path = os.path.join(import_dir, sub)
            matched = _best_image_match_in_dir(sub_path, place_slug)
            if matched:
                return _static_media_url(["core", "photos", "_import", sub, os.path.basename(matched)])
            if alias_slug:
                matched = _best_image_match_in_dir(sub_path, alias_slug)
                if matched:
                    return _static_media_url(["core", "photos", "_import", sub, os.path.basename(matched)])

    category = str(place.get("category", "")).lower()
    return PLACE_CATEGORY_PHOTO_MAP.get(category, "/static/core/photos/places/default.svg")


def _resolved_food_photo(city_key, food):
    food_slug = slugify(food.get("name", "food")) or "food"
    alias_key = f"{city_key}:{food_slug}"
    alias_slug = FOOD_SLUG_IMAGE_ALIASES.get(alias_key, "")
    base_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "foods")
    for candidate in _local_media_candidates(base_dir, city_key, food_slug):
        if os.path.exists(candidate):
            filename = os.path.basename(candidate)
            return _static_media_url(["core", "photos", "foods", city_key, filename])

    if alias_slug:
        for candidate in _local_media_candidates(base_dir, city_key, alias_slug):
            if os.path.exists(candidate):
                filename = os.path.basename(candidate)
                return _static_media_url(["core", "photos", "foods", city_key, filename])

    matched = _best_image_match_in_dir(os.path.join(base_dir, city_key), food_slug)
    if matched:
        return _static_media_url(["core", "photos", "foods", city_key, os.path.basename(matched)])
    if alias_slug:
        matched = _best_image_match_in_dir(os.path.join(base_dir, city_key), alias_slug)
        if matched:
            return _static_media_url(["core", "photos", "foods", city_key, os.path.basename(matched)])

    matched = _best_image_match_in_dir(base_dir, food_slug)
    if matched:
        return _static_media_url(["core", "photos", "foods", os.path.basename(matched)])
    if alias_slug:
        matched = _best_image_match_in_dir(base_dir, alias_slug)
        if matched:
            return _static_media_url(["core", "photos", "foods", os.path.basename(matched)])

    # Optional fallback to imported files if user keeps food photos there.
    import_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "_import")
    if os.path.isdir(import_dir):
        preferred_subdirs = []
        fallback_subdirs = []
        for sub in os.listdir(import_dir):
            if city_key in str(sub).lower():
                preferred_subdirs.append(sub)
            else:
                fallback_subdirs.append(sub)

        # City-matching import folders first to avoid wrong-city image picks.
        for sub in preferred_subdirs + fallback_subdirs:
            sub_path = os.path.join(import_dir, sub)
            matched = _best_image_match_in_dir(sub_path, food_slug)
            if matched:
                return _static_media_url(["core", "photos", "_import", sub, os.path.basename(matched)])
            if alias_slug:
                matched = _best_image_match_in_dir(sub_path, alias_slug)
                if matched:
                    return _static_media_url(["core", "photos", "_import", sub, os.path.basename(matched)])

    food_type = str(food.get("type", "")).lower()
    for keyword, image in FOOD_TYPE_PHOTO_MAP.items():
        if keyword in food_type:
            return image
    return "/static/core/photos/foods/default.svg"


def _resolved_trek_photo(route_id):
    normalized_route = _normalize_slug(route_id)
    if not normalized_route:
        return ""

    # Prefer exact map assets from dedicated trekking map directory.
    maps_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "maps")
    map_slug_candidates = [
        normalized_route,
        f"{normalized_route}_route",
        f"{normalized_route}_map",
    ]
    route_name = TREKKING_ROUTES.get(normalized_route, {}).get("name", "")
    if route_name:
        route_name_slug = _normalize_slug(route_name)
        if route_name_slug:
            map_slug_candidates.extend(
                [
                    route_name_slug,
                    f"{route_name_slug}_route",
                    f"{route_name_slug}_map",
                ]
            )

    seen = set()
    for candidate_slug in map_slug_candidates:
        if candidate_slug in seen:
            continue
        seen.add(candidate_slug)
        matched = _best_image_match_in_dir(maps_dir, candidate_slug)
        if matched:
            return _static_media_url(["core", "maps", os.path.basename(matched)])

    # Fallback to uploaded trek photos if user added custom route visuals.
    trek_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "trek")
    for candidate in _local_media_candidates(trek_dir, "", normalized_route):
        if os.path.exists(candidate):
            return _static_media_url(["core", "photos", "trek", os.path.basename(candidate)])

    matched = _best_image_match_in_dir(trek_dir, normalized_route)
    if matched:
        return _static_media_url(["core", "photos", "trek", os.path.basename(matched)])

    return ""


def _find_place(city_key, place_slug):
    guide = CITY_GUIDES.get(city_key)
    if not guide:
        return None

    normalized_input = str(place_slug or "").strip().lower()
    for place in guide.get("places", []):
        candidate_slug = slugify(place.get("name", ""))
        if _slug_close_match(normalized_input, candidate_slug):
            return place

    alias_target = PLACE_SLUG_IMAGE_ALIASES.get(f"{city_key}:{normalized_input}", "")
    if alias_target:
        for place in guide.get("places", []):
            candidate_slug = slugify(place.get("name", ""))
            if _slug_close_match(alias_target, candidate_slug):
                return place
    return None


def _find_food(city_key, food_slug):
    guide = CITY_GUIDES.get(city_key)
    if not guide:
        return None

    normalized_input = str(food_slug or "").strip().lower()
    for food in guide.get("foods", []):
        candidate_slug = slugify(food.get("name", ""))
        if _slug_close_match(normalized_input, candidate_slug):
            return food

    alias_target = FOOD_SLUG_IMAGE_ALIASES.get(f"{city_key}:{normalized_input}", "")
    if alias_target:
        for food in guide.get("foods", []):
            candidate_slug = slugify(food.get("name", ""))
            if _slug_close_match(alias_target, candidate_slug):
                return food
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
def place_media_svg(request, city, place_slug):
    city_key = str(city).strip().lower()
    place = _find_place(city_key, place_slug)
    if not place:
        svg = _svg_card("Place Visual", "Tourist place preview", "default")
        return HttpResponse(svg, content_type="image/svg+xml")

    resolved = _resolved_place_photo(city_key, place)
    if resolved:
        return HttpResponse(
            status=302,
            headers={"Location": resolved},
        )

    city_name = CITY_GUIDES[city_key].get("display_name", city_key.title()) if city_key in CITY_GUIDES else city_key.title()
    title = place.get("name", "Tourist Place")
    subtitle = f"{city_name} - {place.get('category', 'travel spot').title()}"
    svg = _svg_card(title, subtitle, place.get("category", "default"))
    return HttpResponse(svg, content_type="image/svg+xml")


@api_view(["GET"])
@permission_classes([AllowAny])
def food_media_svg(request, city, food_slug):
    city_key = str(city).strip().lower()
    food = _find_food(city_key, food_slug)
    if not food:
        svg = _svg_card("Food Visual", "Local food preview", "default")
        return HttpResponse(svg, content_type="image/svg+xml")

    resolved = _resolved_food_photo(city_key, food)
    if resolved:
        return HttpResponse(
            status=302,
            headers={"Location": resolved},
        )

    city_name = CITY_GUIDES[city_key].get("display_name", city_key.title()) if city_key in CITY_GUIDES else city_key.title()
    title = food.get("name", "Local Food")
    subtitle = f"{city_name} - {food.get('type', 'food')}"
    food_type = str(food.get("type", "default")).split()[0]
    svg = _svg_card(title, subtitle, food_type)
    return HttpResponse(svg, content_type="image/svg+xml")


@api_view(["GET"])
@permission_classes([AllowAny])
def trek_route_media_svg(request, route_id):
    normalized_route_id = str(route_id).strip().lower().replace("-", "_")
    resolved = _resolved_trek_photo(normalized_route_id)
    if resolved:
        return HttpResponse(
            status=302,
            headers={"Location": resolved},
        )
    svg = _route_svg_card(normalized_route_id)
    return HttpResponse(svg, content_type="image/svg+xml")


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def media_upload(request):
    kind = str(request.data.get("kind", "")).strip().lower()
    city = str(request.data.get("city", "")).strip().lower()
    slug_value = str(request.data.get("slug", "")).strip()
    upload = request.FILES.get("image") or request.FILES.get("file")

    if not upload:
        return Response({"error": "Image file is required."}, status=400)
    if upload.size > MAX_UPLOAD_BYTES:
        return Response({"error": "Image file must be 6MB or smaller."}, status=400)
    if kind not in {"place", "food", "trek"}:
        return Response({"error": "Kind must be place, food, or trek."}, status=400)

    slug_key = _normalize_slug(slug_value)
    if not slug_key:
        return Response({"error": "Slug is required."}, status=400)

    if kind in {"place", "food"}:
        city_key = _normalize_slug(city)
        if not city_key:
            return Response({"error": "City is required for place or food uploads."}, status=400)
        base_folder = "places" if kind == "place" else "foods"
        target_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", base_folder, city_key)
        filename, error = _save_uploaded_image(upload, target_dir, slug_key)
        if error:
            return Response({"error": error}, status=400)
        url = _static_media_url(["core", "photos", base_folder, city_key, filename])
        return Response({"ok": True, "url": url, "kind": kind, "city": city_key, "slug": slug_key})

    route_key = slug_key.replace("-", "_")
    target_dir = os.path.join(settings.BASE_DIR, "core", "static", "core", "photos", "trek")
    filename, error = _save_uploaded_image(upload, target_dir, route_key)
    if error:
        return Response({"error": error}, status=400)
    url = _static_media_url(["core", "photos", "trek", filename])
    return Response({"ok": True, "url": url, "kind": kind, "slug": route_key})


def _historical_formation_note(city_name, place):
    name = place.get("name", "This place")
    category = str(place.get("category", "")).lower()

    category_templates = {
        "heritage": "Local records and community memory describe it as a long-standing civic and spiritual core, expanded through royal-era patronage and traditional trade movement.",
        "history": "It evolved as a historical landmark over multiple local governance periods, and later became a preserved reference point for regional identity.",
        "culture": "The area formed around settlement clusters, festival routes, and artisan activity, gradually becoming a living cultural hub.",
        "spiritual": "It developed as a sacred gathering point where pilgrimage, ritual practice, and community support systems grew together over generations.",
        "nature": "Its landscape was formed by Himalayan geology and water systems, and local communities adapted their lifestyle around seasonal patterns.",
        "viewpoint": "This viewpoint emerged from older walking and grazing paths, later becoming a known public lookout for sunrise, navigation, and festivals.",
        "hiking": "Originally a local movement trail for villages and pasture access, it gradually transitioned into a trekking corridor for visitors.",
        "shopping": "It formed as a local market exchange zone where agricultural produce, crafts, and daily goods connected nearby settlements.",
        "nightlife": "This zone evolved from a commercial street into a social evening district as tourism and hospitality services expanded.",
        "adventure": "The site gained popularity after local route use and modern safety upgrades made the terrain accessible for guided adventure travel.",
        "wildlife": "It was shaped by forest and habitat conservation boundaries, then opened in controlled phases for eco-tourism and education.",
        "leisure": "The area developed as a community recreation space tied to nearby neighborhoods, seasonal gatherings, and family outings.",
        "architecture": "Built form and layout reflect cross-regional design influences that accumulated through religious exchange and local craftsmanship.",
    }

    formation_core = category_templates.get(
        category,
        "It developed gradually through local settlement, trade, and cultural movement, and remains part of everyday community identity.",
    )

    return (
        f"{name} in {city_name} has layered local history. {formation_core} "
        "Today it connects tourists with community memory through food, rituals, architecture, and daily street life."
    )


def _food_origin_note(city_name, food):
    food_name = food.get("name", "This food")
    food_type = str(food.get("type", "local favorite")).lower()

    if "street" in food_type:
        base = "It grew through market-stall culture where vendors optimized quick, affordable flavor for daily commuters and evening crowds."
    elif "traditional" in food_type or "regional" in food_type:
        base = "Its preparation style comes from household and festival kitchens, then moved into public eateries as demand grew."
    elif "drink" in food_type:
        base = "The drink tradition formed around climate, local ingredients, and social tea-time habits in public gathering spaces."
    elif "dessert" in food_type or "sweet" in food_type:
        base = "The recipe evolved from ceremonial and festive use into a popular everyday sweet sold in local markets."
    else:
        base = "It became popular through a mix of local ingredients, migration influence, and city food-lane adaptation."

    return f"{food_name} in {city_name}: {base}"


def _format_npr_range(low, high):
    return f"NPR {int(low)}-{int(high)}"


def _scaled_range(base_range, multiplier):
    low, high = base_range
    return int(low * multiplier), int(high * multiplier)


def _fare_tiers(city_name, budget_level):
    city_fare = _city_fare_profile(city_name)

    budget_transport = _scaled_range(city_fare["public"], 1.0)
    standard_transport = _scaled_range(city_fare["ride-share"], 1.0)
    premium_transport = _scaled_range(city_fare["taxi"], 1.05)

    tiers = {
        "budget": {
            "meals_per_person_npr": _format_npr_range(250, 700),
            "transport_per_day_npr": _format_npr_range(*budget_transport),
            "estimated_daily_total_npr": _format_npr_range(1600, 3200),
            "notes": "Mostly public transport, local eateries, and low ticket-cost spots.",
        },
        "standard": {
            "meals_per_person_npr": _format_npr_range(400, 1000),
            "transport_per_day_npr": _format_npr_range(*standard_transport),
            "estimated_daily_total_npr": _format_npr_range(2800, 5200),
            "notes": "Mix of ride-share and public transport with balanced dining.",
        },
        "premium": {
            "meals_per_person_npr": _format_npr_range(700, 1800),
            "transport_per_day_npr": _format_npr_range(*premium_transport),
            "estimated_daily_total_npr": _format_npr_range(4800, 9200),
            "notes": "Taxi-first mobility, premium cafes/restaurants, and comfort-focused pacing.",
        },
    }

    recommended_tier = "standard"
    if budget_level == "low":
        recommended_tier = "budget"
    elif budget_level == "high":
        recommended_tier = "premium"

    return {
        "recommended_tier": recommended_tier,
        "tiers": tiers,
    }


def _comfort_pack(city_name, safety_priority, pricing_priority):
    city_fare = _city_fare_profile(city_name)
    public_low, public_high = city_fare["public"]
    ride_low, ride_high = city_fare["ride-share"]
    taxi_low, taxi_high = city_fare["taxi"]

    return {
        "city": city_name,
        "safety_priority": safety_priority,
        "pricing_priority": pricing_priority,
        "emergency_contacts": [
            "Tourist Police: 1144",
            "Emergency Police: 100",
            "Ambulance: 102",
        ],
        "pricing_baseline": [
            f"City bus/public micro: NPR {public_low}-{public_high}",
            f"Ride-share short trip: NPR {ride_low}-{ride_high}",
            f"Taxi short trip: NPR {taxi_low}-{taxi_high}",
            "Typical local meal: NPR 250-900",
            "Cafe/restaurant meal: NPR 500-1400",
        ],
        "safety_checklist": [
            "Prefer verified transport after dark.",
            "Avoid carrying all cash in one place.",
            "Keep offline map and hotel contact ready.",
            "Use marked ATMs and avoid isolated lanes at night.",
        ],
    }


def _anti_scam_pack(city_name):
    city_fare = _city_fare_profile(city_name)
    public_low, public_high = city_fare["public"]
    ride_low, ride_high = city_fare["ride-share"]
    taxi_low, taxi_high = city_fare["taxi"]

    return {
        "city": city_name,
        "verified_fare_ranges": [
            f"Public micro/bus typical range: NPR {public_low}-{public_high}",
            f"Ride-share short trip normal range: NPR {ride_low}-{ride_high}",
            f"Taxi short trip normal range: NPR {taxi_low}-{taxi_high}",
        ],
        "scam_red_flags": [
            "Driver refuses meter and demands price far above local range.",
            "Someone pushes you to switch to an unmarked vehicle or unofficial guide.",
            "Restaurant/agent avoids printed bill or adds hidden service charges.",
            "Street currency exchange offers rates that are too good to be true.",
        ],
        "safe_actions": [
            "Confirm price before ride/food order and re-check at payment time.",
            "Use app-based rides or hotel-booked transport at night.",
            "Pay with small notes and avoid exposing full cash wallet.",
            "Choose busy, well-reviewed restaurants and licensed ticket counters.",
        ],
        "report_steps": [
            "Call Tourist Police 1144 for overcharging or harassment.",
            "Note plate number/business name and keep receipt screenshot.",
            "Share route and fare details with hotel/front desk for support.",
        ],
    }


def _build_trust_metrics(stops, transport_plan, safety_priority, pricing_priority):
    safety_score = 68 + (12 if safety_priority else 0)
    pricing_score = 64 + (12 if pricing_priority else 0)
    reasons = []

    if safety_priority:
        reasons.append("Safety-first mode enabled.")
    else:
        reasons.append("Safety-first mode is off, so routes are more flexible.")

    if pricing_priority:
        reasons.append("Fair-pricing mode enabled for budget-aware recommendations.")

    evening_walk_penalty = 0
    for leg in transport_plan:
        if leg.get("slot") == "Evening" and leg.get("mode") == "walking":
            evening_walk_penalty += 10

    avg_transport_cost = 0
    if transport_plan:
        avg_transport_cost = sum(leg.get("estimated_cost_npr", 0) for leg in transport_plan) / len(transport_plan)

    if avg_transport_cost > 700:
        pricing_score -= 8
        reasons.append("Higher transport cost reduced pricing score.")
    elif avg_transport_cost < 300:
        pricing_score += 4
        reasons.append("Affordable transport options improved pricing score.")
    else:
        reasons.append("Transport pricing stayed within normal city range.")

    safety_score -= evening_walk_penalty
    if evening_walk_penalty:
        reasons.append("Evening walking segments reduced safety score.")
    else:
        reasons.append("No risky evening walking segments detected.")

    # Stop count contributes to perceived comfort but avoids over-penalizing short days.
    stop_bonus = min(len(stops), 3) * 4
    comfort_score = int((safety_score + pricing_score) / 2) + stop_bonus

    safety_score = max(40, min(98, int(safety_score)))
    pricing_score = max(40, min(98, int(pricing_score)))
    comfort_score = max(45, min(99, int(comfort_score)))

    if comfort_score >= 85:
        badge = "High Trust"
        level = "high"
    elif comfort_score >= 72:
        badge = "Trusted"
        level = "medium"
    else:
        badge = "Needs Review"
        level = "low"

    scam_risk_score = 28
    scam_reasons = []

    if not pricing_priority:
        scam_risk_score += 18
        scam_reasons.append("Pricing-priority mode is off, so fare filtering is less strict.")
    else:
        scam_reasons.append("Fair-pricing mode reduces overcharge exposure.")

    if not safety_priority:
        scam_risk_score += 14
        scam_reasons.append("Safety-priority mode is off, increasing route flexibility and risk.")
    else:
        scam_reasons.append("Safety-priority mode keeps routes in safer movement windows.")

    taxi_legs = 0
    evening_mobility_risk = 0
    for leg in transport_plan:
        mode = str(leg.get("mode", "")).strip().lower()
        slot = str(leg.get("slot", "")).strip().lower()
        if mode == "taxi":
            taxi_legs += 1
        if slot == "evening" and mode == "walking":
            evening_mobility_risk += 10
        elif slot == "evening" and mode in {"taxi", "ride-share"}:
            evening_mobility_risk += 6

    scam_risk_score += min(14, taxi_legs * 4)
    scam_risk_score += min(20, evening_mobility_risk)

    high_exposure_categories = {"nightlife", "shopping", "marketplace"}
    exposure_points = 0
    for stop in stops:
        category = str(stop.get("category", "")).strip().lower()
        if category in high_exposure_categories:
            exposure_points += 4
    scam_risk_score += min(12, exposure_points)

    if avg_transport_cost > 1000:
        scam_risk_score += 12
        scam_reasons.append("Average transport fare is high; double-check meter and app estimate before paying.")
    elif avg_transport_cost > 700:
        scam_risk_score += 7
        scam_reasons.append("Transport fares are above normal baseline; confirm fare before ride.")
    else:
        scam_reasons.append("Transport fares are within safer baseline range.")

    scam_risk_score = max(15, min(95, int(scam_risk_score)))
    if scam_risk_score >= 70:
        scam_level = "high"
        scam_badge = "Scam Alert: High"
    elif scam_risk_score >= 45:
        scam_level = "medium"
        scam_badge = "Scam Alert: Medium"
    else:
        scam_level = "low"
        scam_badge = "Scam Alert: Low"

    return {
        "safety_score": safety_score,
        "pricing_score": pricing_score,
        "comfort_score": comfort_score,
        "badge": badge,
        "level": level,
        "reasons": reasons,
        "scam_alert": {
            "score": scam_risk_score,
            "level": scam_level,
            "badge": scam_badge,
            "reasons": scam_reasons,
        },
    }


def _build_balanced_day_stops(places, days, max_stops_per_day=2):
    """Distribute places into day buckets with practical stop caps and category variety."""
    if days <= 0:
        return []

    day_stops = [[] for _ in range(days)]
    remaining = list(places)

    # First pass: give each day one unique stop when possible.
    for day_index in range(days):
        if not remaining:
            break
        day_stops[day_index].append(remaining.pop(0))

    # Second pass: fill up to max_stops_per_day while preferring new categories per day.
    while remaining:
        progress = False
        for day_index in range(days):
            if not remaining:
                break
            if len(day_stops[day_index]) >= max_stops_per_day:
                continue

            used_categories = {stop.get("category") for stop in day_stops[day_index]}
            pick_index = next(
                (
                    idx
                    for idx, candidate in enumerate(remaining)
                    if candidate.get("category") not in used_categories
                ),
                0,
            )
            day_stops[day_index].append(remaining.pop(pick_index))
            progress = True

        if not progress:
            break

    return day_stops


def _select_diverse_places(ranked_places, top_n):
    """Select top places while avoiding single-category domination."""
    selected = []
    category_count = defaultdict(int)
    seen_names = set()

    if top_n <= 0:
        return selected

    category_limit = max(2, (top_n + 2) // 3)

    # First pass: take one place from each category if available.
    used_categories = set()
    for place in ranked_places:
        if len(selected) >= top_n:
            break
        name = place.get("name")
        category = place.get("category", "other")
        if name in seen_names or category in used_categories:
            continue
        selected.append(place)
        seen_names.add(name)
        used_categories.add(category)
        category_count[category] += 1

    # Second pass: fill remaining while respecting per-category caps.
    for place in ranked_places:
        if len(selected) >= top_n:
            break
        name = place.get("name")
        category = place.get("category", "other")
        if name in seen_names:
            continue
        if category_count[category] >= category_limit:
            continue
        selected.append(place)
        seen_names.add(name)
        category_count[category] += 1

    # Final pass: fill any gap without category cap, still unique by place.
    for place in ranked_places:
        if len(selected) >= top_n:
            break
        name = place.get("name")
        if name in seen_names:
            continue
        selected.append(place)
        seen_names.add(name)

    return selected


def _place_main_activity(place):
    best_for = place.get("best_for") or []
    if best_for:
        return str(best_for[0]).replace("-", " ").title()
    return "Local Exploration"


@api_view(["POST"])
@permission_classes([AllowAny])
def city_ai_guide(request, city):
    city_key = str(city).strip().lower()
    guide = CITY_GUIDES.get(city_key)
    if not guide:
        return Response(
            {
                "error": "Guide not available yet for this city",
                "available_cities": list(CITY_GUIDES.keys()),
            },
            status=404,
        )

    interests = _normalize_list(request.data.get("interests", []))

    if not interests:
        interests = guide["default_interests"]

    days = int(request.data.get("days", 2) or 2)
    days = max(1, min(days, 7))

    budget_npr = int(request.data.get("budget_npr", 4000) or 4000)
    budget_level = _budget_tier(budget_npr)

    focus_activities = _normalize_list(request.data.get("focus_activities", []))
    avoid_categories = set(_normalize_list(request.data.get("avoid_categories", [])))
    transport_preference = str(request.data.get("transport_preference", "balanced") or "balanced").strip().lower()
    family_mode = _as_bool(request.data.get("family_mode", False))
    include_food = _as_bool(request.data.get("include_food", True), True)
    safety_priority = _as_bool(request.data.get("safety_priority", True), True)
    pricing_priority = _as_bool(request.data.get("pricing_priority", True), True)

    all_interests = list(dict.fromkeys(interests + focus_activities))
    if not all_interests:
        all_interests = guide["default_interests"]

    candidate_places = [
        place for place in guide["places"] if str(place.get("category", "")).lower() not in avoid_categories
    ]
    if not candidate_places:
        candidate_places = guide["places"]

    ranked = sorted(
        candidate_places,
        key=lambda place: _place_score(place, all_interests, budget_level, family_mode)
        + (3 if set(focus_activities).intersection(set(place["best_for"])) else 0),
        reverse=True,
    )

    ranked_unique = []
    seen = set()
    for place in ranked:
        if place["name"] in seen:
            continue
        ranked_unique.append(place)
        seen.add(place["name"])

    if days == 1:
        practical_stops_per_day = 3
    else:
        practical_stops_per_day = 2

    top_n = min(len(ranked_unique), max(4, days * practical_stops_per_day))
    selected = _select_diverse_places(ranked_unique, top_n)
    top_highlights = selected[:3]

    places = []
    for place in selected:
        places.append(
            {
                "name": place["name"],
                "category": place["category"],
                "why_best": place["why_best"],
                "main_activity": _place_main_activity(place),
                "recommended_for": place["best_for"],
                "famous_food_nearby": place["famous_food_nearby"] if include_food else [],
                "price_band_npr": _category_price_band(place["category"]),
                "safety_note": "Prefer trusted transport and stay in well-lit routes.",
                "area_photo_url": _place_photo_url(place, city_key),
                "historical_formation": _historical_formation_note(guide["display_name"], place),
                "map_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(place['map_query'])}",
            }
        )

    day_stops = _build_balanced_day_stops(places, days, max_stops_per_day=practical_stops_per_day)

    foods = []
    if include_food:
        foods = [
            {
                "name": food["name"],
                "type": food["type"],
                "where_to_try": food["where"],
                "price_range_npr": _food_price_range(food.get("type")),
                "photo_url": _food_photo_url(food, city_key),
                "origin_note": _food_origin_note(guide["display_name"], food),
                "map_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(food['name'] + ' ' + food['where'] + ' ' + guide['display_name'])}",
            }
            for food in guide["foods"]
        ]

    day_wise_itinerary = []
    for i in range(days):
        stops = day_stops[i]
        overview = []
        if not stops:
            day_wise_itinerary.append(
                {
                    "day": i + 1,
                    "stops": [],
                    "overview": [],
                    "transport_plan": [],
                    "trust": {
                        "safety_score": 75,
                        "pricing_score": 75,
                        "comfort_score": 75,
                        "badge": "Trusted",
                        "level": "medium",
                        "reasons": ["No additional stops planned for this day. Use as flexible/rest buffer."],
                    },
                    "stop_count": 0,
                    "day_budget_estimate_npr": 0,
                    "practical_note": "Rest or local flexible exploration day.",
                }
            )
            continue

        slot_plan = _assign_slots_for_day(stops)
        ordered_stops = [item["stop"] for item in slot_plan]

        for item in slot_plan:
            stop = item["stop"]
            overview.append(
                {
                    "slot": item["slot"],
                    "title": stop["name"],
                    "note": stop["why_best"],
                    "map_url": stop["map_url"],
                    "duration_hint": "2-3 hrs",
                    "opening_hours": item["opening_hours"],
                    "timing_note": item["timing_note"],
                }
            )
        transport_plan = _build_transport_plan(
            ordered_stops,
            transport_preference,
            safety_priority,
            guide["display_name"],
        )
        day_place_cost = sum(_category_cost_mid(stop.get("category")) for stop in ordered_stops)
        day_transport_cost = sum(leg.get("estimated_cost_npr", 0) for leg in transport_plan)
        day_budget_estimate = int(day_place_cost + day_transport_cost)
        trust = _build_trust_metrics(ordered_stops, transport_plan, safety_priority, pricing_priority)
        day_wise_itinerary.append(
            {
                "day": i + 1,
                "stops": ordered_stops,
                "overview": overview,
                "transport_plan": transport_plan,
                "trust": trust,
                "stop_count": len(ordered_stops),
                "day_budget_estimate_npr": day_budget_estimate,
                "practical_note": f"{len(ordered_stops)} main stops planned with timing validation.",
            }
        )

    trust_scores = [day["trust"]["comfort_score"] for day in day_wise_itinerary if day.get("trust")]
    scam_scores = [day["trust"].get("scam_alert", {}).get("score", 45) for day in day_wise_itinerary if day.get("trust")]
    overall_trust = int(sum(trust_scores) / len(trust_scores)) if trust_scores else 70
    overall_scam_score = int(sum(scam_scores) / len(scam_scores)) if scam_scores else 45
    if overall_scam_score >= 70:
        overall_scam_level = "high"
        overall_scam_badge = "Scam Alert: High"
    elif overall_scam_score >= 45:
        overall_scam_level = "medium"
        overall_scam_badge = "Scam Alert: Medium"
    else:
        overall_scam_level = "low"
        overall_scam_badge = "Scam Alert: Low"
    city_profile = CITY_PROFILES.get(
        city_key,
        {
            "lifestyle": "Local lifestyle and neighborhood culture details will be expanded soon.",
            "main_activities": ["City exploration", "Food tour", "Cultural walk"],
            "street_food_scene": ["Local market snacks", "Tea stalls", "Street momo"],
            "local_connect_tips": ["Talk to local vendors.", "Respect local customs.", "Travel with flexible pace."],
        },
    )

    city_activities = _serialize_city_activities(city_key, all_interests, focus_activities)

    return Response(
        {
            "city": guide["display_name"],
            "city_slug": city_key,
            "tagline": guide["tagline"],
            "inputs": {
                "interests": all_interests,
                "days": days,
                "budget_npr": budget_npr,
                "budget_level": budget_level,
                "family_mode": family_mode,
                "focus_activities": focus_activities,
                "avoid_categories": list(avoid_categories),
                "transport_preference": transport_preference,
                "safety_priority": safety_priority,
                "pricing_priority": pricing_priority,
            },
            "top_highlights": top_highlights,
            "best_places": places,
            "famous_foods": foods,
            "day_wise_itinerary": day_wise_itinerary,
            "activities": city_activities,
            "city_profile": city_profile,
            "comfort_pack": _comfort_pack(guide["display_name"], safety_priority, pricing_priority),
            "anti_scam_pack": _anti_scam_pack(guide["display_name"]),
            "fare_tiers": _fare_tiers(guide["display_name"], budget_level),
            "overall_trust": overall_trust,
            "overall_scam_alert": {
                "score": overall_scam_score,
                "level": overall_scam_level,
                "badge": overall_scam_badge,
            },
            "city_map_url": guide["map_url"],
            "next_expansion": ["Dolpa", "Pathibhara", "Bardia", "Khaptad"],
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def kathmandu_ai_guide(request):
    return city_ai_guide(request, "kathmandu")


@api_view(["GET"])
@permission_classes([AllowAny])
def city_guide_options(request):
    cities = [
        {
            "slug": slug,
            "name": data.get("display_name", slug.title()),
            "tagline": data.get("tagline", ""),
            "default_interests": data.get("default_interests", []),
        }
        for slug, data in CITY_GUIDES.items()
    ]
    cities.sort(key=lambda item: item["name"])
    return Response({"total": len(cities), "cities": cities})


@api_view(["GET"])
@permission_classes([AllowAny])
def trekking_routes_list(request):
    difficulty = str(request.query_params.get("difficulty", "")).strip().lower()
    search = str(request.query_params.get("search", "")).strip().lower()
    max_days_raw = request.query_params.get("max_days")

    max_days = None
    if max_days_raw:
        try:
            max_days = int(max_days_raw)
        except ValueError:
            max_days = None

    routes = []
    for route_id, route in TREKKING_ROUTES.items():
        if difficulty and route.get("difficulty", "").lower() != difficulty:
            continue
        if max_days is not None and route.get("duration_days", 0) > max_days:
            continue
        if search:
            haystack = f"{route.get('name', '')} {route.get('summary', '')} {route.get('region_label', '')}".lower()
            if search not in haystack:
                continue

        routes.append(
            {
                "id": route_id,
                "name": route.get("name"),
                "region_label": route.get("region_label"),
                "difficulty": route.get("difficulty"),
                "duration_days": route.get("duration_days"),
                "max_altitude": route.get("max_altitude"),
                "best_season": route.get("best_season"),
                "summary": route.get("summary"),
                "main_activities": route.get("main_activities", route.get("highlights", [])[:3]),
                "local_lifestyle": route.get(
                    "local_lifestyle",
                    "Tea-house trekking lifestyle with daily interaction across mountain communities.",
                ),
            }
        )

    return Response(
        {
            "total": len(routes),
            "available_difficulties": ["Easy", "Moderate", "Hard"],
            "routes": sorted(routes, key=lambda item: (item["duration_days"], item["name"])),
        }
    )


def _parse_altitude_meters(altitude_text):
    text = str(altitude_text or "")
    matches = re.findall(r"\d[\d,]*", text)
    if not matches:
        return 0
    values = [int(item.replace(",", "")) for item in matches]
    return max(values) if values else 0


def _derive_trek_activities(day):
    highlights = str(day.get("highlights", ""))
    parts = [item.strip() for item in highlights.split(",") if item.strip()]
    if parts:
        return parts[:4]
    route_text = str(day.get("route", ""))
    if route_text:
        return ["Scenic trekking", route_text]
    return ["Scenic trekking", "Tea-house stay"]


TREK_ROUTE_EXPENSE_PROFILES = {
    "poon_hill": {"meals": 1500, "snacks": 400, "porter": 600, "accommodation": 1200, "guide": 700, "misc": 250, "transport": 1200, "ticket": 220, "activity": 550},
    "annapurna_base_camp": {"meals": 2000, "snacks": 650, "porter": 1200, "accommodation": 1900, "guide": 1300, "misc": 380, "transport": 1600, "ticket": 650, "activity": 1050},
    "langtang_valley": {"meals": 1850, "snacks": 620, "porter": 1100, "accommodation": 1750, "guide": 1250, "misc": 350, "transport": 1900, "ticket": 550, "activity": 920},
    "everest_base_camp": {"meals": 2600, "snacks": 900, "porter": 1900, "accommodation": 2800, "guide": 1850, "misc": 600, "transport": 14500, "ticket": 1100, "activity": 1450},
    "mardi_himal": {"meals": 1950, "snacks": 650, "porter": 1150, "accommodation": 1850, "guide": 1300, "misc": 360, "transport": 1500, "ticket": 600, "activity": 980},
    "upper_mustang": {"meals": 2550, "snacks": 900, "porter": 1900, "accommodation": 3000, "guide": 2200, "misc": 700, "transport": 3200, "ticket": 2400, "activity": 1650},
    "gokyo_lakes": {"meals": 2450, "snacks": 850, "porter": 1750, "accommodation": 2600, "guide": 1800, "misc": 560, "transport": 12500, "ticket": 950, "activity": 1400},
    "manaslu_circuit": {"meals": 2350, "snacks": 820, "porter": 1700, "accommodation": 2500, "guide": 1900, "misc": 540, "transport": 2600, "ticket": 1800, "activity": 1350},
}


def _build_day_expense_profile(day, difficulty, route_id=""):
    difficulty_key = str(difficulty or "Moderate").strip().lower()
    difficulty_base = {
        "easy": {"meals": 1600, "snacks": 450, "porter": 700, "accommodation": 1200, "guide": 800, "misc": 250},
        "moderate": {"meals": 1900, "snacks": 600, "porter": 1100, "accommodation": 1700, "guide": 1200, "misc": 350},
        "hard": {"meals": 2300, "snacks": 800, "porter": 1600, "accommodation": 2500, "guide": 1700, "misc": 500},
    }.get(difficulty_key, {"meals": 1900, "snacks": 600, "porter": 1100, "accommodation": 1700, "guide": 1200, "misc": 350})

    route_profile = TREK_ROUTE_EXPENSE_PROFILES.get(str(route_id or "").strip().lower(), {})
    base = {
        "meals": route_profile.get("meals", difficulty_base["meals"]),
        "snacks": route_profile.get("snacks", difficulty_base["snacks"]),
        "porter": route_profile.get("porter", difficulty_base["porter"]),
        "accommodation": route_profile.get("accommodation", difficulty_base["accommodation"]),
        "guide": route_profile.get("guide", difficulty_base["guide"]),
        "misc": route_profile.get("misc", difficulty_base["misc"]),
    }

    route_text = str(day.get("route", "")).lower()
    highlights_text = str(day.get("highlights", "")).lower()
    altitude_value = _parse_altitude_meters(day.get("altitude", ""))

    altitude_bonus = 0
    if altitude_value >= 4500:
        altitude_bonus = 1300
    elif altitude_value >= 3500:
        altitude_bonus = 800
    elif altitude_value >= 2500:
        altitude_bonus = 450

    transport_cost = route_profile.get("transport", 350)
    if "flight" in route_text:
        transport_cost = max(transport_cost, 13000)
    elif any(token in route_text for token in ["pokhara", "kathmandu", "nayapul", "return"]):
        transport_cost = max(transport_cost, 1400)

    ticketing_cost = route_profile.get("ticket", 250)
    if any(token in highlights_text for token in ["base camp", "viewpoint", "monastery", "hot spring", "permit"]):
        ticketing_cost = max(ticketing_cost, 700)

    activity_cost = route_profile.get("activity", 600)
    if any(token in highlights_text for token in ["sunrise", "base camp", "acclimatization", "glacier", "summit"]):
        activity_cost = max(activity_cost, 1200)

    if any(token in route_text for token in ["acclimatization", "rest"]):
        transport_cost = int(transport_cost * 0.4)
        porter_discount = int(base["porter"] * 0.3)
        base["porter"] = max(350, base["porter"] - porter_discount)
        activity_cost = int(activity_cost * 0.85)

    activities = _derive_trek_activities(day)
    per_activity = max(250, int(activity_cost / max(1, len(activities))))

    breakdown = {
        "breakfast_lunch_dinner": base["meals"] + int(altitude_bonus * 0.2),
        "snacks_and_hot_drinks": base["snacks"] + int(altitude_bonus * 0.1),
        "ticketing_and_permits": ticketing_cost,
        "porter": base["porter"],
        "guide": base["guide"],
        "accommodation": base["accommodation"] + int(altitude_bonus * 0.4),
        "transport": transport_cost,
        "activities": activity_cost,
        "miscellaneous": base["misc"] + int(altitude_bonus * 0.2),
    }

    daily_total = sum(breakdown.values())
    range_low = int(round(daily_total * 0.9 / 100.0) * 100)
    range_high = int(round(daily_total * 1.1 / 100.0) * 100)

    return {
        "activities": activities,
        "activity_costs_npr": [
            {"name": item, "estimated_npr": per_activity}
            for item in activities
        ],
        "expense_breakdown_npr": breakdown,
        "estimated_rate_npr": f"NPR {range_low} - {range_high}",
        "estimated_rate_total_npr": daily_total,
    }


def _enrich_trekking_itinerary(route):
    difficulty = route.get("difficulty", "Moderate")
    route_id = route.get("id", "")
    enriched_days = []
    for day in route.get("day_wise_itinerary", []):
        day_payload = dict(day)
        generated = _build_day_expense_profile(day_payload, difficulty, route_id)
        day_payload["activities"] = day_payload.get("activities") or generated["activities"]
        day_payload["activity_costs_npr"] = day_payload.get("activity_costs_npr") or generated["activity_costs_npr"]
        day_payload["expense_breakdown_npr"] = day_payload.get("expense_breakdown_npr") or generated["expense_breakdown_npr"]
        day_payload["estimated_rate_npr"] = day_payload.get("estimated_rate_npr") or generated["estimated_rate_npr"]
        day_payload["estimated_rate_total_npr"] = day_payload.get("estimated_rate_total_npr") or generated["estimated_rate_total_npr"]
        enriched_days.append(day_payload)
    return enriched_days


@api_view(["GET"])
@permission_classes([AllowAny])
def trekking_route_detail(request, route_id):
    normalized_route_id = str(route_id).strip().lower().replace("-", "_")
    route = TREKKING_ROUTES.get(normalized_route_id)

    if not route:
        return Response(
            {
                "error": "Trekking route not found",
                "available_routes": sorted(TREKKING_ROUTES.keys()),
            },
            status=404,
        )

    enriched_itinerary = _enrich_trekking_itinerary(route)

    return Response(
        {
            "id": route.get("id"),
            "name": route.get("name"),
            "region_label": route.get("region_label"),
            "difficulty": route.get("difficulty"),
            "duration_days": route.get("duration_days"),
            "max_altitude": route.get("max_altitude"),
            "best_season": route.get("best_season"),
            "summary": route.get("summary"),
            "highlights": route.get("highlights", []),
            "ordered_info": route.get("ordered_info", []),
            "main_activities": route.get("main_activities", route.get("highlights", [])[:3]),
            "local_lifestyle": route.get(
                "local_lifestyle",
                "Tea-house trekking lifestyle with daily interaction across mountain communities.",
            ),
            "region_foods": route.get("region_foods", []),
            "area_story": route.get("area_story", route.get("summary")),
            "custom_map_image": f"/api/trips/media/trek/{normalized_route_id}.svg",
            "day_wise_itinerary": enriched_itinerary,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def trekking_offline_pack(request, route_id):
    normalized_route_id = str(route_id).strip().lower().replace("-", "_")
    route = TREKKING_ROUTES.get(normalized_route_id)

    if not route:
        return Response(
            {
                "error": "Trekking route not found",
                "available_routes": sorted(TREKKING_ROUTES.keys()),
            },
            status=404,
        )

    checklist = [
        "Download offline maps before leaving city network.",
        "Carry printed permit copies and emergency contact sheet.",
        "Pack water purification and basic first-aid kit.",
        "Save tea-house stop points and next-day altitude targets.",
        "Share route and ETA with one trusted contact.",
    ]

    rescue_contacts = [
        "Tourist Police Nepal: 1144",
        "Emergency Police: 100",
        "Ambulance: 102",
    ]

    enriched_itinerary = _enrich_trekking_itinerary(route)

    return Response(
        {
            "id": route.get("id"),
            "name": route.get("name"),
            "difficulty": route.get("difficulty"),
            "duration_days": route.get("duration_days"),
            "max_altitude": route.get("max_altitude"),
            "best_season": route.get("best_season"),
            "summary": route.get("summary"),
            "custom_map_image": f"/api/trips/media/trek/{normalized_route_id}.svg",
            "ordered_info": route.get("ordered_info", []),
            "main_activities": route.get("main_activities", route.get("highlights", [])[:3]),
            "local_lifestyle": route.get(
                "local_lifestyle",
                "Tea-house trekking lifestyle with daily interaction across mountain communities.",
            ),
            "region_foods": route.get("region_foods", []),
            "area_story": route.get("area_story", route.get("summary")),
            "day_wise_itinerary": enriched_itinerary,
            "offline_checklist": checklist,
            "emergency_contacts": rescue_contacts,
            "recommended_downloads": [
                "Offline topographic map",
                "Nepal weather snapshot",
                "Permit and ID scans",
            ],
        }
    )


# --- Enquiry API (simple server-side saving for booking enquiries) ---
from .models import Enquiry
from rest_framework import status
from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)
from rest_framework import permissions


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ["id", "name", "email", "city", "activity_name", "activity_id", "message", "status", "operator_notes", "created_at", "updated_at"]


@api_view(["POST"])
@permission_classes([AllowAny])
def create_enquiry(request):
    data = request.data or {}
    # allow activity payload or flat fields
    payload = {
        "name": data.get("name") or data.get("contact_name") or "",
        "email": data.get("email") or data.get("contact_email") or "",
        "city": data.get("city") or data.get("activity_city") or "",
        "activity_name": data.get("activity_name") or (data.get("activity") or {}).get("name") or "",
        "activity_id": data.get("activity_id") or (data.get("activity") or {}).get("id") or None,
        "message": data.get("message") or "",
        "status": Enquiry.STATUS_NEW,
    }
    serializer = EnquirySerializer(data=payload)
    if serializer.is_valid():
        enquiry = serializer.save()

        # Try sending a notification email to site admins (best-effort)
        try:
            admin_recipients = [addr for _, addr in getattr(settings, "ADMINS", [])]
            if not admin_recipients:
                admin_recipients = [getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", "book@trailmate.local")]

            subject = f"New enquiry: {enquiry.activity_name or 'General'} from {enquiry.name}"
            body = (
                f"Name: {enquiry.name}\n"
                f"Email: {enquiry.email}\n"
                f"City: {enquiry.city}\n"
                f"Activity: {enquiry.activity_name}\n\n"
                f"Message:\n{enquiry.message}\n\n"
                f"Received at: {enquiry.created_at}\n"
            )
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
            if from_email and admin_recipients:
                send_mail(subject, body, from_email, admin_recipients, fail_silently=True)
        except Exception as exc:
            logger.exception("Failed to send enquiry notification email: %s", exc)

        return Response(
            {
                **EnquirySerializer(enquiry).data,
                "operator_message": "The enquiry is now visible on the operator dashboard and marked as new.",
            },
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnquiryListView(generics.ListAPIView):
    """Admin-only listing of enquiries."""
    queryset = Enquiry.objects.all().order_by("-created_at")
    serializer_class = EnquirySerializer
    permission_classes = [permissions.IsAdminUser]
