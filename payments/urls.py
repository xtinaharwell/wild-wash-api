from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MpesaSTKPushView, MpesaCallbackView, BNPLViewSet, TradeInView

router = DefaultRouter(trailing_slash=True)
router.register(r'bnpl', BNPLViewSet, basename='bnpl')

urlpatterns = [
    path('mpesa/stk-push/', MpesaSTKPushView.as_view(), name='mpesa_stk_push'),
    path('mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
    path('tradein/', TradeInView.as_view(), name='tradein'),
    path('', include(router.urls)),
]
