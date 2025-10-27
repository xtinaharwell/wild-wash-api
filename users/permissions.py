from rest_framework import permissions

class LocationBasedPermission(permissions.BasePermission):
    """
    Permission class that ensures users can only access data from their assigned location.
    """
    
    def has_permission(self, request, view):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # Staff must have a service location assigned
        if request.user.is_staff and not request.user.service_location:
            return False
            
        return True

    def has_object_permission(self, request, view, obj):
        # Superusers have full access
        if request.user.is_superuser:
            return True
            
        # Non-staff users can only access their own data
        if not request.user.is_staff:
            return obj.user == request.user
            
        # Staff can only access data from their location
        if hasattr(obj, 'location'):
            return obj.location == request.user.service_location
            
        # For orders and other location-based models
        if hasattr(obj, 'service_location'):
            return obj.service_location == request.user.service_location
            
        # For user objects
        if hasattr(obj, 'service_location') and request.user.is_location_admin:
            return obj.service_location == request.user.service_location
            
        return False