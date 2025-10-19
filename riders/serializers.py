# riders/serializers.py
from rest_framework import serializers
from .models import RiderLocation

class RiderLocationSerializer(serializers.ModelSerializer):
    # returns rider id (or username if you prefer)
    rider = serializers.SerializerMethodField()
    # friendlier display name for UI
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
        # return a simple identifier (id). You can return username or nested object if you want.
        user = getattr(obj, "rider", None)
        return getattr(user, "id", None)

    def get_rider_display(self, obj):
        user = getattr(obj, "rider", None)
        # Prefer RiderProfile.display_name if available, otherwise username
        profile = getattr(user, "rider_profile", None)
        if profile and getattr(profile, "display_name", ""):
            return profile.display_name
        return getattr(user, "username", None)
