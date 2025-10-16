
# -------------------------
# riders/urls.py
# -------------------------
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderLocationViewSet

router = DefaultRouter()
router.register(r'locations', RiderLocationViewSet, basename='rider-location')

urlpatterns = [
    path('', include(router.urls)),
]


