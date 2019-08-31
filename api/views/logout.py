from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils.auth import ExpiringJWTAuthentication
from api.utils.permission import LoginUserPermission


class LogoutView(APIView):
    authentication_classes = [ExpiringJWTAuthentication]
    permission_classes = [LoginUserPermission]

    def delete(self, request):
        # 由于认证模式采用JWT，后端又没有实现JWT过期机制，所有后端什么也不用做，前端删除token即可
        return Response({"code": 1000})
