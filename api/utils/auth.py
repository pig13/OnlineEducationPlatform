#! /usr/bin/env python
# -*- coding: utf-8 -*-

import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from api.models import UserInfo


class ExpiringJWTAuthentication(BaseAuthentication):

    def decode_jwt(self, jwt_token):
        try:
            res = jwt.decode(jwt_token, settings.JWT_KEY)
        except Exception:
            res = None
        return res

    def authenticate(self, request):
        """
        校验JWT是否存在、篡改、过期
        :param request:
        :return:
        """
        if request.method == "OPTIONS":
            return None
        jwt_token = request.META.get("HTTP_AUTHORIZATION")
        payload = self.decode_jwt(jwt_token)
        if not payload:
            raise AuthenticationFailed("认证失败!")
        now = timezone.now().timestamp()
        if payload['exp'] < now:
            raise AuthenticationFailed("JWT已过期!")
        uid = payload['uid']
        user = UserInfo.objects.filter(uid=uid).first()
        if not user:
            raise AuthenticationFailed("用户不存在!")
        return user, jwt_token
