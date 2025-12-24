from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class GameWallet(models.Model):
    """Tracks game wallet balance for each user."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='game_wallet'
    )
    balance = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')
    total_winnings = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')
    total_losses = models.DecimalField(max_digits=12, decimal_places=2, default='0.00')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Game Wallet"
        verbose_name_plural = "Game Wallets"

    def __str__(self):
        return f"Game Wallet - {self.user.username} (KES {self.balance})"

    def add_funds(self, amount: Decimal, source: str = 'deposit', payment_id: int = None, notes: str = ''):
        """Add funds to wallet and create transaction record."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.balance += amount
        self.total_deposits += amount
        self.updated_at = timezone.now()
        self.save()

        # Create transaction record
        GameTransaction.objects.create(
            wallet=self,
            transaction_type='deposit',
            amount=amount,
            source=source,
            payment_id=payment_id,
            notes=notes
        )

        return self.balance

    def deduct_funds(self, amount: Decimal, reason: str = 'game_play', notes: str = ''):
        """Deduct funds from wallet for gameplay."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if self.balance < amount:
            raise ValueError(f"Insufficient balance. Available: {self.balance}, Required: {amount}")
        
        self.balance -= amount
        self.total_losses += amount
        self.updated_at = timezone.now()
        self.save()

        # Create transaction record
        GameTransaction.objects.create(
            wallet=self,
            transaction_type='debit',
            amount=amount,
            source=reason,
            notes=notes
        )

        return self.balance

    def add_winnings(self, amount: Decimal, game_name: str = '', notes: str = ''):
        """Add winnings to wallet."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        self.balance += amount
        self.total_winnings += amount
        self.updated_at = timezone.now()
        self.save()

        # Create transaction record
        GameTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            source='game_winnings',
            notes=f"Won in {game_name}: {notes}"
        )

        return self.balance


class GameTransaction(models.Model):
    """Records all transactions on a game wallet."""
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('debit', 'Debit (Game Play)'),
        ('credit', 'Credit (Winnings)'),
        ('refund', 'Refund'),
        ('withdrawal', 'Withdrawal'),
    ]

    wallet = models.ForeignKey(GameWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(
        max_length=100,
        help_text="e.g., 'mpesa', 'game_play', 'game_winnings', etc."
    )
    payment_id = models.PositiveIntegerField(null=True, blank=True, help_text="Reference to Payment model if from payment")
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.wallet.user.username} - KES {self.amount}"
