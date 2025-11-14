# notifications/serializers.py
from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "user", "order", "message", "notification_type", "created_at", "is_read"]
        read_only_fields = ["id", "created_at", "user"]
