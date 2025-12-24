from rest_framework import serializers
from .models import GameWallet, GameTransaction


class GameTransactionSerializer(serializers.ModelSerializer):
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)

    class Meta:
        model = GameTransaction
        fields = [
            'id',
            'transaction_type',
            'transaction_type_display',
            'amount',
            'source',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GameWalletSerializer(serializers.ModelSerializer):
    transactions = GameTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = GameWallet
        fields = [
            'id',
            'balance',
            'total_deposits',
            'total_winnings',
            'total_losses',
            'transactions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id',
            'balance',
            'total_deposits',
            'total_winnings',
            'total_losses',
            'transactions',
            'created_at',
            'updated_at'
        ]


class GameWalletBalanceSerializer(serializers.ModelSerializer):
    """Lightweight serializer for just the balance."""
    class Meta:
        model = GameWallet
        fields = ['balance', 'total_deposits', 'total_winnings', 'total_losses', 'updated_at']
