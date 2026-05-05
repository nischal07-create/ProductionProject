from django.contrib import admin
from .models import Enquiry, Destination, Activity, TripPlan, TripPlanActivity


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
	list_display = ("activity_name", "city", "name", "email", "status", "created_at")
	list_editable = ("status",)
	list_filter = ("city",)
	search_fields = ("activity_name", "name", "email", "message", "operator_notes")


admin.site.register(Destination)
admin.site.register(Activity)
admin.site.register(TripPlan)
admin.site.register(TripPlanActivity)
