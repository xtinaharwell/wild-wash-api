# financing/admin.py
from django.contrib import admin
from .models import LoanApplication, LoanCollateral, LoanGuarantor, LoanRepayment


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'loan_type', 'loan_amount', 'status', 'created_at')
    list_filter = ('status', 'loan_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'reviewed_at', 'approved_at', 'funded_at', 'total_interest', 'total_repayment')
    
    fieldsets = (
        ('Application Details', {
            'fields': ('id', 'user', 'loan_type', 'status', 'created_at', 'updated_at')
        }),
        ('Loan Information', {
            'fields': ('loan_amount', 'duration_days', 'purpose', 'daily_interest_rate', 'total_interest', 'total_repayment')
        }),
        ('Order Collateral', {
            'fields': ('order', 'order_value'),
            'classes': ('collapse',)
        }),
        ('Repayment', {
            'fields': ('amount_repaid', 'approved_at', 'funded_at', 'due_date')
        }),
        ('Review', {
            'fields': ('reviewed_at', 'reviewed_by', 'reviewer_notes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_applications', 'reject_applications', 'fund_applications']
    
    def approve_applications(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='approved', approved_at=timezone.now(), reviewed_by=request.user)
        self.message_user(request, f'{updated} applications approved.')
    approve_applications.short_description = 'Approve selected applications'
    
    def reject_applications(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected', reviewed_by=request.user)
        self.message_user(request, f'{updated} applications rejected.')
    reject_applications.short_description = 'Reject selected applications'
    
    def fund_applications(self, request, queryset):
        updated = queryset.filter(status='approved').update(status='active', funded_at=timezone.now())
        self.message_user(request, f'{updated} applications funded.')
    fund_applications.short_description = 'Fund selected applications'


@admin.register(LoanCollateral)
class LoanCollateralAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan_application', 'collateral_type', 'estimated_value', 'created_at')
    list_filter = ('collateral_type', 'created_at')
    search_fields = ('loan_application__id', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(LoanGuarantor)
class LoanGuarantorAdmin(admin.ModelAdmin):
    list_display = ('name', 'loan_application', 'relationship', 'phone_number', 'email')
    list_filter = ('relationship', 'created_at')
    search_fields = ('name', 'email', 'phone_number', 'loan_application__id')
    readonly_fields = ('id', 'created_at')


@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'loan_application', 'amount', 'status', 'payment_method', 'created_at')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('loan_application__id', 'transaction_id')
    readonly_fields = ('id', 'created_at', 'completed_at')


from django.utils import timezone
