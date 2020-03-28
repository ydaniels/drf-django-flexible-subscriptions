from rest_framework import viewsets

from subscriptions import models
from subscriptions_api import serializers

from .models import PlanCost, UserSubscription
from .permissions import IsAdminOrReadOnly


class PlanTagViewSet(viewsets.ModelViewSet):
    queryset = models.PlanTag.objects.all()
    serializer_class = serializers.PlanTagSerializer
    permission_classes = (IsAdminOrReadOnly,)


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = models.SubscriptionPlan.objects.all()
    serializer_class = serializers.SubscriptionPlanSerializer
    permission_classes = (IsAdminOrReadOnly,)


class PlanCostViewSet(viewsets.ModelViewSet):
    queryset = PlanCost.objects.all()
    serializer_class = serializers.PlanCostSerializer
    permission_classes = (IsAdminOrReadOnly,)


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.UserSubscriptionSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserSubscription.objects.all()
        return UserSubscription.objects.filter(user=self.request.user)


class SubscriptionTransactionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.SubscriptionTransactionSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.SubscriptionTransaction.objects.all()
        return models.SubscriptionTransaction.objects.filter(user=self.request.user)


class PlanListViewSet(viewsets.ModelViewSet):
    queryset = models.PlanList.objects.all()
    serializer_class = serializers.PlanListSerializer
    permission_classes = (IsAdminOrReadOnly,)


class PlanListDetailViewSet(viewsets.ModelViewSet):
    queryset = models.PlanListDetail.objects.all()
    serializer_class = serializers.PlanListDetailSerializer
    permission_classes = (IsAdminOrReadOnly,)
