from django.contrib import admin
from .models import GameWallet, GameTransaction


@admin.register(GameWallet)
class GameWalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'total_deposits', 'total_winnings', 'total_losses', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'balance', 'total_deposits', 'total_winnings', 'total_losses')
    
    def has_add_permission(self, request):
        # Wallets are created automatically for users
        return False


@admin.register(GameTransaction)
class GameTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount', 'source', 'created_at')
    list_filter = ('transaction_type', 'source', 'created_at')
    search_fields = ('wallet__user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    
    def has_add_permission(self, request):
        # Transactions are created by system automatically
        return False
