from django.contrib import admin
from .models import Offer, UserOffer

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'discount_percent', 'discount_amount', 'is_active', 'current_uses', 'max_uses')
    list_filter = ('is_active', 'valid_from', 'valid_until')
    search_fields = ('title', 'code', 'description')
    readonly_fields = ('current_uses',)

@admin.register(UserOffer)
class UserOfferAdmin(admin.ModelAdmin):
    list_display = ('user', 'offer', 'claimed_at', 'used_at', 'is_used')
    list_filter = ('is_used', 'claimed_at', 'used_at')
    search_fields = ('user__username', 'user__email', 'offer__title', 'offer__code')
    readonly_fields = ('claimed_at',)