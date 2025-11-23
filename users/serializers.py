# users/serializers.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Location

User = get_user_model()

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'description', 'is_active', 'created_at']

class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 
            'first_name', 'last_name', 
            'service_location', 'location', 'is_location_admin'
        ]
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        location_name = validated_data.pop('location', '').strip()
        
        user = User.objects.create(
            is_staff=True,
            **validated_data
        )
        user.set_password(password)
        
        # If location text is provided but service_location isn't set, try to match it
        if location_name and not user.service_location:
            location_obj = Location.objects.filter(
                name__iexact=location_name,
                is_active=True
            ).first()
            
            if not location_obj:
                location_obj = Location.objects.filter(
                    name__icontains=location_name,
                    is_active=True
                ).first()
            
            if location_obj:
                user.service_location = location_obj
        
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    service_location_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "phone",
            "role",
            "location",
            "pickup_address",
            "is_staff",
            "service_location",
            "service_location_display",
        ]
        read_only_fields = ["id", "is_staff"]

    def get_service_location_display(self, obj):
        if obj.service_location:
            return obj.service_location.name
        return None


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    location = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = User
        fields = ["id", "username", "phone", "password", "first_name", "last_name", "location", "pickup_address"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        location_name = validated_data.get("location", "").strip()
        
        user = User(**validated_data)
        user.set_password(password)
        
        # If location is provided, try to match it with a Location object
        if location_name:
            # Try exact match first
            location_obj = Location.objects.filter(
                name__iexact=location_name,
                is_active=True
            ).first()
            
            # If no exact match, try case-insensitive contains
            if not location_obj:
                location_obj = Location.objects.filter(
                    name__icontains=location_name,
                    is_active=True
                ).first()
            
            # Set as service_location if found (useful for riders/staff later)
            if location_obj:
                user.service_location = location_obj
        
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
