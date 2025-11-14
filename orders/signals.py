# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from notifications.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=Order)
def order_status_update(sender, instance, created, **kwargs):
    """Create notifications when order is created or updated"""
    
    # Notify customer about order status changes
    if instance.user:
        if created:
            message = f"Your order {instance.code} has been created."
            notification_type = 'new_order'
        else:
            message = f"Your order {instance.code} is now {instance.get_status_display()}."
            notification_type = 'order_update'
        
        Notification.objects.create(
            user=instance.user,
            order=instance,
            message=message,
            notification_type=notification_type
        )
    
    # Notify riders in the order's jurisdiction when a new order is created
    if created and instance.service_location:
        # Get all riders assigned to this location
        riders = User.objects.filter(
            role='rider',
            service_location=instance.service_location,
            is_active=True
        )
        
        # Create notification for each rider
        for rider in riders:
            message = f"New order {instance.code} in your area. Pickup: {instance.pickup_address[:50]}..."
            Notification.objects.create(
                user=rider,
                order=instance,
                message=message,
                notification_type='new_order'
            )

