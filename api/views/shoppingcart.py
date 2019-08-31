import json

import redis
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Course, PricePolicy
from api.utils.auth import ExpiringJWTAuthentication
from api.utils.exceptions import CommonException
from api.utils.response import BaseResponse

REDIS_CONN = redis.Redis(decode_responses=True)


class ShoppingCarView(APIView):
    authentication_classes = [ExpiringJWTAuthentication, ]

    def post(self, request):
        res = BaseResponse()
        try:
            # 1 获取前端传过来的 course_id、price_policy_id
            course_id = request.data.get("course_id", "")
            price_policy_id = request.data.get("price_policy_id", "")
            user_id = request.user.id
            # 2 验证数据的合法性
            # 2.1 验证course_id是否合法
            course_obj = Course.objects.get(pk=course_id)
            # 2.2 校验价格策略是否能合法
            # 查找课程关联的价格策略
            price_policy_list = course_obj.price_policy.all()
            price_policy_dict = {}
            for price_policy in price_policy_list:
                price_policy_dict[price_policy.pk] = {
                    "prcie": price_policy.price,
                    "valid_period": price_policy.valid_period,
                    "valid_period_text": price_policy.get_valid_period_display(),
                    "default": price_policy.pk == price_policy_id
                }

            if price_policy_id not in price_policy_dict:
                raise CommonException(1201, "价格策略异常!")

            # 3 构建数据结构
            # 价格策略对象
            pp = PricePolicy.objects.get(pk=price_policy_id)
            course_info = {
                "id": course_id,
                "name": course_obj.name,
                "course_img": course_obj.course_img,
                "relate_price_policy": price_policy_dict,
                "default_price": pp.price,
                "default_price_period": pp.valid_period,
                "default_price_policy_id": pp.pk
            }
            # 4 写入redis
            # 4.1 先拼接购物车的key
            shopping_car_key = settings.SHOPPING_CAR_KEY % (user_id, course_id)
            # 4.2 写入redis
            REDIS_CONN.set(shopping_car_key, json.dumps(course_info))
            res.msg = "加入购物车成功!"

        except CommonException as e:
            res.code = e.code
            res.error = e.error
        except Exception as e:
            res.code = 1202
            res.error = "加入购物车失败!"
        return Response(res.dict)

    def get(self, request):
        res = BaseResponse()
        try:
            # 1 取到user_id
            user_id = request.user.id
            # 2 拼接购物车的key
            shopping_car_key = settings.SHOPPING_CAR_KEY % (user_id, "*")
            # 3 去redis读取该用户的所有加入购物车的课程
            # 3.1 先去模糊匹配出所有符合要求的key
            all_keys = REDIS_CONN.keys(shopping_car_key)
            # 3.2 循环所有的keys 得到每个可以
            shopping_car_list = []
            for key in all_keys:
                course_info = json.loads(REDIS_CONN.get(key))
                shopping_car_list.append(course_info)
            res.data = {"shopping_car_list": shopping_car_list, "total": len(shopping_car_list)}
        except Exception as e:
            res.code = 1233
            res.error = "获取购物车失败"
        return Response(res.dict)

    def delete(self, request):
        res = BaseResponse()
        try:
            # 获取前端传过来的course_id
            course_id = request.data.get("course_id", "")
            user_id = request.user.id
            # 判断课程id是否合法
            shopping_car_key = settings.SHOPPING_CAR_KEY % (user_id, course_id)
            if not REDIS_CONN.exists(shopping_car_key):
                res.code = 1203
                res.error = "删除的课程不存在"
                return Response(res.dict)
            # 删除redis中的数据
            REDIS_CONN.delete(shopping_car_key)
            res.data = "删除成功"
        except Exception as e:
            res.code = 1204
            res.error = "删除失败"
        return Response(res.dict)
