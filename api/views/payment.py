import random

import redis
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import Course, CouponRecord, PricePolicy, Order, OrderDetail
from api.utils.ali_api import ali_api
from api.utils.auth import ExpiringJWTAuthentication
from api.utils.exceptions import CommonException
from api.utils.response import BaseResponse

REDIS_CONN = redis.Redis(decode_responses=True)


class PaymentView(APIView):
    authentication_classes = [ExpiringJWTAuthentication]

    def get_pay_url(self, request, order_number, final_price):
        pay_url = ali_api.pay.get_pay_url(out_trade_no=order_number, total_amount=final_price, subject="课程")
        return pay_url

    def get_order_num(self):
        now = timezone.now()
        orderType = "1"
        dateStr4yyyyMMddHHmmss = "{0}{1}{2}{3}{4}{5}".format(now.year, now.month, now.day, now.hour, now.minute,
                                                             now.second)
        rand = str(random.randint(1000, 9999))
        s = orderType + dateStr4yyyyMMddHHmmss + rand
        return s

    def post(self, request, *args, **kwargs):
        """
        重新计算总价格，生成订单，返回支付URL
        模拟请求数据格式：
        {
        is_beli:true,
        course_list=[
            {
                course_id:1
                default_price_policy_id:1,
                coupon_record_id:2
            },
            {
                course_id:2
                default_price_policy_id:4,
                coupon_record_id:6
            }
            ],
        global_coupon_id:3,
        pay_money:298
        }

        状态码：
            1300:  成功
            1301:  课程不存在
            1302:  价格策略不合法
            1303:  加入购物车失败
            1304:  获取购物车失败
            1305:  贝里数有问题
            1306:  优惠券异常
            1307:  优惠券未达到最低消费
            1308:  支付总价格异常

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        response = BaseResponse()
        # 1 获取数据
        user_id = request.user.pk
        global_coupon_id = request.data.get("global_coupon_id")
        pay_money = request.data.get("pay_money")
        course_list = request.data.get("course_list")
        is_beli = request.data.get("is_beli")
        now = timezone.now()
        try:
            # 2 校验数据
            # 2.2 校验课程
            course_price_list = []
            for course_dict in course_list:
                # 2.2.1 校验课程id
                course_id = course_dict.get("course_id")
                course_obj = Course.objects.get(pk=course_id)
                # 2.2.2 价格策略id
                if course_dict.get("default_price_policy_id") not in [obj.pk for obj in course_obj.price_policy.all()]:
                    raise CommonException("价格策略异常！", 1302)
                # 2.2.3 课程优惠券id
                price_policy_obj = PricePolicy.objects.get(pk=course_dict.get("default_price_policy_id"))
                course_dict["original_price"] = price_policy_obj.price
                course_dict["valid_period_display"] = price_policy_obj.get_valid_period_display()
                course_dict["valid_period"] = price_policy_obj.valid_period
                coupon_record_id = course_dict.get("coupon_record_id")
                if coupon_record_id:
                    coupon_record_list = CouponRecord.objects.filter(account=request.user,
                                                                     status=0,
                                                                     coupon__valid_begin_date__lt=now,
                                                                     coupon__valid_end_date__gt=now,
                                                                     coupon__content_type_id=9,
                                                                     coupon__object_id=course_id
                                                                     )
                    if coupon_record_id and coupon_record_id not in [obj.pk for obj in coupon_record_list]:
                        raise CommonException("课程优惠券异常！", 1306)
                    # 计算循环课程的课程优惠券优惠后的价格
                    coupon_record_obj = CouponRecord.objects.get(pk=coupon_record_id)
                    rebate_price = self.cal_coupon_price(price_policy_obj.price, coupon_record_obj)
                    course_price_list.append(rebate_price)
                    course_dict["rebate_price"] = rebate_price
                else:
                    course_price_list.append(price_policy_obj.price)
            # 2.3 校验通用优惠券id
            if global_coupon_id:
                global_coupon_record_list = CouponRecord.objects.filter(account=request.user,
                                                                        status=0,
                                                                        coupon__valid_begin_date__lt=now,
                                                                        coupon__valid_end_date__gt=now,
                                                                        coupon__content_type_id=9,
                                                                        coupon__object_id=None
                                                                        )
                if global_coupon_id and global_coupon_id not in [obj.pk for obj in global_coupon_record_list]:
                    raise CommonException("通用优惠券异常", 1306)
                global_coupon_record_obj = CouponRecord.objects.get(pk=global_coupon_id)
                final_price = self.cal_coupon_price(sum(course_price_list), global_coupon_record_obj)
            else:
                final_price = sum(course_price_list)
            # 2.4 计算实际支付价格与money做校验
            cost_beli_num = 0
            if is_beli:
                final_price = final_price - request.user.beli / 10
                cost_beli_num = request.user.beli
                if final_price < 0:
                    final_price = 0
                    cost_beli_num = int(final_price * 10)
            if final_price != float(pay_money):
                raise CommonException(1308, "支付总价格异常！")

            # 3 生成订单记录
            order_number = self.get_order_num()
            order_obj = Order.objects.create(
                payment_type=1,
                order_number=order_number,
                account=request.user,
                status=1,
                actual_amount=pay_money,
            )
            for course_item in course_list:
                OrderDetail.objects.create(
                    order=order_obj,
                    content_type_id=9,
                    object_id=course_item.get("course_id"),
                    original_price=course_item.get("original_price"),
                    price=course_item.get("rebate_price") or course_item.get("original_price"),
                    valid_period=course_item.get("valid_period"),
                    valid_period_display=course_item.get("valid_period_display"),
                )
            # 3 保存数据
            request.user.beli = request.user.beli - cost_beli_num
            request.user.save()
            REDIS_CONN.set(order_number + "|" + str(cost_beli_num), "", 20)
            # 删除 redis 中 account 信息
            account_key = settings.ACCOUNT_KEY % user_id
            REDIS_CONN.delete(account_key)
            # 4 获取支付URL
            response.data = self.get_pay_url(request, order_number, final_price)

        except ObjectDoesNotExist as e:
            response.code = 1301
            response.msg = "课程不存在！"
        except CommonException as e:
            response.code = e.code
            response.msg = e.error
        except Exception as e:
            response.code = 5000
            response.msg = str(e)

        return Response(response.dict)

    def cal_coupon_price(self, price, coupon_record_obj):
        coupon_type = coupon_record_obj.coupon.coupon_type
        money_equivalent_value = coupon_record_obj.coupon.money_equivalent_value
        off_percent = coupon_record_obj.coupon.off_percent
        minimum_consume = coupon_record_obj.coupon.minimum_consume
        rebate_price = 0
        if coupon_type == 0:  # 立减券
            rebate_price = price - money_equivalent_value
            if rebate_price <= 0:
                rebate_price = 0
        elif coupon_type == 1:  # 满减券
            if minimum_consume > price:
                raise CommonException(1307, "优惠券未达到最低消费")
            else:
                rebate_price = price - money_equivalent_value
        elif coupon_type == 2:
            rebate_price = price * off_percent / 100

        return rebate_price


def get_pay_url(request):
    res = BaseResponse()
    order_number = request.GET.get("order_number")
    final_price = request.GET.get("final_price")
    stat = Order.objects.filter(order_number=order_number, actual_amount=float(final_price))
    if stat:
        pay_url = ali_api.pay.get_pay_url(out_trade_no=order_number, total_amount=final_price, subject="test")
        res.data = {"pay_url": pay_url}
    else:
        res.code = 1402
        res.msg = '订单不存在'
    return JsonResponse(res.dict)
