from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import BNPLUser
from .serializers import BNPLUserSerializer

class BNPLViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BNPLUserSerializer

    def get_queryset(self):
        return BNPLUser.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get the user's BNPL status."""
        try:
            bnpl_user = BNPLUser.objects.get(user=request.user)
            serializer = self.get_serializer(bnpl_user)
            return Response(serializer.data)
        except BNPLUser.DoesNotExist:
            return Response({
                'is_enrolled': False,
                'credit_limit': 0,
                'current_balance': 0
            })

    @action(detail=False, methods=['post'])
    def opt_in(self, request):
        """Opt in to BNPL service."""
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response(
                {'detail': 'Phone number is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is already enrolled
        bnpl_user, created = BNPLUser.objects.get_or_create(
            user=request.user,
            defaults={
                'phone_number': phone_number,
                'is_active': True
            }
        )

        if not created:
            if not bnpl_user.is_active:
                bnpl_user.is_active = True
                bnpl_user.phone_number = phone_number
                bnpl_user.save()
                serializer = self.get_serializer(bnpl_user)
                return Response(serializer.data)
            return Response(
                {'detail': 'You are already enrolled in BNPL'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(bnpl_user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def opt_out(self, request):
        """Opt out of BNPL service."""
        try:
            bnpl_user = BNPLUser.objects.get(user=request.user)
            if bnpl_user.current_balance > 0:
                return Response(
                    {'detail': 'Cannot opt out while you have an outstanding balance'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            bnpl_user.is_active = False
            bnpl_user.save()
            return Response({'detail': 'Successfully opted out of BNPL'})
        except BNPLUser.DoesNotExist:
            return Response(
                {'detail': 'You are not enrolled in BNPL'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class MpesaSTKPushView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Expect: amount, phone, order_id
        # Implement call to Daraja API here (server-side)
        # This is a placeholder that returns a simulated response
        amount = request.data.get('amount')
        phone = request.data.get('phone')
        order_id = request.data.get('order_id')
        # TODO: call Daraja, create Payment record, return payment status
        return Response({'status': 'started', 'order_id': order_id, 'amount': amount, 'phone': phone})