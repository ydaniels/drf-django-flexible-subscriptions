from django.urls import reverse
import pytest
from datetime import datetime
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from subscriptions.models import PlanCost, SubscriptionPlan, PlanList


@pytest.mark.django_db
class BaseTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user('demo_user')
        self.admin_user = User.objects.create_user('admin_user')
        self.admin_user.is_staff = True
        self.admin_user.save()

    def api_client(self, is_staff=True):
        user = self.admin_user if is_staff else self.user
        self.client.force_login(user)
        return self.client

    def test_staff_can_action_tags(self):
        tags_url = reverse('subscriptions_api:plan-tags-list')
        post_data = {'tag': 'Test Tag'}
        # self.client.force_login(self.admin_user)
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(tags_url, data=post_data)

        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['tag'], post_data['tag'])

        tags_url_id = reverse('subscriptions_api:plan-tags-detail', kwargs={'pk': r.data['id']})

        patch_tag_name = 'Patch New Tag'
        r = self.api_client(is_staff=True).patch(tags_url_id, data={'tag': patch_tag_name})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['tag'], patch_tag_name)

        put_tag_name = 'Put New Tag'
        r = self.api_client(is_staff=True).put(tags_url_id, data={'tag': put_tag_name})
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data['tag'], put_tag_name)

        r = self.api_client(is_staff=True).delete(tags_url_id)
        self.assertEqual(r.status_code, status.HTTP_204_NO_CONTENT)

    def test_normal_user_can_only_read_tags(self):
        tags_url = reverse('subscriptions_api:plan-tags-list')
        post_data = {'tag': 'Test Tag'}
        self.client.force_authenticate(self.user)
        r = self.client.post(tags_url, data=post_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.get(tags_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_can_action_subscription_plan(self):
        plans_url = reverse('subscriptions_api:subscription-plans-list')
        plans_data = {'plan_name': 'Standard Plan'}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(plans_url, data=plans_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['plan_name'], plans_data['plan_name'])

    def test_normal_user_can_only_read_subscription_plan(self):
        plans_url = reverse('subscriptions_api:subscription-plans-list')
        plans_data = {'plan_name': 'Standard Plan'}
        self.client.force_authenticate(self.user)
        r = self.client.post(plans_url, data=plans_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.get(plans_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_can_action_subscription_plan_cost(self):
        plan = SubscriptionPlan(plan_name='Premium Plan')
        plan.save()
        cost_url = reverse('subscriptions_api:plan-costs-list')
        cost_data = {'plan': plan.pk}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(cost_url, data=cost_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['plan'], plan.pk)

    def test_normal_user_can_only_read_subscription_plan_cost(self):
        plan = SubscriptionPlan(plan_name='Professional Plan')
        plan.save()
        cost_url = reverse('subscriptions_api:plan-costs-list')
        cost_data = {'plan': plan.pk}
        self.client.force_authenticate(self.user)
        r = self.client.post(cost_url, data=cost_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.get(cost_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_can_create_user_subscription(self):
        plan = SubscriptionPlan(plan_name='Unlimited Plan')
        plan.save()
        cost = PlanCost(cost=9.99, plan=plan)
        cost.save()
        subscription_url = reverse('subscriptions_api:user-subscriptions-list')
        user_sub_data = {'subscription': cost.pk, 'user': self.user.pk}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(subscription_url, data=user_sub_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['subscription'], cost.pk)

    def test_user_can_only_see_own_subscription(self):
        cost = self.create_new_user_plan_cost(plan_name='Free Plan')

        subscription_url = reverse('subscriptions_api:user-subscriptions-list')
        user_sub_data = {'subscription': cost.pk, 'user': self.admin_user.pk}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(subscription_url, data=user_sub_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.user)
        subscription_url_id = reverse('subscriptions_api:user-subscriptions-detail', kwargs={'pk': r.data['id']})
        r = self.client.get(subscription_url_id)
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        r = self.client.get(subscription_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_staff_can_create_user_transaction(self):
        cost = self.create_new_user_plan_cost('Basic Plan')
        transact_data = {'user': self.user.pk, 'subscription': cost.pk, 'date_transaction': datetime.now()}
        transaction_url = reverse('subscriptions_api:subscription-transactions-list')
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(transaction_url, data=transact_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['subscription'], cost.pk)

    def test_user_can_only_see_own_transaction(self):
        cost = self.create_new_user_plan_cost('Smart Plan')
        transact_data = {'user': self.admin_user.pk, 'subscription': cost.pk, 'date_transaction': datetime.now()}
        transaction_url = reverse('subscriptions_api:subscription-transactions-list')
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(transaction_url, data=transact_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.client.force_authenticate(self.user)
        transaction_url_id = reverse('subscriptions_api:subscription-transactions-detail', kwargs={'pk': r.data['id']})
        r = self.client.get(transaction_url_id)
        self.assertEqual(r.status_code, status.HTTP_404_NOT_FOUND)
        r = self.client.get(transaction_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_admin_can_action_planlist(self):
        plan_list_url = reverse('subscriptions_api:planlist-list')
        plan_list_data = {'title': 'Monthly Plans'}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(plan_list_url, data=plan_list_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['title'], plan_list_data['title'])

    def test_user_can_only_read_planlist(self):
        plan_list_url = reverse('subscriptions_api:planlist-list')
        plan_list_data = {'title': 'Quarterly Plans'}
        self.client.force_authenticate(self.user)
        r = self.client.post(plan_list_url, data=plan_list_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.get(plan_list_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_admin_can_action_planlist_detail(self):
        plan_list = PlanList(title='Weekly Plans')
        plan_list.save()
        plan = self.create_new_user_plan(plan_name='Free')
        plan_list_detail_url = reverse('subscriptions_api:planlist-details-list')
        plan_list_detail_data = {'plan': plan.pk, 'plan_list': plan_list.pk}
        self.client.force_authenticate(self.admin_user)
        r = self.client.post(plan_list_detail_url, data=plan_list_detail_data)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data['plan'], plan_list_detail_data['plan'])

    def test_user_can_only_read_planlist_detail(self):
        plan_list = PlanList(title='Bi Weekly Plans')
        plan_list.save()
        plan = self.create_new_user_plan(plan_name='Freemium')
        plan_list_detail_url = reverse('subscriptions_api:planlist-details-list')
        plan_list_detail_data = {'plan': plan.pk, 'plan_list': plan_list.pk}
        self.client.force_authenticate(self.user)
        r = self.client.post(plan_list_detail_url, data=plan_list_detail_data)
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)
        r = self.client.get(plan_list_detail_url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def create_new_user_plan(self, plan_name):
        plan = SubscriptionPlan(plan_name=plan_name)
        plan.save()
        return plan

    def create_new_user_plan_cost(self, plan_name, cost=9.99):
        plan = self.create_new_user_plan(plan_name)
        cost = PlanCost(cost=cost, plan=plan)
        cost.save()
        return cost

    def tearDown(self):
        for user in User.objects.all():
            user.delete()
