# orders/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from .models import Order
from .serializers import OrderCreateSerializer, OrderListSerializer
from django_filters.rest_framework import DjangoFilterBackend

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 50

class OrderViewSet(viewsets.ModelViewSet):
    """
    - GET /api/orders/         -> list (paginated; only current user's orders)
    - POST /api/orders/        -> create (associates request.user)
    - GET /api/orders/{pk}/    -> retrieve
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['code', 'service__name', 'pickup_address', 'dropoff_address']
    filterset_fields = ['status']

    def get_queryset(self):
        # only return orders belonging to current user
        user = self.request.user
        return Order.objects.filter(user=user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderCreateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        # use serializer create() which attaches request.user
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        read_serializer = OrderListSerializer(order, context={'request': request})
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
