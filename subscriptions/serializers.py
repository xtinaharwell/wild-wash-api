from rest_framework import serializers
from .models import Subscription

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'frequency', 'active', 'next_pickup_date']
        read_only_fields = ['id', 'active', 'next_pickup_date']