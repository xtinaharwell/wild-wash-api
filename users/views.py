from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .serializers import (
    UserSerializer, UserCreateSerializer, ChangePasswordSerializer,
    LocationSerializer, StaffCreateSerializer
)
from .models import Location
from .permissions import LocationBasedPermission

User = get_user_model()

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def get_csrf(request):
    # ensure_csrf_cookie will set the csrftoken cookie in the response headers
    return JsonResponse({"detail": "csrf cookie set"})


class UserProfileView(APIView):
    """
    View for handling the current user's profile
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        """Get the current user's profile"""
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update the current user's profile"""
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    """
    Admin-friendly user viewset for managing all users.
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        # Allow anyone to create (signup) via create()
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """
        Login with phone number, email, or username and password
        Supports multiple phone formats: 0718693484, +254718693484, 254718693484
        """
        from services.sms_service import format_phone_number
        
        # Try to get user identifier (could be phone, email, or username)
        phone = request.data.get('phoneNumber') or request.data.get('phone')
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        
        # Try phone number authentication first
        if phone:
            try:
                # Format the phone number to match stored format
                formatted_phone = format_phone_number(phone)
                # Try exact match first
                user = User.objects.get(phone=formatted_phone)
            except User.DoesNotExist:
                # Try without formatting in case it's already formatted
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    pass
        
        # Try email authentication if phone didn't work
        if not user and email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                pass
        
        # Try username authentication if phone and email didn't work
        if not user and username:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                pass
        
        # If user not found
        if not user:
            return Response(
                {'detail': 'Invalid credentials. Please check your phone/email/username and try again.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        if not user.check_password(password):
            return Response({'detail': 'Invalid password.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Check if user is active
        if not user.is_active:
            return Response({'detail': 'This account is inactive.'}, status=status.HTTP_401_UNAUTHORIZED)
        
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key, 
            'user': UserSerializer(user).data
        })


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password set'})


@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing service locations.
    Only superusers can create/update/delete locations.
    Staff can view their assigned location.
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [LocationBasedPermission]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class AdminLoginView(APIView):
    """
    Special login view for admin users that verifies superuser status
    Supports phone, email, or username with multiple phone formats
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from services.sms_service import format_phone_number
        
        phone = request.data.get('phoneNumber') or request.data.get('phone')
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        
        # Try phone number authentication
        if phone:
            try:
                formatted_phone = format_phone_number(phone)
                user = User.objects.get(phone=formatted_phone)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    pass
        
        # Try email if phone didn't work
        if not user and email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                pass
        
        # Try username if phone and email didn't work
        if not user and username:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response(
                {'detail': 'Invalid credentials or not an admin'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_superuser:
            return Response(
                {'detail': 'You do not have admin privileges.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {'detail': 'Invalid password.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'detail': 'This account is inactive.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class StaffLoginView(APIView):
    """
    Special login view for staff members that checks their location assignment
    Supports phone, email, or username with multiple phone formats
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from services.sms_service import format_phone_number
        
        phone = request.data.get('phoneNumber') or request.data.get('phone')
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not password:
            return Response({'detail': 'Password is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = None
        
        # Try phone number authentication
        if phone:
            try:
                formatted_phone = format_phone_number(phone)
                user = User.objects.get(phone=formatted_phone)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    pass
        
        # Try email if phone didn't work
        if not user and email:
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                pass
        
        # Try username if phone and email didn't work
        if not user and username:
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response(
                {'detail': 'Invalid credentials or not a staff member'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_staff:
            return Response(
                {'detail': 'You do not have staff privileges.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.check_password(password):
            return Response(
                {'detail': 'Invalid password.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'detail': 'This account is inactive.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class StaffViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing staff members.
    Only superusers can access this ViewSet.
    """
    queryset = User.objects.filter(is_staff=True)
    serializer_class = StaffCreateSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.filter(is_staff=True).exclude(is_superuser=True)

    def perform_create(self, serializer):
        user = serializer.save(is_staff=True)
        return user