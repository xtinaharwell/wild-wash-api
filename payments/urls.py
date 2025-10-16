

# -------------------------
# payments/urls.py
# -------------------------
from django.urls import path
from .views import MpesaSTKPushView

urlpatterns = [
    path('mpesa/stk/', MpesaSTKPushView.as_view(), name='mpesa-stk-push'),
]

