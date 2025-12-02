# orders/models.py
from django.db import models
from django.conf import settings
from services.models import Service
from users.models import Location
from decimal import Decimal
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('picked', 'Picked Up'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('pending_assignment', 'Pending Assignment'),  # For manual/walk-in orders awaiting rider assignment
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,            # allow null
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    # Support multiple services per order
    services = models.ManyToManyField(Service, related_name="orders")
    
    # Keep service field for backward compatibility (will be the first service or None)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="primary_orders")
    service_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        help_text="The location where this order is being processed"
    )
    code = models.CharField(max_length=32, unique=True, blank=True)  # e.g. "WW-12345"
    pickup_address = models.TextField()
    dropoff_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    urgency = models.IntegerField(default=1)  # e.g. 1–5 urgency level
    items = models.IntegerField(default=1)    # number of items
    package = models.IntegerField(default=1, blank=True)  # you already had this
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # store numeric
    # Staff-entered actual price paid (may differ from estimate)
    actual_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual price paid for the order recorded by staff"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    estimated_delivery = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)  # helpful to record real delivery time
    rider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_orders",
    )
    # Rider-added details during pickup
    quantity = models.IntegerField(
        null=True,
        blank=True,
        help_text="Quantity of items picked up by rider"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Rider's notes about the order"
    )
    # Optional requested pickup datetime set by customer when scheduling
    requested_pickup_at = models.DateTimeField(null=True, blank=True)
    
    # Fields for staff-created manual orders
    order_type = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online Order'),
            ('manual', 'Staff-Created Order'),
        ],
        default='online',
        help_text="Whether order was created online or manually by staff"
    )
    drop_off_type = models.CharField(
        max_length=20,
        choices=[
            ('delivery', 'Customer Delivery'),
            ('walk_in', 'Walk-in Customer'),
            ('phone', 'Phone Order'),
        ],
        default='delivery',
        help_text="How the order was dropped off/created"
    )
    # Customer details for manual orders (when user is None or guest)
    customer_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Customer name for manual/walk-in orders"
    )
    customer_phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Customer phone for manual/walk-in orders"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_orders",
        help_text="Staff member who created this manual order"
    )


    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"WW-{uuid.uuid4().hex[:6].upper()}"
        # Set the first service as primary service for backward compatibility
        if not self.service and self.pk:
            first_service = self.services.first()
            if first_service:
                self.service = first_service
        super().save(*args, **kwargs)

    def get_total_price(self):
        """Calculate total price from all services"""
        return sum(service.price for service in self.services.all())

    def __str__(self):
        return f"Order #{self.id} - {self.user.username if self.user else 'Guest'}"

    class Meta:
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['rider', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['code']),
        ]


class OrderEvent(models.Model):
    """A lightweight audit/event record for actions taken on an Order.

    Examples: order_created, status_changed, pickup_details_recorded, assigned_rider
    """
    order = models.ForeignKey(Order, related_name='events', on_delete=models.CASCADE)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='order_events',
    )
    event_type = models.CharField(max_length=64)
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"OrderEvent({self.order.code}): {self.event_type} @ {self.created_at}"
