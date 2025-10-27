# orders/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Order
from services.models import Service
from users.models import Location
from decimal import Decimal

User = get_user_model()

class OrderCreateSerializer(serializers.ModelSerializer):
    # accept service as PK -> DRF will convert to Service instance
    service = serializers.PrimaryKeyRelatedField(queryset=Service.objects.all())
    service_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_active=True),
        required=False
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "service",
            "service_location",
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
        # basic sanity defaults / checks
        if data.get("items") is None:
            data["items"] = 1
        if data.get("items", 0) < 1:
            raise serializers.ValidationError({"items": "Must be at least 1"})
        # allow weight_kg and price to be null for backend calculation
        return data

    def create(self, validated_data):
        """
        Attach order to:
         - request.user if authenticated, else
         - a single guest user (created if missing).
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        # If the incoming request is from an anonymous user, attach to guest user.
        if not (user and getattr(user, "is_authenticated", False)):
            guest_username = "guest_orders"           # choose a unique username
            guest_email = "guest@wildwash.local"
            guest_user, created = User.objects.get_or_create(
                username=guest_username,
                defaults={"email": guest_email, "is_active": False},
            )
            if created:
                # Make sure the account cannot be used to login
                guest_user.set_unusable_password()
                guest_user.save()

            user = guest_user

        # Create the order and set the human-friendly code afterwards
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
    service_location_name = serializers.CharField(source="service_location.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "created_at",
            "user",
            "service_name",
            "service_location_name",
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
