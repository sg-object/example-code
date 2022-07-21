class IsStaffMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if user.is_staff or user.is_superuser:
            return True
        
        return False
