from django.db import models
from django.conf import settings

class Subscription(models.Model):
    FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('bi-weekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES
    )
    active = models.BooleanField(default=True)
    next_pickup_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.frequency} subscription"