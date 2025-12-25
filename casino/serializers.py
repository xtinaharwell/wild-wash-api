from rest_framework import serializers
from .models import GameWallet, GameTransaction, SpinAlgorithmConfiguration


class SpinAlgorithmConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for spin algorithm configurations."""
    algorithm_info = serializers.SerializerMethodField()
    
    class Meta:
        model = SpinAlgorithmConfiguration
        fields = [
            'id',
            'name',
            'algorithm_key',
            'is_active',
            'start_time',
            'end_time',
            'days_of_week',
            'description',
            'algorithm_info',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_algorithm_info(self, obj):
        """Get algorithm segments and metadata."""
        return obj.get_algorithm_info()


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
