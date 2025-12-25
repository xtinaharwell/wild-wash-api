from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


def get_algorithm_choices():
    """Get algorithm choices dynamically."""
    try:
        from .algorithms import ALGORITHM_REGISTRY
        return [(key, key.replace('_', ' ').title()) for key in ALGORITHM_REGISTRY.keys()]
    except ImportError:
        return [('balanced', 'Balanced')]


class SpinAlgorithmConfiguration(models.Model):
    """Configuration for spin algorithms."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of this algorithm configuration"
    )
    algorithm_key = models.CharField(
        max_length=50,
        choices=get_algorithm_choices(),
        help_text="Which algorithm to use"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Only one algorithm can be active at a time"
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time to auto-activate this algorithm (optional)"
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time to deactivate this algorithm (optional)"
    )
    days_of_week = models.CharField(
        max_length=20,
        default='0,1,2,3,4,5,6',
        help_text="Comma-separated day numbers: 0=Mon, 6=Sun"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of when/why to use this algorithm"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Spin Algorithm Configuration"
        verbose_name_plural = "Spin Algorithm Configurations"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        status = "✓ ACTIVE" if self.is_active else "○ inactive"
        return f"{self.name} ({self.algorithm_key}) {status}"
    
    def save(self, *args, **kwargs):
        """Ensure only one algorithm is active at a time."""
        if self.is_active:
            SpinAlgorithmConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    def get_algorithm_info(self):
        """Get algorithm instance and metadata."""
        from .algorithms import get_algorithm
        algo = get_algorithm(self.algorithm_key)
        return {
            'key': self.algorithm_key,
            'name': algo.name,
            'description': algo.description,
            'segments': algo.segments
        }


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
