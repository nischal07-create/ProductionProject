from datetime import date
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Destination, Activity, TripPlan


User = get_user_model()


class TripApiTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username="alice", password="Password123!")
		self.destination = Destination.objects.create(name="Kathmandu", country="Nepal")
		self.activity = Activity.objects.create(
			destination=self.destination,
			name="Heritage Walk",
			description="Durbar Square tour",
			tags="culture,history",
			cost_estimate="25.00",
			duration_hours="3.0",
			indoor=False,
			family_friendly=True,
		)

	def test_public_catalogue_endpoints(self):
		destination_response = self.client.get(reverse("destination-list"))
		activity_response = self.client.get(reverse("activity-list"))

		self.assertEqual(destination_response.status_code, status.HTTP_200_OK)
		self.assertEqual(activity_response.status_code, status.HTTP_200_OK)

	def test_trip_plan_requires_auth(self):
		response = self.client.get(reverse("trip-plan-list-create"))
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_authenticated_user_can_create_and_list_own_trip_plan(self):
		self.client.force_authenticate(user=self.user)

		create_response = self.client.post(
			reverse("trip-plan-list-create"),
			{
				"title": "Weekend in Kathmandu",
				"destination": self.destination.id,
				"start_date": date(2026, 4, 10),
				"end_date": date(2026, 4, 12),
				"budget": "300.00",
				"notes": "Focus on local food and culture",
			},
			format="json",
		)
		self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

		list_response = self.client.get(reverse("trip-plan-list-create"))
		self.assertEqual(list_response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(list_response.json()), 1)
		self.assertEqual(TripPlan.objects.filter(user=self.user).count(), 1)
