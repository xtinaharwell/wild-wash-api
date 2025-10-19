# urls for Wild Wash Django apps
# Save each section to the matching file path in your project.

# -------------------------
# users/urls.py
# -------------------------
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoginView, ChangePasswordView, get_csrf

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('csrf/', get_csrf, name='csrf'),
]


