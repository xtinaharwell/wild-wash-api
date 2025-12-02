# financing/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from django.db.models import Q
from .models import LoanApplication, LoanCollateral, LoanGuarantor, LoanRepayment
from .serializers import (
    LoanApplicationDetailSerializer,
    LoanApplicationListSerializer,
    CreateLoanApplicationSerializer,
    LoanCollateralSerializer,
    LoanGuarantorSerializer,
    LoanRepaymentSerializer
)


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing loan applications.
    
    - Users can view their own applications
    - Users can create new loan applications
    - Admins can review and approve/reject applications
    """
    queryset = LoanApplication.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'id']
    ordering_fields = ['created_at', 'loan_amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter based on user role"""
        user = self.request.user
        
        # Admins see all applications
        if user.is_staff or user.is_superuser:
            return LoanApplication.objects.all()
        
        # Regular users see only their own
        return LoanApplication.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == 'create':
            return CreateLoanApplicationSerializer
        elif self.action == 'pending_review':
            return LoanApplicationListSerializer
        # Return detailed serializer for list and retrieve to get all nested data
        return LoanApplicationDetailSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new loan application"""
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        loan_app = serializer.save()
        
        # Return detailed serializer
        return Response(
            LoanApplicationDetailSerializer(loan_app).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def pending_review(self, request):
        """Get all loan applications pending review"""
        pending_apps = self.get_queryset().filter(status='pending')
        serializer = self.get_serializer(pending_apps, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a loan application"""
        loan_app = self.get_object()
        
        if loan_app.status != 'pending':
            return Response(
                {'error': f'Cannot approve application with status {loan_app.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan_app.status = 'approved'
        loan_app.approved_at = timezone.now()
        loan_app.reviewed_at = timezone.now()
        loan_app.reviewed_by = request.user
        loan_app.reviewer_notes = request.data.get('notes', '')
        loan_app.save()
        
        return Response(
            LoanApplicationDetailSerializer(loan_app).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        """Reject a loan application"""
        loan_app = self.get_object()
        
        if loan_app.status != 'pending':
            return Response(
                {'error': f'Cannot reject application with status {loan_app.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan_app.status = 'rejected'
        loan_app.reviewed_at = timezone.now()
        loan_app.reviewed_by = request.user
        loan_app.reviewer_notes = request.data.get('notes', '')
        loan_app.save()
        
        return Response(
            LoanApplicationDetailSerializer(loan_app).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def fund(self, request, pk=None):
        """Mark a loan application as funded"""
        loan_app = self.get_object()
        
        if loan_app.status != 'approved':
            return Response(
                {'error': 'Only approved applications can be funded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        loan_app.status = 'active'
        loan_app.funded_at = timezone.now()
        loan_app.due_date = timezone.now() + timezone.timedelta(days=loan_app.duration_days)
        loan_app.save()
        
        return Response(
            LoanApplicationDetailSerializer(loan_app).data,
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def repay(self, request, pk=None):
        """Record a repayment for a loan"""
        loan_app = self.get_object()
        
        # Check if user owns this loan
        if loan_app.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to repay this loan'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if loan_app.status not in ['active', 'approved']:
            return Response(
                {'error': f'Cannot repay loan with status {loan_app.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        amount = request.data.get('amount')
        payment_method = request.data.get('payment_method', 'mpesa')
        
        if not amount:
            return Response(
                {'error': 'amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return Response(
                {'error': 'amount must be a valid number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create repayment record
        repayment = LoanRepayment.objects.create(
            loan_application=loan_app,
            amount=amount,
            payment_method=payment_method,
            status='completed'  # In production, integrate with payment gateway
        )
        
        # Update loan
        loan_app.amount_repaid += amount
        
        # Check if fully repaid
        if loan_app.amount_repaid >= loan_app.total_repayment:
            loan_app.status = 'repaid'
        
        loan_app.save()
        
        return Response(
            LoanRepaymentSerializer(repayment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def summary(self, request, pk=None):
        """Get a summary of loan application with key metrics"""
        loan_app = self.get_object()
        
        # Check permissions
        if loan_app.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You do not have permission to view this loan'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        remaining = max(0, (loan_app.total_repayment or 0) - loan_app.amount_repaid)
        
        return Response({
            'id': str(loan_app.id),
            'status': loan_app.status,
            'loan_amount': str(loan_app.loan_amount),
            'total_repayment': str(loan_app.total_repayment or 0),
            'amount_repaid': str(loan_app.amount_repaid),
            'remaining_balance': str(remaining),
            'due_date': loan_app.due_date,
            'days_remaining': (loan_app.due_date - timezone.now()).days if loan_app.due_date else None,
        })


# Standalone function-based view for creating loan requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from orders.models import Order
from decimal import Decimal


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_loan_request(request):
    """
    Create a new loan request from the frontend.
    
    Accepts:
    - loan_type: 'order_collateral' or 'collateral_only'
    - loan_amount: decimal
    - duration_days: integer
    - purpose: string
    - order_id: integer (for order_collateral)
    - collateral: dict with type and items
    - guarantors: list of dicts with name, phone_number, email, relationship
    """
    try:
        data = request.data
        user = request.user
        
        # Validate required fields
        loan_type = data.get('loan_type')
        loan_amount = data.get('loan_amount')
        duration_days = data.get('duration_days')
        purpose = data.get('purpose')
        collateral_data = data.get('collateral', {})
        guarantors_data = data.get('guarantors', [])
        
        # Validation
        if not loan_type or loan_type not in ['order_collateral', 'collateral_only']:
            return Response(
                {'error': 'loan_type must be "order_collateral" or "collateral_only"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not loan_amount:
            return Response(
                {'error': 'loan_amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not duration_days:
            return Response(
                {'error': 'duration_days is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not purpose:
            return Response(
                {'error': 'purpose is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not guarantors_data or len(guarantors_data) == 0:
            return Response(
                {'error': 'At least one guarantor is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle order collateral
        order = None
        order_value = None
        
        if loan_type == 'order_collateral':
            order_id = data.get('order_id')
            if not order_id:
                return Response(
                    {'error': 'order_id is required for order_collateral loans'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                order = Order.objects.get(id=order_id)
                order_value = Decimal(str(order.actual_price or order.price or 0))
            except Order.DoesNotExist:
                return Response(
                    {'error': f'Order with id {order_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Create loan application
        loan_app = LoanApplication.objects.create(
            user=user,
            loan_type=loan_type,
            loan_amount=Decimal(str(loan_amount)),
            duration_days=int(duration_days),
            purpose=purpose,
            order=order,
            order_value=order_value,
            status='pending'
        )
        
        # Calculate interest
        loan_app.calculate_total_interest()
        loan_app.save()
        
        # Add collateral items for collateral_only type
        if loan_type == 'collateral_only':
            collateral_items = collateral_data.get('items', [])
            for item in collateral_items:
                LoanCollateral.objects.create(
                    loan_application=loan_app,
                    collateral_type=item.get('type', 'other'),
                    description=item.get('description', ''),
                    estimated_value=Decimal(str(item.get('estimated_value', 0)))
                )
        
        # Add guarantors
        for guarantor in guarantors_data:
            LoanGuarantor.objects.create(
                loan_application=loan_app,
                name=guarantor.get('name', ''),
                phone_number=guarantor.get('phone_number', ''),
                email=guarantor.get('email', ''),
                relationship=guarantor.get('relationship', 'friend')
            )
        
        # Return created loan application
        serializer = LoanApplicationDetailSerializer(loan_app)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
