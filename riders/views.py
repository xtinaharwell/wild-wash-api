from rest_framework import viewsets, permissions
from .models import RiderLocation
from .serializers import RiderLocationSerializer

class RiderLocationViewSet(viewsets.ModelViewSet):
    """Riders push their current GPS location (used for live tracking)."""
    queryset = RiderLocation.objects.all()
    serializer_class = RiderLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Riders see their own locations; admin can see all
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(rider=self.request.user)

    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)