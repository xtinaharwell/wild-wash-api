from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MpesaSTKPushView, BNPLViewSet

router = DefaultRouter(trailing_slash=True)
router.register(r'bnpl', BNPLViewSet, basename='bnpl')

urlpatterns = [
    path('mpesa/stk-push/', MpesaSTKPushView.as_view(), name='mpesa_stk_push'),
    path('', include(router.urls)),
]
