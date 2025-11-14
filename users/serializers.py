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
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 
            'first_name', 'last_name', 
            'service_location', 'is_location_admin'
        ]
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(
            is_staff=True,
            **validated_data
        )
        user.set_password(password)
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

    class Meta:
        model = User
        fields = ["id", "username", "phone", "password", "first_name", "last_name", "location", "pickup_address"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
