#! /usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework.filters import BaseFilterBackend


class CourseFilter(BaseFilterBackend):
    """
    课程展示 过滤器
    """

    def filter_queryset(self, request, queryset, view):
        extra = {}
        category_id = str(request.query_params.get("category_id"))
        # 如果分类ID不是数字或分类ID传输的为0
        if not category_id.isdigit() or category_id == "0":
            extra = extra
        else:
            extra.update({"course_category_id": category_id})
        return queryset.filter(**extra)
