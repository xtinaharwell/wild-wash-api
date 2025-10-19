# riders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RiderLocationViewSet, PublicRiderLocationsView, RiderProfileViewSet

router = DefaultRouter()
# authenticated CRUD for locations (used by rider device / admin)
router.register(r'locations', RiderLocationViewSet, basename='rider-location')
# profiles (public read, admin write)
router.register(r'profiles', RiderProfileViewSet, basename='rider-profile')

urlpatterns = [
    # public latest locations: GET /riders/
    path("", PublicRiderLocationsView.as_view(), name="rider-latest"),
    # include viewset routes at /riders/
    path("", include(router.urls)),
]
