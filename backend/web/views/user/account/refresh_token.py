from rest_framework.views import APIView
from rest_framework.response import Response

import settings


class RefreshToken(APIView):
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get['refresh_token']
            if not refresh_token:
                return Response({
                    'result': 'refresh token 不存在'
                }, status=401)
            refresh = RefreshToken(refresh_token)
            if settings.SIMPLE_JWT('ROTATE_FRESH_TOKEN'):
                refresh.set_jti()
                response = Response({
                    'result': 'success',
                    'access': str(refresh.access_token),
                })
                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    samesite='Lax',
                    secure=True,
                    max_age=86400 * 7,
                )
                return response
            return Response({
                'result': 'success',
            })

        except:
            return Response({
                'result': 'refresh token 过期了',
            }, status=401)