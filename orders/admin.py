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
    list_display = ("id", "user", "services_display", "rider", "status", "urgency", "estimated_delivery", "created_at")
    list_filter = ("status", "urgency", "created_at", "rider")
    search_fields = ("user__username", "user__email", "services__name", "code")
    readonly_fields = ("created_at", "updated_at", "code", "services_display_readonly")
    actions = [make_ready, make_delivered, unassign_rider]
    ordering = ("-created_at",)
    list_per_page = 50  # Limit results per page to improve load time
    list_select_related = ("user", "service", "rider", "service_location")  # Optimize queries
    filter_horizontal = ("services",)  # Better UI for M2M field

    fieldsets = (
        (None, {"fields": ("code", "user", "services_display_readonly", "pickup_address", "dropoff_address", "status")}),
        ("Assignment", {"fields": ("rider", "service_location")}),
        ("Scheduling & urgency", {"fields": ("urgency", "estimated_delivery")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")} ),
    )

    def services_display(self, obj):
        """Display all services for this order in list view"""
        services = obj.services.all()
        if services.exists():
            return ", ".join([service.name for service in services])
        elif obj.service:
            return obj.service.name
        return "No services"
    services_display.short_description = "Services"

    def services_display_readonly(self, obj):
        """Display services in readonly detail view"""
        if not obj.id:
            return "N/A"
        services = obj.services.all()
        if services.exists():
            html_list = "<ul style='margin: 0; padding-left: 20px;'>"
            for service in services:
                html_list += f"<li>{service.name} - KSh {service.price:,.0f}</li>"
            html_list += "</ul>"
            return html_list
        elif obj.service:
            return f"{obj.service.name} - KSh {obj.service.price:,.0f}"
        return "No services"
    services_display_readonly.short_description = "Services"
    services_display_readonly.allow_tags = True
