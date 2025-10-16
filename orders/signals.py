# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from notifications.models import Notification

@receiver(post_save, sender=Order)
def order_status_update(sender, instance, **kwargs):
    Notification.objects.create(
        user=instance.user,
        order=instance,
        message=f"Your order is now {instance.get_status_display()}."
    )
