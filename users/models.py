from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import random
import string

def format_phone_number(phone_number):
    """
    Format phone number to international format (+254...)
    Handles various input formats:
    - 254718693484 -> +254718693484
    - +254718693484 -> +254718693484
    - 0718693484 -> +254718693484
    - 0112345678 -> +254112345678 (landline format)
    - 112345678 -> +254112345678
    """
    if not phone_number:
        return None
    
    # Convert to string and strip whitespace
    phone = str(phone_number).strip()
    
    # Remove any non-digit characters except +
    phone = ''.join(c for c in phone if c.isdigit() or c == '+')
    
    # Remove leading + if present (we'll add it back)
    if phone.startswith('+'):
        phone = phone[1:]
    
    # If starts with 0, replace with 254 (Kenya country code)
    # This handles both mobile (07x) and landline (011, 020, etc.) formats
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    
    # If doesn't start with 254, add it
    if not phone.startswith('254'):
        phone = '254' + phone
    
    # Add + prefix
    phone = '+' + phone
    
    return phone

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

    phone = models.CharField(max_length=20, null=True, blank=True)  # Phone number for SMS notifications and login
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

    def save(self, *args, **kwargs):
        """Auto-format phone number to international format before saving"""
        if self.phone:
            self.phone = format_phone_number(self.phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"


class PasswordResetCode(models.Model):
    """
    Model to store temporary password reset codes sent via SMS.
    Codes expire after 15 minutes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=4)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Code expires in 15 minutes
            self.expires_at = timezone.now() + timezone.timedelta(minutes=15)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Reset code for {self.phone}"
