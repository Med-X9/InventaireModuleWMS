from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from apps.mobile.services.auth_service import AuthService


class RefreshTokenView(APIView):
    """API de refresh token"""
    
    def post(self, request):
        auth_service = AuthService()
        
        refresh_token = request.data.get('refresh_token')
        
        response_data, error = auth_service.refresh_token(refresh_token)
        
        if error:
            return Response({
                'success': False,
                'error': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(response_data, status=status.HTTP_200_OK)
