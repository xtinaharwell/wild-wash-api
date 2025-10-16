from rest_framework import views, permissions, status
from rest_framework.response import Response

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