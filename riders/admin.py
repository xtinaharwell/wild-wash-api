from django.contrib import admin
from .models import RiderProfile, RiderLocation

@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "display_name", "phone", "vehicle_type", "vehicle_reg", "is_active")
    search_fields = ("display_name", "user__username", "phone", "vehicle_reg")
    list_filter = ("vehicle_type", "is_active")
    readonly_fields = ("created_at", "updated_at")

@admin.register(RiderLocation)
class RiderLocationAdmin(admin.ModelAdmin):
    list_display = ("id", "rider", "latitude", "longitude", "recorded_at")
    search_fields = ("rider__username",)
    list_filter = ("recorded_at",)
    readonly_fields = ("created_at",)
    ordering = ("-recorded_at",)
