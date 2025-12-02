# financing/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoanApplicationViewSet, create_loan_request

router = DefaultRouter()
router.register(r'loans', LoanApplicationViewSet, basename='loan-application')

urlpatterns = [
    path('request/', create_loan_request, name='create-loan-request'),
    path('', include(router.urls)),
]
