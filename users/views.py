from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

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
    queryset = User.objects.all()
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
        # simple token login example - assumes username/password posted
        from django.contrib.auth import authenticate
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data})


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
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if not user or not user.is_superuser:
            return Response(
                {'detail': 'Invalid credentials or not an admin'}, 
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
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if not user or not user.is_staff:
            return Response(
                {'detail': 'Invalid credentials or not a staff member'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.service_location:
            return Response(
                {'detail': 'No location assigned'}, 
                status=status.HTTP_403_FORBIDDEN
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