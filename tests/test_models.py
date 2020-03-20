from django.test import TestCase
from django.contrib.auth.models import User, Group
import pytest

from subscriptions.models import SubscriptionPlan, SubscriptionTransaction
from subscriptions_api.models import PlanCost, UserSubscription

pytestmark = pytest.mark.django_db


class TestProxyModel(TestCase):

    def setUp(self):
        username = 'api_user'
        password = 'apipw'
        self.user = User.objects.create_user(username, 'api_user@example.com', password)

    def create_subscription_plan(self, name):
        group, _ = Group.objects.get_or_create(name=name)
        plan, _ = SubscriptionPlan.objects.get_or_create(plan_name=name, group=group)
        cost, _ = PlanCost.objects.get_or_create(plan=plan)
        return cost

    def test_can_setup_active_user_subscription_from_cost(self):
        plan_name = 'Standard Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True)
        active_subscription = self.user.subscriptions.get(subscription__plan__plan_name=plan_name)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(active_subscription.subscription, cost)
        self.assertEqual(active_subscription, subscription)
        self.assertTrue(active_subscription.active)
        self.assertFalse(active_subscription.cancelled)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_setup_inactive_subscription(self):
        plan_name = 'Basic Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=False)
        active_subscription = self.user.subscriptions.get(subscription__plan__plan_name=plan_name)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(active_subscription.subscription, cost)
        self.assertEqual(active_subscription, subscription)
        self.assertFalse(active_subscription.active)
        self.assertFalse(active_subscription.cancelled)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_activate_user_subscription_directly(self):
        plan_name = 'Extended Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=False)
        active_subscription = self.user.subscriptions.get(subscription__plan__plan_name=plan_name)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertFalse(active_subscription.active)
        self.assertEqual(active_subscription, subscription)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())
        subscription.activate_user_subscription()
        active_subscription.refresh_from_db()
        self.assertTrue(active_subscription.active)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_deactivate_user_subscription_directly(self):
        plan_name = 'Cool Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True)
        active_subscription = self.user.subscriptions.get(subscription__plan__plan_name=plan_name)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertTrue(active_subscription.active)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

        self.assertEqual(active_subscription, subscription)

        subscription.deactivate_user_subscription()
        active_subscription.refresh_from_db()
        self.assertFalse(active_subscription.active)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_user_subscription_transaction_generated(self):
        plan_name = 'Fake Plan'
        cost = self.create_subscription_plan(plan_name)
        subscription = cost.setup_user_subscription(self.user, active=True)
        subscription.record_transaction()
        transaction_exist = SubscriptionTransaction.objects.filter(user=self.user,
                                                                   subscription=subscription.subscription).exists()
        self.assertTrue(transaction_exist)

    def test_user_no_multiple_subscriptions_allowed(self):
        plan_name = 'Fake Plan 1'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True)
        plan_name = 'Fake Plan 2'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True)
        subscriptions = UserSubscription.objects.filter(user=self.user)
        self.assertFalse(all(sub.active is True for sub in subscriptions.all()))

    def test_user_only_allowed_single_subscription_at_a_time(self):
        plan_name = 'Fake Plan 3'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True, del_multipe_subscription=True)
        plan_name = 'Fake Plan 4'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True, del_multipe_subscription=True)
        subscriptions_count = UserSubscription.objects.filter(user=self.user).count()
        self.assertEqual(subscriptions_count, 1)

    def tearDown(self):
        self.user.delete()
