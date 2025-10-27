from django.db import models
from users.models import User
from django.utils import timezone

class Offer(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    discount_percent = models.IntegerField(default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    code = models.CharField(max_length=50, unique=True)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    max_uses = models.IntegerField(null=True, blank=True)
    current_uses = models.IntegerField(default=0)
    
    def __str__(self):
        return self.title

class UserOffer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claimed_offers')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='user_claims')
    claimed_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'offer')
        ordering = ['-claimed_at']

    def __str__(self):
        return f"{self.user.username} - {self.offer.title}"