from rest_framework import routers
from .views import PlanTagViewSet, PlanCostViewSet, PlanListDetailViewSet, \
    PlanListViewSet, SubscriptionPlanViewSet, SubscriptionTransactionViewSet, \
    UserSubscriptionViewSet

app_name = 'subscriptions_api'

router = routers.SimpleRouter()
router.register('plan-tags', PlanTagViewSet, basename='plan-tags')
router.register('plan-costs', PlanCostViewSet, basename='plan-costs')
router.register('planlist-details', PlanListDetailViewSet, basename='planlist-details')
router.register('planlist', PlanListViewSet, basename='planlist')
router.register('subscription-plans', SubscriptionPlanViewSet, basename='subscription-plans')
router.register('subscription-transactions', SubscriptionTransactionViewSet, basename='subscription-transactions')
router.register('user-subscriptions', UserSubscriptionViewSet, basename='user-subscriptions')

urlpatterns = router.urls
