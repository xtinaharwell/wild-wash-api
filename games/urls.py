from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GameWalletViewSet, GameWalletSimpleView

router = DefaultRouter()
router.register(r'wallet', GameWalletViewSet, basename='game-wallet')

urlpatterns = [
    path('wallet-balance/', GameWalletSimpleView.as_view(), name='game-wallet-simple'),
] + router.urls
