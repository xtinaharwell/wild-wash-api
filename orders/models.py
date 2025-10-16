from django.db import models
from django.conf import settings
from services.models import Service

class Order(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('picked', 'Picked Up'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    pickup_address = models.TextField()
    dropoff_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    urgency = models.IntegerField(default=1)  # e.g. 1–5 urgency level
    # packages = models.IntegerField(default=1)  # number of packages
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
