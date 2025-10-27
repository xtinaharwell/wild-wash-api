# urls for Wild Wash Django apps
# -------------------------
# users/urls.py
# -------------------------
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, LoginView, ChangePasswordView, 
    get_csrf, RegisterView, UserProfileView,
    LocationViewSet, StaffViewSet, StaffLoginView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('staff-login/', StaffLoginView.as_view(), name='staff-login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('csrf/', get_csrf, name='csrf'),
]


