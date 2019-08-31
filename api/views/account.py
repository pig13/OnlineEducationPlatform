import datetime
import json

import redis
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import CouponRecord, Course, PricePolicy
from api.utils.auth import ExpiringJWTAuthentication
from api.utils.exceptions import CommonException
from api.utils.response import BaseResponse

REDIS_CONN = redis.Redis(decode_responses=True)


class AccountView(APIView):
    """
    结算接口
    """
    authentication_classes = [ExpiringJWTAuthentication, ]

    def get_coupon_list(self, request, course_id=None):

        now = datetime.datetime.utcnow()

        coupon_record_list = CouponRecord.objects.filter(
            account=request.user,
            status=0,
            coupon__valid_begin_date__lte=now,
            coupon__valid_end_date__gt=now,
            coupon__content_type_id=9,  # 8 对应了content_type中的course表的id
            coupon__object_id=course_id  # 对应的课程

        )

        coupon_list = []

        for coupon_record in coupon_record_list:
            coupon_list.append({
                "pk": coupon_record.pk,
                "name": coupon_record.coupon.name,
                "coupon_type": coupon_record.coupon.get_coupon_type_display(),
                "money_equivalent_value": coupon_record.coupon.money_equivalent_value,
                "off_percent": coupon_record.coupon.off_percent,
                "minimum_consume": coupon_record.coupon.minimum_consume,
            })

        return coupon_list

    def post(self, request, *args, **kwargs):
        """
        根据前端传来的 [{"course_id":1,"price_policy_id":2},]  新建一个 account 存储到 redis
        :param request:
        :param args:
        :param kwargs:q
        :return:
        """
        user = request.user
        course_list = request.data
        response = BaseResponse()
        try:
            # 创建存储到redis的数据结构
            redis_data = {}
            redis_data['account_course_list'] = []
            price_list = []
            for course_dict in course_list:
                course_id = course_dict.get("course_id")
                price_policy_id = course_dict.get("price_policy_id")
                # 校验课程是否存在
                course_obj = Course.objects.get(pk=course_id)
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
                    raise CommonException(1102, "价格策略异常!")
                pp = PricePolicy.objects.get(pk=price_policy_id)
                # 将课程信息加入到每一个课程结算字典中
                account_dict = {
                    "id": course_id,
                    "name": course_obj.name,
                    "course_img": course_obj.course_img,
                    "relate_price_policy": price_policy_dict,
                    "default_price": pp.price,
                    "rebate_price": pp.price,
                    "default_price_period": pp.valid_period,
                    "default_price_policy_id": pp.pk
                }
                # 课程价格加入到价格列表
                price_list.append(float(pp.price))

                # 查询当前用户拥有未使用的，在有效期的且与当前课程相关的优惠券
                account_dict["coupon_list"] = self.get_coupon_list(request, course_id)
                # 记录当前课程信息
                redis_data['account_course_list'].append(account_dict)
            # 获取通用优惠券
            redis_data['global_coupons'] = self.get_coupon_list(request)
            # 计算总价格
            redis_data['total_price'] = sum(price_list)
            # 存储到redis中
            account_key = settings.ACCOUNT_KEY % user.pk
            REDIS_CONN.set(account_key, json.dumps(redis_data))
        except ObjectDoesNotExist as e:
            response.code = 1103
            response.error = "课程不存在!"
        except CommonException as e:
            response.code = e.code
            response.error = e.error

        return Response(response.dict)

    def get(self, request, *args, **kwargs):
        """
        获取post请求创建的数据
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        res = BaseResponse()
        try:
            account_key = settings.ACCOUNT_KEY % request.user.pk
            data = json.loads(REDIS_CONN.get(account_key))
            data['total'] = len(data['account_course_list'])
            res.data = data
        except Exception as e:
            res.code = 1101
            res.error = "获取购物车失败"
        return Response(res.dict)

    def cal_coupon_price(self, price, coupon_info):

        coupon_type = coupon_info["coupon_type"]
        money_equivalent_value = coupon_info.get("money_equivalent_value")
        off_percent = coupon_info.get("off_percent")
        minimum_consume = coupon_info.get("minimum_consume")
        rebate_price = 0
        if coupon_type == "立减券":  # 立减券
            rebate_price = price - money_equivalent_value
            if rebate_price <= 0:
                rebate_price = 0
        elif coupon_type == "满减券":  # 满减券
            if minimum_consume > price:
                raise CommonException(1104, "优惠券未达到最低消费")
            else:
                rebate_price = price - money_equivalent_value
        elif coupon_type == "折扣券":
            rebate_price = price * off_percent / 100

        return rebate_price

    def put(self, request, *args, **kwargs):
        """
        根据前端传来 {"is_beli":"true","choose_coupons":{"global_coupon_id":id,course_id:coupon_id}} ,动态计算总价格返回
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        res = BaseResponse()
        try:
            # 获取数据
            choose_coupons = request.data.get("choose_coupons")
            is_beli = request.data.get("is_beli")
            # 获取结算课程列表
            cal_price = {}
            account_key = settings.ACCOUNT_KEY % request.user.pk
            data = json.loads(REDIS_CONN.get(account_key))
            account_course_list = data.get("account_course_list")
            # 构建 account_courses_info 数据结构
            '''
            account_courses_info = {
                'id': {
                    'coupon': {
                        'pk': '',
                        'name': '',
                        'coupon_type': '',
                        'money_equivalent_value': '',
                        'off_percent': 111,
                        'minimum_consume': 111
                    },
                    'default_price': 11
                }
            }
            '''
            account_courses_info = {}
            for account_course in account_course_list:
                temp = {
                    "coupon": {},
                    "default_price": account_course["default_price"]
                }
                account_courses_info[account_course["id"]] = temp
                for item in account_course["coupon_list"]:
                    coupon_id = choose_coupons.get(str(account_course["id"]))
                    if coupon_id == item["pk"]:
                        temp["coupon"] = item
            # 计算每个课程优惠后的价格
            price_list = []
            for key, val in account_courses_info.items():
                if not val.get("coupon"):
                    price_list.append(val["default_price"])
                    cal_price[key] = val["default_price"]
                else:
                    coupon_info = val.get("coupon")
                    default_price = val["default_price"]
                    rebate_price = self.cal_coupon_price(default_price, coupon_info)
                    price_list.append(rebate_price)
                    cal_price[key] = rebate_price
            # 总价格
            total_price = sum(price_list)
            # 计算通用优惠券的价格
            global_coupon_id = choose_coupons.get("global_coupon_id")
            if global_coupon_id:
                global_coupons = data.get("global_coupons")
                global_coupon_dict = {}
                for item in global_coupons:
                    global_coupon_dict[item["pk"]] = item
                total_price = self.cal_coupon_price(total_price, global_coupon_dict[global_coupon_id])
            # 计算贝里，贝里——》平台货币
            if json.loads(is_beli):
                total_price = total_price - request.user.beli / 10
                if total_price < 0:
                    total_price = 0
            cal_price["total_price"] = total_price
            res.data = cal_price
        except CommonException as e:
            res.code = e.code
            res.msg = e.error
        except Exception as e:
            res.code = 5000
            res.msg = str(e)
        return Response(res.dict)
