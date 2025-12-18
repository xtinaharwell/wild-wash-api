import requests
import base64
import logging
from datetime import datetime
from django.conf import settings
from rest_framework import views, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import BNPLUser, Payment
from .serializers import BNPLUserSerializer

from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

class BNPLViewSet(viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
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
    permission_classes = []  # Allow unauthenticated access
    authentication_classes = []

    def get(self, request):
        """Get user's phone number for checkout (if authenticated)."""
        if request.user.is_authenticated:
            phone = None
            if hasattr(request.user, 'phone_number'):
                phone = request.user.phone_number
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone_number'):
                phone = request.user.profile.phone_number
            
            if phone:
                return Response({'phone_number': phone})
        
        return Response({'phone_number': None})

    def post(self, request):
        """Initiate M-Pesa STK Push payment."""
        amount = request.data.get('amount')
        phone = request.data.get('phone')
        order_id = request.data.get('order_id')
        
        logger.info(f"STK Push request: amount={amount}, phone={phone}, order_id={order_id}")
        
        # If no phone provided and user is authenticated, try to get from user profile
        if not phone and request.user.is_authenticated:
            # Try to get phone from user profile
            if hasattr(request.user, 'phone_number'):
                phone = request.user.phone_number
                logger.info(f"Using phone from user profile: {phone}")
            elif hasattr(request.user, 'profile') and hasattr(request.user.profile, 'phone_number'):
                phone = request.user.profile.phone_number
                logger.info(f"Using phone from user.profile: {phone}")
        
        # Validate input
        if not all([amount, phone, order_id]):
            error_msg = f'Missing required fields: amount={bool(amount)}, phone={bool(phone)}, order_id={bool(order_id)}'
            logger.error(error_msg)
            return Response(
                {'detail': 'amount, phone, and order_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert amount to numeric
        try:
            amount = int(float(amount))
        except (ValueError, TypeError):
            return Response(
                {'detail': 'Invalid amount format'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store original order_id for reference, extract numeric part if available
        order_reference = order_id
        order_id_numeric = None
        
        # Try to extract numeric part from order_id (e.g., 'WW-00176' -> 176)
        if isinstance(order_id, str):
            import re
            numeric_match = re.search(r'\d+', order_id)
            if numeric_match:
                try:
                    order_id_numeric = int(numeric_match.group())
                except (ValueError, TypeError):
                    pass
        else:
            try:
                order_id_numeric = int(order_id)
            except (ValueError, TypeError):
                pass
        
        # Validate phone number format (Kenyan format)
        if not self._validate_phone(phone):
            return Response(
                {'detail': 'Invalid phone number. Use format: 254712345678 or 0712345678'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Clean up phone number - remove + prefix if present
        if phone.startswith('+'):
            phone = phone[1:]
            logger.info(f"Cleaned phone number from request: {phone}")
        
        # Log the phone being used
        logger.info(f"Using phone number for STK Push: {phone}")
        
        try:
            # Verify credentials are set
            if not settings.MPESA_CONSUMER_KEY or not settings.MPESA_CONSUMER_SECRET:
                error_msg = 'M-Pesa credentials not configured. Check your .env file for MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET'
                logger.error(error_msg)
                return Response(
                    {'detail': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Get access token from Daraja API
            access_token = self._get_access_token()
            
            # Initiate STK Push
            stk_response = self._initiate_stk_push(
                access_token, amount, phone, order_reference
            )
            
            # Create Payment record
            checkout_request_id = stk_response.get('CheckoutRequestID', '')
            payment = Payment.objects.create(
                user=request.user if request.user.is_authenticated else None,
                order_id=order_id_numeric,
                amount=amount,
                phone_number=phone,
                provider='mpesa',
                provider_reference=checkout_request_id,
                status='pending',
                raw_payload={'order_reference': order_reference}
            )
            payment.mark_initiated(provider_reference=checkout_request_id)
            
            logger.info(f"Payment initiated successfully: {checkout_request_id}")
            return Response({
                'status': 'success',
                'message': 'STK push sent to your phone',
                'checkout_request_id': stk_response.get('CheckoutRequestID'),
                'order_id': order_reference,
                'amount': amount
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error initiating payment: {str(e)}", exc_info=True)
            return Response(
                {'detail': f'Error initiating payment: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_phone(self, phone):
        """Validate Kenyan phone number."""
        # Remove + prefix if present
        clean_phone = phone.lstrip('+')
        
        # Accept formats: 254712345678 or 0712345678 or +254712345678
        if clean_phone.startswith('0') and len(clean_phone) == 10:
            return True
        if clean_phone.startswith('254') and len(clean_phone) == 12:
            return True
        return False

    def _get_access_token(self):
        """Get access token from Safaricom Daraja API."""
        url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        
        logger.info(f"Requesting access token from {url}")
        logger.debug(f"Using Consumer Key: {settings.MPESA_CONSUMER_KEY[:10]}...")
        
        try:
            response = requests.get(
                url,
                auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
                timeout=10
            )
            response.raise_for_status()
            token = response.json()['access_token']
            logger.info(f"Access token obtained successfully")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {str(e)}", exc_info=True)
            raise Exception(f'Failed to get access token: {str(e)}')

    def _initiate_stk_push(self, access_token, amount, phone, order_id):
        """Send STK Push request to Daraja API."""
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        # Generate timestamp and password
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self._encode_password(
            settings.MPESA_BUSINESS_SHORTCODE,
            settings.MPESA_PASSKEY,
            timestamp
        )
        
        # Format phone number to 254 format
        formatted_phone = phone.replace('0', '254', 1) if phone.startswith('0') else phone
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": settings.MPESA_BUSINESS_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": formatted_phone,
            "PartyB": settings.MPESA_BUSINESS_SHORTCODE,
            "PhoneNumber": formatted_phone,
            "CallBackURL": settings.MPESA_CALLBACK_URL,
            "AccountReference": order_id,
            "TransactionDesc": f"Wildwash Order {order_id}"
        }
        
        logger.info(f"Initiating STK Push to {formatted_phone} for amount {amount} KES")
        logger.debug(f"STK Push payload: {payload}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            logger.debug(f"STK Push response status: {response.status_code}")
            logger.debug(f"STK Push response body: {response.text}")
            response.raise_for_status()
            result = response.json()
            logger.info(f"STK Push successful. CheckoutRequestID: {result.get('CheckoutRequestID')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"STK push failed: {str(e)}", exc_info=True)
            raise Exception(f'STK push failed: {str(e)}')

    @staticmethod
    def _encode_password(shortcode, passkey, timestamp):
        """Encode password for M-Pesa authentication."""
        password_string = f"{shortcode}{passkey}{timestamp}"
        return base64.b64encode(password_string.encode()).decode()


class MpesaCallbackView(views.APIView):
    """Handle M-Pesa callback notifications."""
    permission_classes = []  # Allow unauthenticated access for M-Pesa callbacks
    authentication_classes = []
    
    def post(self, request):
        """Process M-Pesa callback."""
        try:
            data = request.data
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            
            # Update payment status
            if checkout_request_id:
                payment = Payment.objects.get(provider_reference=checkout_request_id)
                
                if result_code == 0:
                    payment.mark_success(payload=data)
                else:
                    payment.mark_failed(payload=data, note=f'Result Code: {result_code}')
            
            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {'detail': f'Callback processing error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )