from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User, Group
import pytest
import swapper
from subscriptions_api.models import SubscriptionPlan, PlanCost, DAY, MONTH, WEEK, YEAR
pytestmark = pytest.mark.django_db

UserSubscription = swapper.load_model('subscriptions_api', 'UserSubscription')
SubscriptionTransaction = swapper.load_model('subscriptions_api', 'SubscriptionTransaction')


@pytestmark
class TestSubscriptionModel(TestCase):

    def setUp(self):
        username = 'api_user'
        password = 'apipw'
        self.user = User.objects.create_user(username, 'api_user@example.com', password)

    def create_subscription_plan(self, name, **kwargs):
        group, _ = Group.objects.get_or_create(name=name)
        plan, _ = SubscriptionPlan.objects.get_or_create(plan_name=name, group=group)
        cost, _ = PlanCost.objects.get_or_create(plan=plan, **kwargs)
        return cost

    def test_can_setup_active_user_subscription_from_cost(self):
        plan_name = 'Standard Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True)
        active_subscription = self.user.subscriptions.get(plan_cost=cost)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(active_subscription.plan_cost, cost)
        self.assertEqual(active_subscription, subscription)
        self.assertTrue(active_subscription.active)
        self.assertFalse(active_subscription.cancelled)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_setup_active_user_subscription_with_custom_date(self):
        plan_name = 'Custom Standard Plan'
        date = timezone.now() + timedelta(days=8)
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, subscription_date=date)
        active_subscription = self.user.subscriptions.get(plan_cost=cost)
        self.assertEqual(active_subscription.date_billing_start, date)

    def test_can_setup_inactive_subscription(self):
        plan_name = 'Basic Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=False)
        active_subscription = self.user.subscriptions.get(plan_cost=cost)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertEqual(active_subscription.plan_cost, cost)
        self.assertEqual(active_subscription, subscription)
        self.assertFalse(active_subscription.active)
        self.assertFalse(active_subscription.cancelled)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_activate_user_subscription_directly_custom_date(self):
        plan_name = 'Custom Extended Plan'
        cost = self.create_subscription_plan(plan_name)
        grace_period_days = 2
        cost.plan.grace_period = grace_period_days
        cost.plan.save()
        date = timezone.now() - timedelta(days=30)
        subscription = cost.setup_user_subscription(self.user, active=False)
        subscription.activate(subscription_date=date)
        self.assertEqual(subscription.date_billing_start, date)
        self.assertEqual(subscription.date_billing_next, cost.next_billing_datetime(date))
        self.assertEqual(subscription.date_billing_end, cost.next_billing_datetime(date) + timedelta(grace_period_days))

    def test_can_activate_user_subscription_directly(self):
        plan_name = 'Extended Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=False)
        active_subscription = self.user.subscriptions.get(plan_cost=cost)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertFalse(active_subscription.active)
        self.assertEqual(active_subscription, subscription)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())
        subscription.activate()
        active_subscription.refresh_from_db()
        self.assertTrue(active_subscription.active)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_can_deactivate_user_subscription_directly(self):
        plan_name = 'Cool Plan'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True)
        active_subscription = self.user.subscriptions.get(plan_cost=cost)
        subscription = UserSubscription.objects.get(user=self.user)
        self.assertTrue(active_subscription.active)
        self.assertTrue(self.user.groups.filter(name=cost.plan.group.name).exists())

        self.assertEqual(active_subscription, subscription)

        subscription.deactivate()
        active_subscription.refresh_from_db()
        self.assertFalse(active_subscription.active)
        self.assertFalse(self.user.groups.filter(name=cost.plan.group.name).exists())

    def test_user_subscription_transaction_generated(self):
        plan_name = 'Fake Plan'
        cost = self.create_subscription_plan(plan_name)
        subscription = cost.setup_user_subscription(self.user, active=True)
        subscription.record_transaction()
        transaction_exist = SubscriptionTransaction.objects.filter(user=self.user,
                                                                   subscription=subscription).exists()
        self.assertTrue(transaction_exist)

    def test_auto_generated_transaction(self):
        plan_name = 'Fake Plan'
        cost = self.create_subscription_plan(plan_name)
        subscription = cost.setup_user_subscription(self.user, active=True, record_transaction=True)
        self.assertEqual(subscription.transactions.count(), 1)

    def test_transaction_auto_paid(self):
        plan_name = 'Fake Plan'
        cost = self.create_subscription_plan(plan_name)
        subscription = cost.setup_user_subscription(self.user, active=False)
        transaction = subscription.record_transaction()
        self.assertFalse(transaction.paid)
        subscription.activate(mark_transaction_paid=True)
        transaction.refresh_from_db()
        self.assertTrue(transaction.paid)

    def test_daily_day_cost(self):
        cost = self.create_subscription_plan('Super Saver')
        cost.cost = 100
        cost.recurrence_unit = DAY
        cost.recurrence_period = 2
        cost.save()
        self.assertEqual(cost.daily_cost, 50)

    def test_daily_weekly_cost(self):
        cost = self.create_subscription_plan('Weeky Super Saver')
        cost.cost = 9.99
        cost.recurrence_unit = WEEK
        cost.recurrence_period = 1
        cost.save()
        self.assertEqual(cost.daily_cost, 9.99 / 7)

    def test_daily_monthly_cost(self):
        cost = self.create_subscription_plan('Monthly Super Saver')
        cost.cost = 29.99
        cost.recurrence_unit = MONTH
        cost.recurrence_period = 1
        cost.save()
        self.assertEqual(cost.daily_cost, 29.99 / 30.4368)

    def test_daily_yearly_cost(self):
        cost = self.create_subscription_plan('Yearly Super Saver')
        cost.cost = 1029.99
        cost.recurrence_unit = YEAR
        cost.recurrence_period = 10
        cost.save()
        self.assertEqual(cost.daily_cost, 1029.99 / 3652.425)

    def test_subscription_used_daily_balance(self):
        cost = self.create_subscription_plan('Limited Spot', recurrence_unit=MONTH, cost=100)
        used_days = 10
        date = timezone.now() - timedelta(days=used_days)
        subscription = cost.setup_user_subscription(user=self.user, active=True, subscription_date=date)
        self.assertEqual(subscription.used_daily_balance, round(cost.daily_cost * used_days, 2))

    def test_subscription_unsed_daily_balance(self):
        cost = self.create_subscription_plan('Limited Spot', recurrence_unit=MONTH, cost=100)
        used_days = 10

        date = timezone.now() - timedelta(days=used_days)
        next_billing_date = cost.next_billing_datetime(date)
        unused_days = (next_billing_date - timezone.now()).days
        subscription = cost.setup_user_subscription(user=self.user, active=True, subscription_date=date)
        self.assertEqual(subscription.unused_daily_balance, round(cost.daily_cost * unused_days, 2))

    def test_send_notification(self):
        cost = self.create_subscription_plan('Cool Limited Spot', recurrence_unit=MONTH, cost=100)
        subscription = cost.setup_user_subscription(user=self.user, active=True)
        notify = subscription.notify_processing()
        self.assertEqual(notify.notification, 'notify_processing')

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
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True,
                                     del_multipe_subscription=True)
        plan_name = 'Fake Plan 4'
        cost = self.create_subscription_plan(plan_name)
        cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True,
                                     del_multipe_subscription=True)
        subscriptions_count = UserSubscription.objects.filter(user=self.user).count()
        self.assertEqual(subscriptions_count, 1)

    def test_subscription_reused(self):
        plan_name = 'Fake Plan 3'
        cost = self.create_subscription_plan(plan_name)
        subscription = cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True,
                                                    del_multipe_subscription=True)
        subscription_2 = cost.setup_user_subscription(self.user, active=True, no_multipe_subscription=True)
        self.assertNotEqual(subscription, subscription_2)
        plan_name = 'Fake Plan 4'
        cost_2 = self.create_subscription_plan(plan_name)
        subscription_3 = cost_2.setup_user_subscription(self.user, active=True, no_multipe_subscription=True, resuse=True)
        subscription_4 = cost_2.setup_user_subscription(self.user, active=True, no_multipe_subscription=True, resuse=True)
        self.assertEqual(subscription_3, subscription_4)

    def tearDown(self):
        self.user.delete()
