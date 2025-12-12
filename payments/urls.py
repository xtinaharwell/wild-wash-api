from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MpesaSTKPushView, MpesaCallbackView, BNPLViewSet

router = DefaultRouter(trailing_slash=True)
router.register(r'bnpl', BNPLViewSet, basename='bnpl')

urlpatterns = [
    path('mpesa/stk-push/', MpesaSTKPushView.as_view(), name='mpesa_stk_push'),
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('', include(router.urls)),
]
