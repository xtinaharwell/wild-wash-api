# financing/serializers.py
from rest_framework import serializers
from .models import LoanApplication, LoanCollateral, LoanGuarantor, LoanRepayment
from orders.models import Order


class LoanCollateralSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanCollateral
        fields = ['id', 'collateral_type', 'description', 'estimated_value', 'created_at']
        read_only_fields = ['id', 'created_at']


class LoanGuarantorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanGuarantor
        fields = ['id', 'name', 'phone_number', 'email', 'relationship', 'created_at']
        read_only_fields = ['id', 'created_at']


class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = ['id', 'amount', 'status', 'payment_method', 'transaction_id', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']


class LoanApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for loan applications with nested relationships"""
    collateral_items = LoanCollateralSerializer(many=True, read_only=True)
    guarantors = LoanGuarantorSerializer(many=True, read_only=True)
    repayments = LoanRepaymentSerializer(many=True, read_only=True)
    order_code = serializers.CharField(source='order.code', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'user', 'user_username', 'loan_type', 'loan_amount', 'duration_days',
            'purpose', 'status', 'daily_interest_rate', 'total_interest', 'total_repayment',
            'order', 'order_code', 'order_value', 'created_at', 'updated_at', 'reviewed_at',
            'approved_at', 'funded_at', 'due_date', 'reviewer_notes', 'amount_repaid',
            'collateral_items', 'guarantors', 'repayments'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'reviewed_at', 'approved_at', 'funded_at',
            'total_interest', 'total_repayment'
        ]


class LoanApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    order_code = serializers.CharField(source='order.code', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    collateral_count = serializers.SerializerMethodField()
    guarantor_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'user', 'user_username', 'loan_type', 'loan_amount', 'status',
            'order_code', 'created_at', 'collateral_count', 'guarantor_count'
        ]
    
    def get_collateral_count(self, obj):
        return obj.collateral_items.count()
    
    def get_guarantor_count(self, obj):
        return obj.guarantors.count()


class CreateLoanApplicationSerializer(serializers.Serializer):
    """Serializer for creating loan applications"""
    loan_type = serializers.ChoiceField(choices=['order_collateral', 'collateral_only'])
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    duration_days = serializers.IntegerField(min_value=1, max_value=365)
    purpose = serializers.CharField(max_length=1000)
    order_id = serializers.IntegerField(required=False, allow_null=True)
    
    # Collateral items (for collateral_only type)
    collateral_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )
    
    # Guarantors
    guarantors = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )
    
    def validate(self, data):
        loan_type = data.get('loan_type')
        
        # For order_collateral, order_id is required
        if loan_type == 'order_collateral':
            if not data.get('order_id'):
                raise serializers.ValidationError("order_id is required for order_collateral loans")
        
        # At least one guarantor is required
        guarantors = data.get('guarantors', [])
        if not guarantors:
            raise serializers.ValidationError("At least one guarantor is required")
        
        return data
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Extract nested data
        collateral_items = validated_data.pop('collateral_items', [])
        guarantors = validated_data.pop('guarantors', [])
        order_id = validated_data.pop('order_id', None)
        
        # Handle order if provided
        order = None
        order_value = None
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                order_value = order.actual_price or order.price
            except Order.DoesNotExist:
                raise serializers.ValidationError("Order not found")
        
        # Create loan application
        loan_app = LoanApplication.objects.create(
            user=user,
            order=order,
            order_value=order_value,
            **validated_data
        )
        
        # Create collateral items
        for collateral in collateral_items:
            LoanCollateral.objects.create(
                loan_application=loan_app,
                collateral_type=collateral.get('type', 'other'),
                description=collateral.get('description', ''),
                estimated_value=collateral.get('estimated_value', 0)
            )
        
        # Create guarantors
        for guarantor in guarantors:
            LoanGuarantor.objects.create(
                loan_application=loan_app,
                name=guarantor.get('name', ''),
                phone_number=guarantor.get('phone_number', ''),
                email=guarantor.get('email', ''),
                relationship=guarantor.get('relationship', 'other')
            )
        
        return loan_app
