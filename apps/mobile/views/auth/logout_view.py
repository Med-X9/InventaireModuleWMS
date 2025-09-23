from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class LogoutView(APIView):
    """API de déconnexion mobile"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        auth_service = AuthService()
        response_data = auth_service.logout()
        return Response(response_data, status=200)
