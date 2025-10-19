# riders/views.py
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RiderLocation
from .serializers import RiderLocationSerializer

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
        # load recent locations ordered by recorded_at desc
        qs = RiderLocation.objects.all().order_by("-recorded_at", "-created_at")

        # choose latest per rider in Python (works on any DB)
        latest_by_rider = {}
        for loc in qs:
            rider_id = getattr(loc, "rider_id", None)
            if rider_id is None:
                # include anonymous / unknown rider rows if any
                # use a unique key for these
                rider_key = f"anon-{loc.id}"
            else:
                rider_key = str(rider_id)
            if rider_key not in latest_by_rider:
                latest_by_rider[rider_key] = loc

        latest_list = list(latest_by_rider.values())

        serializer = RiderLocationSerializer(latest_list, many=True, context={"request": request})
        return Response(serializer.data)
