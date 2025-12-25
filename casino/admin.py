from django.contrib import admin
from .models import GameWallet, GameTransaction, SpinAlgorithmConfiguration


@admin.register(SpinAlgorithmConfiguration)
class SpinAlgorithmConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'algorithm_key', 'is_active', 'start_time', 'end_time', 'updated_at')
    list_filter = ('is_active', 'algorithm_key', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Algorithm Configuration', {
            'fields': ('name', 'algorithm_key', 'is_active')
        }),
        ('Schedule (Optional)', {
            'fields': ('start_time', 'end_time', 'days_of_week'),
            'description': 'Leave empty for manual control. Use 0=Monday, 6=Sunday for days_of_week.'
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Log algorithm changes."""
        if obj.is_active:
            # Notify that this algorithm is now active
            pass
        super().save_model(request, obj, form, change)


@admin.register(GameWallet)
class GameWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'total_deposits', 'total_winnings', 'total_losses', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'total_deposits', 'total_winnings', 'total_losses')
    fields = ('user', 'balance', 'total_deposits', 'total_winnings', 'total_losses', 'created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Wallets are created automatically for users
        return False
    
    def save_model(self, request, obj, form, change):
        """Log balance changes to transaction history"""
        if change:  # If editing an existing wallet
            try:
                original = GameWallet.objects.get(pk=obj.pk)
                balance_change = obj.balance - original.balance
                
                if balance_change != 0:
                    # Create a transaction record for admin adjustment
                    if balance_change > 0:
                        transaction_type = 'credit'
                        source = 'admin_credit'
                    else:
                        transaction_type = 'debit'
                        source = 'admin_debit'
                        balance_change = abs(balance_change)
                    
                    GameTransaction.objects.create(
                        wallet=obj,
                        transaction_type=transaction_type,
                        amount=balance_change,
                        source=source,
                        notes=f"Admin adjustment by {request.user.username}"
                    )
            except GameWallet.DoesNotExist:
                pass
        
        super().save_model(request, obj, form, change)


@admin.register(GameTransaction)
class GameTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'source', 'created_at')
    search_fields = ('wallet__user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Transactions are created by system automatically
        return False
