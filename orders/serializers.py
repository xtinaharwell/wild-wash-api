# orders/serializers.py
from rest_framework import serializers
from .models import Order
from services.models import Service
from decimal import Decimal
from django.utils import timezone

class OrderCreateSerializer(serializers.ModelSerializer):
    # accept service as ID (FK), and return service name in read serializer
    class Meta:
        model = Order
        fields = [
            'id',
            'service',           # expects service id
            'pickup_address',
            'dropoff_address',
            'urgency',
            'items',
            'package',
            'weight_kg',
            'price',
            'estimated_delivery',
        ]
        read_only_fields = ['id']

    def validate_service(self, value):
        # ensure service exists (DRF will check FK, but you can add checks)
        if not Service.objects.filter(pk=value.id if hasattr(value, 'id') else value).exists():
            raise serializers.ValidationError("Invalid service")
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        # Create order but leave code empty for now (we'll set it after saving)
        order = Order.objects.create(user=user, **validated_data)
        # generate human-friendly code like WW-00001
        order.code = f"WW-{order.id:05d}"
        order.save(update_fields=['code'])
        return order


class OrderListSerializer(serializers.ModelSerializer):
    package = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    status = serializers.CharField(source='get_status_display')  # human-readable label
    service_name = serializers.CharField(source='service.name', read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)  # optional

    class Meta:
        model = Order
        fields = [
            'id',
            'code',
            'created_at',
            'user',               # ✅ add this if you want user data
            'service_name',       # ✅ service readable name
            'pickup_address',     # ✅ missing before
            'dropoff_address',    # ✅ missing before
            'urgency',            # ✅ if you want it displayed
            'items',
            'weight_kg',
            'package',
            'price',
            'price_display',
            'status',
            'estimated_delivery',
            'delivered_at',
        ]

    def get_package(self, obj):
        return getattr(obj.service, 'name', f"Package {obj.package}")

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
