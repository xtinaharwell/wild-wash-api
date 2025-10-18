# orders/models.py
from django.db import models
from django.conf import settings
from services.models import Service
from decimal import Decimal
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('picked', 'Picked Up'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),    # add cancelled to match frontend
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,            # allow null
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    code = models.CharField(max_length=32, unique=True, blank=True)  # e.g. "WW-12345"
    pickup_address = models.TextField()
    dropoff_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    urgency = models.IntegerField(default=1)  # e.g. 1–5 urgency level
    items = models.IntegerField(default=1)    # number of items
    package = models.IntegerField(default=1, blank=True)  # you already had this
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # store numeric
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)  # helpful to record real delivery time



    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"WW-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"
