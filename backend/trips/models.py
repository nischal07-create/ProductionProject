from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()

class Destination(models.Model):
    name = models.CharField(max_length=120)      # e.g., Kathmandu
    country = models.CharField(max_length=80, default="Nepal")

    def __str__(self):
        return f"{self.name}, {self.country}"

class Activity(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name="activities")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=300, blank=True)  # comma-separated tags
    cost_estimate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)
    indoor = models.BooleanField(default=False)
    family_friendly = models.BooleanField(default=True)
    photo_urls = models.JSONField(default=list, blank=True)  # List of photo URLs for the activity

    def __str__(self):
        return f"{self.name} ({self.destination.name})"


class TripPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trip_plans")
    title = models.CharField(max_length=150)
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name="trip_plans")
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class TripPlanActivity(models.Model):
    trip_plan = models.ForeignKey(TripPlan, on_delete=models.CASCADE, related_name="items")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="trip_items")
    day_number = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=1)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["day_number", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["trip_plan", "day_number", "order"],
                name="unique_trip_plan_day_order",
            )
        ]

    def __str__(self):
        return f"{self.trip_plan.title} - Day {self.day_number} #{self.order}"


class Enquiry(models.Model):
    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_BOOKED = "booked"
    STATUS_CLOSED = "closed"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_BOOKED, "Booked"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=160)
    email = models.EmailField()
    city = models.CharField(max_length=120, blank=True)
    activity_name = models.CharField(max_length=200, blank=True)
    activity_id = models.PositiveIntegerField(null=True, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)
    operator_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Enquiry: {self.activity_name or 'general'} by {self.name} <{self.email}>"