class IsStaffMember(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_staff and not user.is_superuser:
            return False

        if request.path == '/api/swagger/':
            token = request.query_params.get('token', None)
            if token == None or len(token) < 1:
                return False
            
            swagger_token = get_object_or_404(SwaggerToken, token = token, user_id= user.id)
            swagger_token.delete()
        
        return True