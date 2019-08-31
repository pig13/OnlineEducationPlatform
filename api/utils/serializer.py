from rest_framework import serializers

from api import models


class CourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Course
        fields = (
            "id",
            "name",
        )


class CourseSerializer(serializers.ModelSerializer):
    level = serializers.CharField(source="get_level_display")
    coursedetail_id = serializers.CharField(source="coursedetail.pk")

    class Meta:
        model = models.Course
        fields = (
            'id',
            'name',
            'course_img',
            'brief',
            'level',
            "coursedetail_id"
        )

    def to_representation(self, instance):

        data = super(CourseSerializer, self).to_representation(instance)
        # 购买人数
        # data["people_buy"] = instance.order_details.all().count()
        # 价格套餐列表
        price_policies = instance.price_policy.all().order_by("price").only("price")

        price = getattr(price_policies.first(), "price", 0)

        if price_policies and price == 0:
            is_free = True
            price = "免费"
            origin_price = "原价￥{}".format(price_policies.last().price)
        else:
            is_free = False
            price = "￥{}".format(price)
            origin_price = None

        # 是否免费
        data["is_free"] = is_free
        # 展示价格
        data["price"] = price
        # 原价
        data["origin_price"] = origin_price

        return data


class CourseDetailSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="course.name")
    prices = serializers.SerializerMethodField()
    brief = serializers.StringRelatedField(source='course.brief')
    study_all_time = serializers.StringRelatedField(source='hours')
    level = serializers.CharField(source='course.get_level_display')

    teachers_info = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    recommend_coursesinfo = serializers.SerializerMethodField()

    # learnnumber = serializers.SerializerMethodField()
    # OftenAskedQuestion = serializers.SerializerMethodField()

    class Meta:
        model = models.CourseDetail
        fields = "__all__"

    def get_prices(self, obj):
        return PricePolicySerializer(
            obj.course.price_policy.all(), many=True, context=self.context
        ).data

    def get_study_all_time(self, obj):
        return "30小时"

    def get_recommend_coursesinfo(self, obj):
        courses = RecommendCourseSerializer(obj.recommend_courses.all(), many=True)
        return courses.data

    def get_teachers_info(self, obj):
        teachers = TeacherSerializer(obj.teachers.all(), many=True)
        return teachers.data

    def get_is_online(self, obj):
        if obj.course.status == 0:
            return True
        elif obj.course.status == 2:
            return False
        else:
            return ''

    # def get_learnnumber(self, obj):
    #     return obj.course.order_details.all().count()

    # def get_OftenAskedQuestion(self, obj):
    #     question_queryset = models.OftenAskedQuestion.objects.filter(content_type__model='Course',
    #                                                        object_id=obj.course.id)
    #     serializer = OftenAskedQuestionSerializer(question_queryset, many=True)
    #     return serializer.data
    #


class RecommendCourseSerializer(serializers.ModelSerializer):
    course_id = serializers.CharField(source="pk")
    course_name = serializers.CharField(source="name")

    class Meta:
        model = models.Course
        fields = ('course_id', 'course_name',)


class PricePolicySerializer(serializers.ModelSerializer):
    valid_period_name = serializers.StringRelatedField(source="get_valid_period_display")

    class Meta:
        model = models.PricePolicy
        fields = ('id', 'valid_period', 'valid_period_name', 'price',)


class CourseChapterSerializer(serializers.ModelSerializer):
    chapter_name = serializers.SerializerMethodField()
    chapter_symbol = serializers.SerializerMethodField()

    class Meta:
        model = models.CourseChapter
        fields = (
            'id',
            'chapter_name',
            'chapter_symbol',
        )

    def get_chapter_name(self, instance):
        return '第%s章·%s' % (instance.chapter, instance.name)

    def get_chapter_symbol(self, instance):
        return "chapter_%s_%s" % (self.context.get('enrolled_course_id', 1), instance.id)

    def to_representation(self, instance):
        data = super(CourseChapterSerializer, self).to_representation(instance)

        queryset = instance.coursesections.all().order_by("order")
        # 获取章节对应的课时数量
        data["section_of_count"] = queryset.count()
        data["free_trail"] = queryset.filter(free_trail=True).exists()
        data["coursesections"] = SectionSerializer(
            queryset, many=True, read_only=True, context=self.context
        ).data

        return data


class SectionSerializer(serializers.ModelSerializer):
    #  暂时未用到
    pass


class OftenAskedQuestionSerializer(serializers.ModelSerializer):
    question_tittle = serializers.SerializerMethodField()
    question_answer = serializers.SerializerMethodField()

    class Meta:
        model = models.OftenAskedQuestion
        fields = ('question_tittle', 'question_answer')

    def get_question_tittle(self, obj):
        return obj.question

    def get_question_answer(self, obj):
        return obj.answer


class TeacherSerializer(serializers.ModelSerializer):
    teacher_id = serializers.CharField(source="pk")
    teacher_name = serializers.CharField(source="name")
    teacher_brief = serializers.CharField(source="brief")
    teacher_image = serializers.CharField(source="image")

    class Meta:
        model = models.Teacher
        fields = ('teacher_id', 'teacher_name', 'title', 'signature', 'teacher_image', 'teacher_brief')


class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserInfo
        fields = "__all__"
