from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class LoginView(APIView):
    """API de connexion mobile"""
    
    def post(self, request):
        auth_service = AuthService()
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        response_data, error = auth_service.login(username, password)
        
        if error:
            return Response({
                'success': False,
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_200_OK)
