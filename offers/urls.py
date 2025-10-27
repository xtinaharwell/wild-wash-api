from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OfferViewSet, UserOfferViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'user-offers', UserOfferViewSet, basename='user-offers')
router.register(r'', OfferViewSet, basename='offer')

urlpatterns = [
    path('', include(router.urls)),
]