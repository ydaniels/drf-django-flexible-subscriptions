import importlib
from django.utils import timezone

from subscriptions import models

from subscriptions_api.app_settings import SETTINGS


class UserSubscription(models.UserSubscription):
    """UserSubscription Proxy model to allow generation of transactions directly"""
    SubscriptionTransactionClass = models.SubscriptionTransaction

    class Meta:
        proxy = True

    def record_transaction(self, amount=None, transaction_date=None):
        """Records transaction details in SubscriptionTransaction.
            Parameters:
                amount: Use custom amount to create transaction for the subscription
                transaction_date (obj): A DateTime object of when
                    payment occurred (defaults to current datetime if
                    none provided).
            Returns:
                obj: The created SubscriptionTransaction instance.
        """
        if transaction_date is None:
            transaction_date = timezone.now()

        return self.SubscriptionTransactionClass.objects.create(
            user=self.user,
            subscription=self.subscription,
            date_transaction=transaction_date,
            amount=amount or self.subscription.cost,
        )

    @property
    def unused_daily_balance(self):
        """
        Calculate unused balance  of a subscription for a particular period
        """
        current_date = timezone.now()
        if self.date_billing_next > current_date:
            days_left = (self.date_billing_next - current_date).days
            return round(days_left * self.subscription.daily_cost, 2)
        return 0

    @property
    def used_daily_balance(self):
        """
        Calculate used balance  of a subscription for a particular period
        """
        current_date = timezone.now()
        if current_date > self.date_billing_start:
            days_used = (current_date - self.date_billing_start).days
            return round(days_used * self.subscription.daily_cost, 2)
        return 0

    def activate(self, subscription_date=None):
        current_date = subscription_date or timezone.now()
        self.active = True
        self.cancelled = False
        self.date_billing_start = current_date
        self.date_billing_end = None
        self.date_billing_last = current_date
        self.date_billing_next = self.subscription.next_billing_datetime(current_date)
        self._add_user_to_group()
        self.save()

    def deactivate(self):
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

    def notify(self, notifier):
        """
        param notififer: notifie class that takes usersubscription object and has a send method
        """
        if SETTINGS[notifier] is None:
            return
        Notify = getattr(  # pylint: disable=invalid-name
            importlib.import_module(SETTINGS[notifier]['module']),
            SETTINGS[notifier]['class']
        )
        notify_obj = Notify(self, notifier)
        notify_obj.send()
        return notify_obj

    def notify_processing(self):
        """Sends notification of processing subscription.

        """
        return self.notify('notify_processing_manager')

    def notify_expired(self):
        """Sends notification of expired subscription.

        """
        return self.notify('notify_expired_manager')

    def notify_overdue(self):
        """Sends notification of overdue subscription.

        """
        return self.notify('notify_overdue_manager')

    def notify_new(self):
        """Sends notification of newly active subscription

        """
        return self.notify('notify_new_manager')

    def notify_payment_error(self):
        """Sends notification of a payment error

        """
        return self.notify('notify_payment_error_manager')

    def notify_payment_success(self):
        """Sends notifiation of a payment success

        """
        return self.notify('notify_payment_success_manager')


class PlanCost(models.PlanCost):
    """PlanCost Proxy model that includes helper method to create user subscription
    see https://github.com/studybuffalo/django-flexible-subscriptions/blob/master/subscriptions/views.py#840

    """
    UserSubscriptionClass = UserSubscription

    class Meta:
        proxy = True

    def setup_user_subscription(self, user, active=True, subscription_date=None, no_multipe_subscription=False, del_multipe_subscription=False):
        """Adds subscription to user and adds them to required group if active.
            Parameters:
                user (obj): A Django user instance.
                active (bool): Add user to required group if active.
                subscription_date (date) :  Date to use for  creation subscription
            Returns:
                obj: The newly created UserSubscription instance.
        """
        if no_multipe_subscription:
            previous_subscriptions = self.UserSubscriptionClass.objects.filter(user=user, active=True).all()
            for sub in previous_subscriptions:
                sub.deactivate()
                if del_multipe_subscription:
                    sub.delete()

        # Add subscription plan to user
        subscription = UserSubscription.objects.create(
            user=user,
            subscription=self,
            active=active,
            cancelled=False
        )

        # Add user to the proper group

        if active:
            subscription.activate(subscription_date=subscription_date)

        return subscription

    @property
    def daily_cost(self):
        """
        Returns the daily cost for a plan cost period
        """
        if self.recurrence_unit == models.DAY:
            return float(self.cost) / (1 * self.recurrence_period)

        if self.recurrence_unit == models.WEEK:
            return float(self.cost) / (7 * self.recurrence_period)

        if self.recurrence_unit == models.MONTH:
            return float(self.cost) / (30.4368 * self.recurrence_period)

        if self.recurrence_unit == models.YEAR:
            # Adds the average number of days per year as per:
            # http://en.wikipedia.org/wiki/Year#Calendar_year
            # This handle any issues with leap years
            return float(self.cost) / (365.2425 * self.recurrence_period)

        return 0
