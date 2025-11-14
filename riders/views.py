# riders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RiderLocation, RiderProfile
from .serializers import RiderLocationSerializer, RiderProfileSerializer


class RiderLocationViewSet(viewsets.ModelViewSet):
    """Private viewset: riders push GPS updates. Auth required for create/update."""
    queryset = RiderLocation.objects.all()
    serializer_class = RiderLocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Riders see their own locations; staff can see all
        if self.request.user.is_staff:
            return super().get_queryset()
        return self.queryset.filter(rider=self.request.user)

    def perform_create(self, serializer):
        serializer.save(rider=self.request.user)


class PublicRiderLocationsView(APIView):
    """
    Public endpoint: GET /riders/ -> returns an array of latest RiderLocation entries,
    one per rider, newest first. No authentication required.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs):
        qs = RiderLocation.objects.all().order_by("-recorded_at", "-created_at")
        latest_by_rider = {}
        for loc in qs:
            rider_id = getattr(loc, "rider_id", None)
            rider_key = f"anon-{loc.id}" if rider_id is None else str(rider_id)
            if rider_key not in latest_by_rider:
                latest_by_rider[rider_key] = loc

        latest_list = list(latest_by_rider.values())
        serializer = RiderLocationSerializer(latest_list, many=True, context={"request": request})
        return Response(serializer.data)


class RiderProfileViewSet(viewsets.ModelViewSet):
    """
    Read (public) access to rider profiles. Creation/updates/deletes restricted to admin.
    Routes:
      - GET /riders/profiles/         -> list
      - GET /riders/profiles/<pk>/    -> retrieve
      - POST/PUT/PATCH/DELETE         -> admin only
    """
    queryset = RiderProfile.objects.select_related("user", "user__service_location").all().order_by("-created_at")
    serializer_class = RiderProfileSerializer

    def get_permissions(self):
        # Public read access, admin required for write
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]
