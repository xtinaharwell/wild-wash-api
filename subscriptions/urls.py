from django.urls import path
from .views import SubscriptionView

urlpatterns = [
    path('me/subscription/', SubscriptionView.as_view(), name='user-subscription'),
]