from django.contrib.auth.models import AbstractUser
from django.db import models

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class User(AbstractUser):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("rider", "Rider"),
        ("admin", "Admin"),
        ("staff", "Staff"),
        ("washer", "Washer"),
        ("folder", "Folder"),
    )

    STAFF_TYPE_CHOICES = (
        ("general", "General Staff"),
        ("washer", "Washer"),
        ("folder", "Folder"),
    )

    phone = models.CharField(max_length=20)  # Required phone number
    service_location = models.ForeignKey(
        Location, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='staff_members',
        help_text="Location where staff member works"
    )
    # Customer's address/location
    location = models.CharField(max_length=100, blank=True, null=True)
    # Customer's default pickup address for bookings
    pickup_address = models.TextField(blank=True, null=True, help_text="Default pickup address for service bookings")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")
    staff_type = models.CharField(
        max_length=20,
        choices=STAFF_TYPE_CHOICES,
        default="general",
        help_text="Type of staff: General, Washer, or Folder"
    )
    is_location_admin = models.BooleanField(
        default=False,
        help_text="Designates whether this user can manage other users in their location"
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
