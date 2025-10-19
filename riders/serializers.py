# riders/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import RiderLocation, RiderProfile

User = get_user_model()

class RiderLocationSerializer(serializers.ModelSerializer):
    rider = serializers.SerializerMethodField()
    rider_display = serializers.SerializerMethodField()

    class Meta:
        model = RiderLocation
        fields = [
            "id",
            "rider",
            "rider_display",
            "latitude",
            "longitude",
            "accuracy",
            "heading",
            "speed",
            "recorded_at",
            "created_at",
        ]

    def get_rider(self, obj):
        return getattr(obj.rider, "id", None)

    def get_rider_display(self, obj):
        user = getattr(obj, "rider", None)
        profile = getattr(user, "rider_profile", None)
        if profile and getattr(profile, "display_name", ""):
            return profile.display_name
        return getattr(user, "username", None)


class RiderProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for RiderProfile. Exposes the related user's username,
    and file URLs for id/license documents.
    """
    user = serializers.CharField(source="user.username", read_only=True)
    id_document = serializers.FileField(read_only=True)
    license_document = serializers.FileField(read_only=True)

    class Meta:
        model = RiderProfile
        fields = [
            "id",
            "user",
            "display_name",
            "phone",
            "vehicle_type",
            "vehicle_reg",
            "is_active",
            "rating",
            "completed_jobs",
            "id_document",
            "license_document",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "rating",
            "completed_jobs",
            "created_at",
            "updated_at",
        ]
