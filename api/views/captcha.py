import json

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from api.utils.geetest import GeeTestLib


class CaptchaView(APIView):
    def get(self, request):
        captcha_config = settings.THIRD_PART_CONFIG['GEE_TEST']
        gt = GeeTestLib(captcha_config["gee_test_access_id"], captcha_config["gee_test_access_key"])
        gt.pre_process()
        # 设置 geetest session, 用于是否启用滑动验证码向 geetest 发起远程验证, 如果取不到的话只是对本地轨迹进行校验
        # self.request.session[gt.GT_STATUS_SESSION_KEY] = status
        # request.session["user_id"] = user_id
        response_str = gt.get_response_str()
        response_str = json.loads(response_str)

        return Response({"error_no": 0, "data": response_str})
