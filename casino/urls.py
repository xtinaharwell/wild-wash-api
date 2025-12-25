from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GameWalletViewSet, GameWalletSimpleView, SpinAlgorithmViewSet

router = DefaultRouter()
router.register(r'wallet', GameWalletViewSet, basename='game-wallet')
router.register(r'algorithms', SpinAlgorithmViewSet, basename='spin-algorithm')

urlpatterns = [
    path('wallet-balance/', GameWalletSimpleView.as_view(), name='game-wallet-simple'),
] + router.urls
