"""
Combined models.py content for two Django apps: `riders` and `payments`.

Save the `riders` portion to `riders/models.py` and the `payments` portion to `payments/models.py` in your project.

These models assume you have a custom user model (settings.AUTH_USER_MODEL) and an `orders.Order` model.
"""

# ---------------------------
# riders/models.py
# ---------------------------
from django.conf import settings
from django.db import models
from django.utils import timezone


class RiderProfile(models.Model):
    """Optional extended profile for users that act as riders/drivers.

    If you already store rider fields on your custom User model (is_rider flag),
    you can use this profile for extra per-rider data (vehicle, documents, rating).
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rider_profile')
    display_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    vehicle_type = models.CharField(max_length=60, blank=True, help_text='e.g. Motorcycle, Car, Van')
    vehicle_reg = models.CharField(max_length=40, blank=True, help_text='Vehicle registration number')
    is_active = models.BooleanField(default=True)

    # verification / docs
    id_document = models.FileField(upload_to='riders/docs/', blank=True, null=True)
    license_document = models.FileField(upload_to='riders/docs/', blank=True, null=True)

    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    completed_jobs = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Rider profile'
        verbose_name_plural = 'Rider profiles'

    def __str__(self):
        return self.display_name or getattr(self.user, 'username', str(self.user))


class RiderLocation(models.Model):
    """Stores periodic location updates from riders for live tracking.

    A rider device (mobile app) should POST GPS updates to an endpoint that
    creates RiderLocation rows. For real-time apps you can combine this with
    Django Channels / Redis to broadcast locations.
    """
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy = models.FloatField(blank=True, null=True, help_text='GPS accuracy in meters')
    heading = models.FloatField(blank=True, null=True, help_text='Direction in degrees')
    speed = models.FloatField(blank=True, null=True, help_text='Speed in m/s')

    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        indexes = [models.Index(fields=['rider', 'recorded_at'])]

    def __str__(self):
        return f"{self.rider} @ {self.latitude},{self.longitude} ({self.recorded_at.isoformat()})"

