# orders/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Order
from services.models import Service
from users.models import Location
from decimal import Decimal

User = get_user_model()

class OrderCreateSerializer(serializers.ModelSerializer):
    # Accept multiple services via 'services' field
    services = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        many=True,
        write_only=True,
        required=False
    )
    # Keep 'service' for backward compatibility (single service)
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.all(),
        required=False
    )
    service_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_active=True),
        required=False
    )
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "service",
            "services",
            "service_location",
            "pickup_address",
            "dropoff_address",
            "urgency",
            "items",
            "package",
            "weight_kg",
            "price",
            "total_price",
            "estimated_delivery",
        ]
        read_only_fields = ["id", "total_price"]

    def validate(self, data):
        # basic sanity defaults / checks
        if data.get("items") is None:
            data["items"] = 1
        if data.get("items", 0) < 1:
            raise serializers.ValidationError({"items": "Must be at least 1"})
        
        # Ensure at least one service is provided
        services = data.get("services", [])
        service = data.get("service")
        if not services and not service:
            raise serializers.ValidationError(
                {"services": "At least one service must be provided"}
            )
        
        # allow weight_kg and price to be null for backend calculation
        return data

    def create(self, validated_data):
        """
        Attach order to:
         - request.user if authenticated, else
         - a single guest user (created if missing).
        Automatically set service_location from user's service_location.
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
        if 'user' not in validated_data:
            validated_data['user'] = user
        
        # Auto-set service_location from user's service_location if not provided
        if 'service_location' not in validated_data or not validated_data['service_location']:
            # Priority 1: User's service_location
            if user and user.service_location:
                validated_data['service_location'] = user.service_location
            # Priority 2: Try to infer from user's location field
            elif user and user.location:
                user_location = user.location.lower().strip()
                from users.models import Location
                inferred_location = Location.objects.filter(
                    name__icontains=user_location,
                    is_active=True
                ).first()
                if inferred_location:
                    validated_data['service_location'] = inferred_location
            # Priority 3: Try to infer from pickup_address
            if 'service_location' not in validated_data or not validated_data.get('service_location'):
                pickup_address = validated_data.get('pickup_address', '').lower()
                from users.models import Location
                locations = Location.objects.filter(is_active=True)
                for loc in locations:
                    if loc.name.lower() in pickup_address:
                        validated_data['service_location'] = loc
                        break
        
        # Extract services list for M2M
        services = validated_data.pop('services', [])
        
        # If no services in list but single service provided, use that
        if not services and 'service' in validated_data:
            services = [validated_data['service']]
        
        # Create the order
        order = Order.objects.create(**validated_data)
        
        # Add services to the order
        if services:
            order.services.set(services)
            # Set the primary service to the first one for backward compatibility
            if not order.service:
                order.service = services[0]
                order.save(update_fields=['service'])
        
        order.code = f"WW-{order.id:05d}"
        order.save(update_fields=["code"])
        return order

    def get_total_price(self, obj):
        """Calculate total price from all services"""
        total = sum(service.price for service in obj.services.all())
        return float(total) if total else 0


class OrderListSerializer(serializers.ModelSerializer):
    package = serializers.SerializerMethodField()
    price_display = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    status = serializers.CharField()
    service_name = serializers.CharField(source="service.name", read_only=True, allow_null=True)
    services_list = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    service_location = serializers.SerializerMethodField()
    rider = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    dropoff_location = serializers.SerializerMethodField()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache services and rider data to avoid multiple DB hits
        if isinstance(self.instance, list):
            self._services_cache = {}
            for order in self.instance:
                self._services_cache[order.id] = list(order.services.all().values('id', 'name', 'price'))
        elif self.instance:
            self._services_cache = {self.instance.id: list(self.instance.services.all().values('id', 'name', 'price'))}

    def get_user(self, obj):
        if not obj.user:
            return None
        return {
            'username': obj.user.username,
            'location': obj.user.location,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }

    def get_service_location(self, obj):
        if not obj.service_location:
            return None
        return {
            'id': obj.service_location.id,
            'name': obj.service_location.name,
        }

    def get_rider(self, obj):
        if not obj.rider:
            return None
        return {
            'username': obj.rider.username,
            'first_name': obj.rider.first_name,
            'last_name': obj.rider.last_name,
            'service_location': {
                'name': obj.rider.service_location.name if obj.rider.service_location else None
            }
        }

    def get_services_list(self, obj):
        """Return list of services with their details"""
        services = obj.services.all().values('id', 'name', 'price')
        return list(services)

    def get_total_price(self, obj):
        """Calculate total price from all services"""
        total = sum(service.price for service in obj.services.all())
        return float(total) if total else None

    def get_package(self, obj):
        return getattr(obj.service, "name", f"Package {obj.package}") if obj.service else f"Package {obj.package}"

    def get_price_display(self, obj):
        # Use total price from services if available
        total = sum(service.price for service in obj.services.all())
        if total:
            try:
                p = Decimal(str(total))
                if p == p.to_integral():
                    return f"KSh {int(p):,}"
                return f"KSh {p:,}"
            except Exception:
                return str(total)
        elif obj.price is not None:
            try:
                p = Decimal(obj.price)
                if p == p.to_integral():
                    return f"KSh {int(p):,}"
                return f"KSh {p:,}"
            except Exception:
                return str(obj.price)
        return ""

    def get_pickup_location(self, obj):
        """Return pickup location coordinates if available from service_location"""
        if obj.service_location and hasattr(obj.service_location, 'latitude') and hasattr(obj.service_location, 'longitude'):
            return {
                'lat': float(obj.service_location.latitude) if obj.service_location.latitude else None,
                'lng': float(obj.service_location.longitude) if obj.service_location.longitude else None
            }
        return None

    def get_dropoff_location(self, obj):
        """Return dropoff location - could be user's location or another location"""
        if obj.user and hasattr(obj.user, 'latitude') and hasattr(obj.user, 'longitude'):
            return {
                'lat': float(obj.user.latitude) if obj.user.latitude else None,
                'lng': float(obj.user.longitude) if obj.user.longitude else None
            }
        return None

    class Meta:
        model = Order
        fields = [
            "id",
            "code",
            "created_at",
            "user",
            "service_name",
            "services_list",
            "service_location",
            "pickup_address",
            "dropoff_address",
            "pickup_location",
            "dropoff_location",
            "urgency",
            "items",
            "weight_kg",
            "quantity",
            "description",
            "package",
            "price",
            "total_price",
            "price_display",
            "status",
            "estimated_delivery",
            "delivered_at",
            "rider"
        ]
