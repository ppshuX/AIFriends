from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from web.utils.llm_env import api_key_configured, save_llm_config

_LOOPBACK = {"127.0.0.1", "::1", "::ffff:127.0.0.1"}


def client_is_loopback(request):
    # 不信任 X-Forwarded-For，避免远程请求伪装成本机改写密钥。
    return request.META.get("REMOTE_ADDR", "") in _LOOPBACK


class LlmConfigView(APIView):
    """报告 API Key 是否已配置，并允许本机登录用户写入数据目录 .env。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "result": "success",
            "api_key_configured": api_key_configured(),
        })

    def post(self, request):
        if not client_is_loopback(request):
            return Response({
                "result": "只能在本机修改 API Key",
                "api_key_configured": api_key_configured(),
            }, status=403)
        api_key = request.data.get("api_key", "")
        api_base = request.data.get("api_base", None)
        try:
            save_llm_config(api_key, api_base)
        except ValueError as exc:
            return Response({
                "result": str(exc),
                "api_key_configured": api_key_configured(),
            }, status=400)
        except OSError:
            return Response({
                "result": "无法写入配置文件，请检查数据目录是否可写",
                "api_key_configured": api_key_configured(),
            }, status=400)
        return Response({
            "result": "success",
            "api_key_configured": True,
        })
