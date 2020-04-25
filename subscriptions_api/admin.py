from django.contrib import admin
from swapper import load_model
from subscriptions_api.models import PlanList, PlanListDetail, PlanTag, PlanCost, SubscriptionPlan

UserSubscription = load_model('subscriptions_api', 'UserSubscription')
SubscriptionTransaction = load_model('subscriptions_api', 'SubscriptionTransaction')

admin.site.register(PlanTag)
admin.site.register(PlanCost)
admin.site.register(SubscriptionPlan)
admin.site.register(PlanList)
admin.site.register(PlanListDetail)
admin.site.register(UserSubscription)
admin.site.register(SubscriptionTransaction)
