import swapper
from rest_framework import serializers
from subscriptions_api import models

UserSubscriptionModel = swapper.load_model('subscriptions_api', 'UserSubscription')
SubscriptionTransactionModel = swapper.load_model('subscriptions_api', 'SubscriptionTransaction')


class PlanTagSerializer(serializers.ModelSerializer):
    """Serializer for PlanTag model"""

    class Meta:
        model = models.PlanTag
        fields = '__all__'


class PlanCostSerializer(serializers.ModelSerializer):
    """PlanCost model serializer with property fields  exposed as serializer method fields"""
    recurrent_unit_text = serializers.SerializerMethodField()
    billing_frequency_text = serializers.SerializerMethodField()

    def get_recurrent_unit_text(self, obj):
        return obj.display_recurrent_unit_text

    def get_billing_frequency_text(self, obj):
        return obj.display_billing_frequency_text

    class Meta:
        model = models.PlanCost
        fields = '__all__'


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model and Tags can be created directly on it"""

    tags = PlanTagSerializer(many=True, read_only=True)
    tags_str = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    costs = PlanCostSerializer(many=True, read_only=True)

    def get_tags_str(self, obj):
        return obj.display_tags()

    def get_features(self, obj):
        return obj.get_features()

    class Meta:
        model = models.SubscriptionPlan
        fields = '__all__'


class PlanListDetailSerializer(serializers.ModelSerializer):
    """PlanListDetail serializer"""
    plan = SubscriptionPlanSerializer()

    class Meta:
        model = models.PlanListDetail
        fields = '__all__'

    def to_internal_value(self, data):
        self.fields['plan'] = serializers.PrimaryKeyRelatedField(queryset=models.SubscriptionPlan.objects.all())
        return super(PlanListDetailSerializer, self).to_internal_value(data)

    def to_representation(self, obj):
        self.fields['plan'] = SubscriptionPlanSerializer()
        return super(PlanListDetailSerializer, self).to_representation(obj)


class PlanListSerializer(serializers.ModelSerializer):
    """PlanList serializer"""
    plan_list_details = PlanListDetailSerializer(many=True, read_only=True)
    features = serializers.SerializerMethodField()

    class Meta:
        model = models.PlanList
        fields = '__all__'

    def get_features(self, obj):
        return obj.get_features()


class SubscriptionTransactionSerializer(serializers.ModelSerializer):
    """SubscriptionTransaction serializer"""

    class Meta:
        model = SubscriptionTransactionModel
        fields = '__all__'


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User subscription model serializer"""
    transactions = SubscriptionTransactionSerializer(many=True, read_only=True)
    description = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscriptionModel
        fields = '__all__'

    def get_description(self, obj):
        return obj.description
