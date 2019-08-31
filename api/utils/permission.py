#! /usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework.permissions import BasePermission


class LoginUserPermission(BasePermission):

    def has_permission(self, request, view):
        if request.user:
            return True
        else:
            return False
