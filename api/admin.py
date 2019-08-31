from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(UserInfo)
admin.site.register(Course)
admin.site.register(CourseDetail)
admin.site.register(CourseChapter)
admin.site.register(CourseSection)
admin.site.register(PricePolicy)
admin.site.register(Teacher)
admin.site.register(Coupon)
admin.site.register(CouponRecord)
admin.site.register(Order)
admin.site.register(OrderDetail)
admin.site.register(CourseCategory)
