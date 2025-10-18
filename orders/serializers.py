# orders/serializers.py
from rest_framework import serializers
from .models import Order
from services.models import Service
from decimal import Decimal

class OrderCreateSerializer(serializers.ModelSerializer):
    # explicitly accept service as PK (integer) and let DRF convert it to a Service instance
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())

    class Meta:
        model = Order
        fields = [
            "id",
            "service",           # expects service id (PK)
            "pickup_address",
            "dropoff_address",
            "urgency",
            "items",
            "package",
            "weight_kg",
            "price",
            "estimated_delivery",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        """
        Example validations:
        - pickup_address required if pickup contact provided
        - ensure items is positive
        """
        if data.get("items") is None:
            data["items"] = 1
        if data.get("items", 0) < 1:
            raise serializers.ValidationError({"items": "Must be at least 1"})
        # allow null weight and price (backend can compute)
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        order = Order.objects.create(user=user, **validated_data)
        order.code = f"WW-{order.id:05d}"
        order.save(update_fields=["code"])
        return order


class OrderListSerializer(serializers.ModelSerializer):
    package = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    status = serializers.CharField(source="get_status_display")
    service_name = serializers.CharField(source="service.name", read_only=True)
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "created_at",
            "user",
            "service_name",
            "pickup_address",
            "dropoff_address",
            "urgency",
            "items",
            "weight_kg",
            "package",
            "price",
            "price_display",
            "status",
            "estimated_delivery",
            "delivered_at",
        ]

    def get_package(self, obj):
        return getattr(obj.service, "name", f"Package {obj.package}")

    def get_price_display(self, obj):
        if obj.price is None:
            return ""
        try:
            p = Decimal(obj.price)
            if p == p.to_integral():
                return f"KSh {int(p):,}"
            return f"KSh {p:,}"
        except Exception:
            return str(obj.price)
