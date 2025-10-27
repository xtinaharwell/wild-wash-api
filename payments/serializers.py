# payments/serializers.py
from rest_framework import serializers
from .models import Payment, MpesaSTKRequest, BNPLUser
from django.contrib.auth import get_user_model

User = get_user_model()


class PaymentSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    # If you use order FK, you can replace order_id with a nested serializer or PrimaryKeyRelatedField

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "order_id",
            "provider",
            "provider_reference",
            "amount",
            "currency",
            "phone_number",
            "status",
            "initiated_at",
            "completed_at",
            "raw_payload",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "initiated_at", "completed_at", "created_at", "updated_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["order_id", "amount", "currency", "phone_number", "provider"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        payment = Payment.objects.create(user=user, **validated_data)
        return payment


class BNPLUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = BNPLUser
        fields = [
            'id',
            'user',
            'is_active',
            'phone_number',
            'credit_limit',
            'current_balance',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'credit_limit', 'current_balance', 'created_at', 'updated_at']


class MpesaSTKRequestSerializer(serializers.ModelSerializer):
    payment = PaymentSerializer(read_only=True)
    payment_id = serializers.PrimaryKeyRelatedField(
        queryset=Payment.objects.all(), source="payment", write_only=True
    )

    class Meta:
        model = MpesaSTKRequest
        fields = [
            "id",
            "payment",
            "payment_id",
            "checkout_request_id",
            "merchant_request_id",
            "result_code",
            "result_desc",
            "callback_payload",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "payment", "created_at", "updated_at"]
