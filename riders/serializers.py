# riders/serializers.py
from rest_framework import serializers
from .models import RiderProfile, RiderLocation
from django.contrib.auth import get_user_model

User = get_user_model()


class RiderProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

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
            "id_document",
            "license_document",
            "rating",
            "completed_jobs",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "rating", "completed_jobs", "created_at", "updated_at"]

    def create(self, validated_data):
        # if you want to auto-attach the logged-in user:
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            validated_data["user"] = request.user
        return super().create(validated_data)


class RiderLocationSerializer(serializers.ModelSerializer):
    rider = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RiderLocation
        fields = [
            "id",
            "rider",
            "latitude",
            "longitude",
            "accuracy",
            "heading",
            "speed",
            "recorded_at",
            "created_at",
        ]
        read_only_fields = ["id", "rider", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            validated_data["rider"] = request.user
        return super().create(validated_data)
