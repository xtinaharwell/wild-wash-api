from django.contrib import admin
from .models import Order

@admin.action(description="Mark selected orders as Ready")
def make_ready(modeladmin, request, queryset):
    queryset.update(status='ready')

@admin.action(description="Mark selected orders as Delivered")
def make_delivered(modeladmin, request, queryset):
    queryset.update(status='delivered')

@admin.action(description="Unassign rider from selected orders")
def unassign_rider(modeladmin, request, queryset):
    queryset.update(rider=None)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "service", "rider", "status", "urgency", "estimated_delivery", "created_at")
    list_filter = ("status", "urgency", "created_at", "rider")
    search_fields = ("user__username", "user__email", "service__name", "id")
    readonly_fields = ("created_at", "updated_at")
    actions = [make_ready, make_delivered, unassign_rider]
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("user", "service", "pickup_address", "dropoff_address", "status")}),
        ("Assignment", {"fields": ("rider",)}),
        ("Scheduling & urgency", {"fields": ("urgency", "estimated_delivery")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")} ),
    )
