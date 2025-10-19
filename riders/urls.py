# riders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderLocationViewSet, PublicRiderLocationsView

router = DefaultRouter()
router.register(r'locations', RiderLocationViewSet, basename='rider-location')

urlpatterns = [
    # Public listing (latest per rider) at /riders/
    path("", PublicRiderLocationsView.as_view(), name="rider-latest"),
    # Authenticated CRUD for locations (devices/admin) at /riders/locations/
    path("locations/", include(router.urls)),
]
