#! /usr/bin/env python
# -*- coding: utf-8 -*-

from alipay import AliPay
from django.conf import settings


class MyAliPay(AliPay):
    DEFAULT_ALI_PAY_CONFIG = settings.THIRD_PART_CONFIG["ALI_PAY"]["default"]

    def __init__(self, *args, **kwargs):
        super(MyAliPay, self).__init__(*args, **kwargs)

    def get_pay_url(self, out_trade_no, total_amount, subject):
        """
        获取支付页面URL
        :param out_trade_no: str,系统内唯一订单号
        :param total_amount: float,总价格，保留两位小数
        :param subject: str，主题，将会显示到支付页面
        :return: str
        """
        order_string = self.api_alipay_trade_page_pay(
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            subject=subject,
            return_url=self.DEFAULT_ALI_PAY_CONFIG['return_url'],
            notify_url=self.DEFAULT_ALI_PAY_CONFIG['notify_url']  # 可选, 不填则使用默认notify url
        )
        return self._gateway + "?" + order_string

    def trade(self, data: dict) -> bool:
        """
        对数据进行验签
        :param data:
        :return:
        """
        signature = data.pop("sign")
        # verification
        success = self.verify(data, signature)
        return success


class AliApi(object):
    # 默认的支付配置
    DEFAULT_ALI_PAY_CONFIG = settings.THIRD_PART_CONFIG["ALI_PAY"]["default"]
    # APP私钥
    APP_PRIVATE_KEY_STRING = open(DEFAULT_ALI_PAY_CONFIG["app_private_key_path"]).read()
    # 阿里公钥
    ALIPAY_PUBLIC_KEY_STRING = open(DEFAULT_ALI_PAY_CONFIG["alipay_public_key_path"]).read()

    def __init__(self):
        # 支付类业务
        self.pay = MyAliPay(
            appid=self.DEFAULT_ALI_PAY_CONFIG['app_id'],
            app_notify_url=self.DEFAULT_ALI_PAY_CONFIG['notify_url'],  # 默认回调url
            app_private_key_string=self.APP_PRIVATE_KEY_STRING,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=self.ALIPAY_PUBLIC_KEY_STRING,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=self.DEFAULT_ALI_PAY_CONFIG['debug'],  # 默认False
        )


ali_api = AliApi()

if __name__ == '__main__':
    import os

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'luffy_boy.settings')
    import django
    import uuid

    django.setup()
    url = ali_api.pay.get_pay_url(uuid.uuid1().hex, 11.1, 'test')
