from django.contrib import admin
from .models import Payment, MpesaSTKRequest, BNPLUser

@admin.register(BNPLUser)
class BNPLUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'phone_number', 'credit_limit', 'current_balance', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('user__username', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

class MpesaSTKInline(admin.TabularInline):
    model = MpesaSTKRequest
    extra = 0
    readonly_fields = ("checkout_request_id", "merchant_request_id", "result_code", "created_at")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_id", "provider", "amount", "currency", "status", "created_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("provider_reference", "user__username", "phone_number")
    readonly_fields = ("created_at", "updated_at", "initiated_at", "completed_at")
    inlines = [MpesaSTKInline]
    ordering = ("-created_at",)

@admin.register(MpesaSTKRequest)
class MpesaSTKRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "payment", "checkout_request_id", "merchant_request_id", "result_code", "created_at")
    search_fields = ("checkout_request_id", "merchant_request_id", "payment__provider_reference")
    readonly_fields = ("created_at", "updated_at")
