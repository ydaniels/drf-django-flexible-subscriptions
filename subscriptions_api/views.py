from rest_framework import viewsets


from subscriptions_api import serializers, models

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
    queryset = models.PlanCost.objects.all()
    serializer_class = serializers.PlanCostSerializer
    permission_classes = (IsAdminOrReadOnly,)


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.UserSubscriptionSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_staff:
            return models.UserSubscription.objects.all()
        return models.UserSubscription.objects.filter(user=self.request.user)


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
