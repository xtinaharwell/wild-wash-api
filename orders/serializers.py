# orders/serializers.py
from rest_framework import serializers
from django.conf import settings
from .models import Order
from services.serializers import ServiceSerializer
from services.models import Service
from django.contrib.auth import get_user_model

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "phone"]


class OrderSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), write_only=True, source="service"
    )

    assigned_rider = SimpleUserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "service",
            "service_id",
            "pickup_address",
            "dropoff_address",
            "status",
            "urgency",
            "estimated_delivery",
            "created_at",
            "updated_at",
            "assigned_rider",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at", "assigned_rider"]


class OrderCreateSerializer(serializers.ModelSerializer):
    service_id = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(), write_only=True, source="service"
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "service_id",
            "pickup_address",
            "dropoff_address",
            "urgency",
            # any additional fields like 'notes' can be added
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create an order.")
        validated_data["user"] = user
        return super().create(validated_data)


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status", "estimated_delivery"]
