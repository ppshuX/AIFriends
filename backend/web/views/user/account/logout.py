from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .cookies import delete_refresh_token_cookie


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        response = Response({
            'result': 'success',
        })
        delete_refresh_token_cookie(response)
        return response
