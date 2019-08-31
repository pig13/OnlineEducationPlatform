import datetime

import jwt
from django.conf import settings
from django.contrib import auth
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import UserInfo
from api.utils.captcha_verify import verify
from api.utils.exceptions import CommonException
from api.utils.response import BaseResponse


class LoginView(APIView):

    def generate_JWT(self, payload):
        if not isinstance(payload, dict):
            raise CommonException(2001, 'payload 必须是字典类型')
        payload['exp'] = (timezone.now() + datetime.timedelta(seconds=settings.JWT_EXP)).timestamp()
        return jwt.encode(payload=payload, key=settings.JWT_KEY, algorithm=settings.JWT_ALGORITHM)

    def post(self, request):
        response = BaseResponse()
        receive = request.data  # 原始数据
        if request.method == 'POST':
            is_valid = verify(receive)
            if is_valid:
                username = receive.get("username")
                password = receive.get("password")
                user = auth.authenticate(username=username, password=password)
                if user is not None:

                    user_info = UserInfo.objects.filter(pk=user.pk).values('username', 'head_img', 'uid').first()
                    user = {
                        'uid': user_info['uid'],
                    }
                    token = self.generate_JWT(user)  # type:bytes

                    response.msg = "验证成功!"
                    response.data = {
                        'userinfo': {
                            'username': user_info['username'],
                            'head_img': user_info['username'],
                        },
                        'token': token
                    }
                else:
                    try:
                        UserInfo.objects.get(username=username)
                        response.msg = "密码错误!"
                        response.code = 1002
                    except UserInfo.DoesNotExist:
                        response.msg = "用户不存在!"
                        response.code = 1003
            else:

                response.code = 1001
                response.msg = "请完成滑动验证!"

            return Response(response.dict)
