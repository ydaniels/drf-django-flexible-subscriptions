from django.utils import timezone

from subscriptions import models


class UserSubscription(models.UserSubscription):
    """UserSubscription Proxy model to allow generation of transactions directly"""

    class Meta:
        proxy = True

    def record_transaction(self, transaction_date=None):
        """Records transaction details in SubscriptionTransaction.
            Parameters:

                transaction_date (obj): A DateTime object of when
                    payment occurred (defaults to current datetime if
                    none provided).
            Returns:
                obj: The created SubscriptionTransaction instance.
        """
        if transaction_date is None:
            transaction_date = timezone.now()

        return models.SubscriptionTransaction.objects.create(
            user=self.user,
            subscription=self.subscription,
            date_transaction=transaction_date,
            amount=self.subscription.cost,
        )

    def activate_user_subscription(self):
        self.active = True
        self.cancelled = False
        self._add_user_to_group()
        self.save()

    def deactivate_user_subscription(self):
        self.active = False
        self.cancelled = True
        self._remove_user_from_group()
        self.save()

    def _add_user_to_group(self):
        try:
            group = self.subscription.plan.group
            group.user_set.add(self.user)
        except AttributeError:
            # No group available to add user to
            pass

    def _remove_user_from_group(self):
        try:
            group = self.subscription.plan.group
            group.user_set.remove(self.user)
        except AttributeError:
            # No group available to add user to
            pass

    def notify_expired(self):
        """Sends notification of expired subscription.

        """

    def notify_new(self):
        """Sends notification of newly active subscription

        """

    def notify_payment_error(self):
        """Sends notification of a payment error

        """

    def notify_payment_success(self):
        """Sends notifiation of a payment success

        """


class PlanCost(models.PlanCost):
    """PlanCost Proxy model that includes helper method to create user subscription
    see https://github.com/studybuffalo/django-flexible-subscriptions/blob/master/subscriptions/views.py#840

    """

    class Meta:
        proxy = True

    def setup_user_subscription(self, user, active=True, no_multipe_subscription=True, del_multipe_subscription=False):
        """Adds subscription to user and adds them to required group if active.
            Parameters:
                user (obj): A Django user instance.
                active (obj): Add user to required group if active.
                no_multipe_sub (bool) :  Only allow one subscription for a user at a time by removing user old subscriptions
            Returns:
                obj: The newly created UserSubscription instance.
        """
        if no_multipe_subscription:
            previous_subscriptions = UserSubscription.objects.filter(user=user).all()
            for sub in previous_subscriptions:
                sub.deactivate_user_subscription()
                if del_multipe_subscription:
                    sub.delete()

        current_date = timezone.now()

        # Add subscription plan to user
        subscription = UserSubscription.objects.create(
            user=user,
            subscription=self,
            date_billing_start=current_date,
            date_billing_end=None,
            date_billing_last=current_date,
            date_billing_next=self.next_billing_datetime(current_date),
            active=active,
            cancelled=False,
        )

        # Add user to the proper group

        if active:
            subscription.activate_user_subscription()

        return subscription
