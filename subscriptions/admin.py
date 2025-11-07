from django.contrib import admin
from .models import Subscription

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'frequency', 'active', 'next_pickup_date', 'created_at']
    list_filter = ['active', 'frequency']
    search_fields = ['user__username', 'user__email']
    date_hierarchy = 'created_at'