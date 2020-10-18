import swapper
from datetime import timedelta
import importlib
from uuid import uuid4
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from subscriptions_api.app_settings import SETTINGS

SubscriptionTransactionModel = swapper.get_model_name('subscriptions_api', 'SubscriptionTransaction')
UserSubscriptionModel = swapper.get_model_name('subscriptions_api', 'UserSubscription')


class BaseUserSubscription(models.Model):
    """Details of a user's specific subscription."""
    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
        verbose_name='ID',
    )
    user = models.ForeignKey(
        get_user_model(),
        help_text=_('the user this subscription applies to'),
        null=True,
        on_delete=models.CASCADE,
        related_name='subscriptions',
    )
    plan_cost = models.ForeignKey(
        'subscriptions_api.PlanCost',
        help_text=_('the plan costs and billing frequency for this user'),
        null=True,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    reference = models.CharField(
        help_text=_('External System Reference'),
        max_length=100,
        null=True,
        blank=True,
    )
    date_billing_start = models.DateTimeField(
        blank=True,
        help_text=_('the date to start billing this subscription'),
        null=True,
        verbose_name='billing start date',
    )
    date_billing_end = models.DateTimeField(
        blank=True,
        help_text=_('the date to finish billing this subscription'),
        null=True,
        verbose_name='billing start end',
    )
    date_billing_last = models.DateTimeField(
        blank=True,
        help_text=_('the last date this plan was billed'),
        null=True,
        verbose_name='last billing date',
    )
    date_billing_next = models.DateTimeField(
        blank=True,
        help_text=_('the next date billing is due'),
        null=True,
        verbose_name='next start date',
    )
    active = models.BooleanField(
        default=True,
        help_text=_('whether this subscription is active or not'),
    )
    due = models.BooleanField(
        default=False,
        help_text=_('whether this subscription is due or not'),
    )
    cancelled = models.BooleanField(
        default=False,
        help_text=_('whether this subscription is cancelled or not'),
    )

    class Meta:
        ordering = ('user', 'date_billing_start',)
        abstract = True

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

        if amount is None:
            amount = self.plan_cost.cost
        SubscriptionTransaction = swapper.load_model('subscriptions_api', 'SubscriptionTransaction')
        return SubscriptionTransaction.objects.create(
            user=self.user,
            subscription=self,  # A transaction should link to is subscription
            date_transaction=transaction_date,
            amount=amount,
        )

    @property
    def unused_daily_balance(self):
        """
        Calculate unused balance  of a subscription for a particular period
        """
        current_date = timezone.now()
        if self.date_billing_next > current_date:
            days_left = (self.date_billing_next - current_date).days
            return round(days_left * self.plan_cost.daily_cost, 2)
        return 0

    @property
    def description(self):
        if self.plan_cost:
            text = f'{self.plan_cost.plan.plan_name} {self.plan_cost.display_billing_frequency_text}'
            return text

    @property
    def used_daily_balance(self):
        """
        Calculate used balance  of a subscription for a particular period
        """
        current_date = timezone.now()
        if current_date > self.date_billing_start:
            days_used = (current_date - self.date_billing_start).days
            return round(days_used * self.plan_cost.daily_cost, 2)
        return 0

    def activate(self, subscription_date=None, mark_transaction_paid=True):
        current_date = subscription_date or timezone.now()
        next_billing_date = self.plan_cost.next_billing_datetime(current_date)
        self.active = True
        self.cancelled = False
        self.due = False
        self.date_billing_start = current_date
        self.date_billing_end = next_billing_date + timedelta(days=self.plan_cost.plan.grace_period)
        self.date_billing_next = next_billing_date
        self._add_user_to_group()
        if mark_transaction_paid:
            self.transactions.update(paid=True)
        self.save()

    def deactivate(self):
        current_date = timezone.now()
        self.active = False
        self.date_billing_last = current_date
        self.cancelled = True
        self.due = False
        self._remove_user_from_group()
        self.save()
        self.plan_cost.activate_default_subscription(self.user)

    def _add_user_to_group(self):
        try:
            group = self.plan_cost.plan.group
            group.user_set.add(self.user)
        except AttributeError:
            # No group available to add user to
            pass

    def _remove_user_from_group(self):
        try:
            group = self.plan_cost.plan.group
            group.user_set.remove(self.user)
        except AttributeError:
            # No group available to add user to
            pass

    def notify(self, notifier, **kwargs):
        """
        param notififer: notifie class that takes usersubscription object and has a send method
        """
        if SETTINGS[notifier] is None:
            return
        Notify = getattr(  # pylint: disable=invalid-name
            importlib.import_module(SETTINGS[notifier]['module']),
            SETTINGS[notifier]['class']
        )
        notify_obj = Notify(self, notifier, **kwargs)
        notify_obj.send()
        return notify_obj

    def notify_processing(self, **kwargs):
        """Sends notification of processing subscription.

        """
        return self.notify('notify_processing', **kwargs)

    def notify_expired(self, **kwargs):
        """Sends notification of expired subscription.

        """
        return self.notify('notify_expired', **kwargs)

    def notify_overdue(self, **kwargs):
        """Sends notification of overdue subscription.

        """
        return self.notify('notify_overdue', **kwargs)

    def notify_new(self, **kwargs):
        """Sends notification of new subscription

        """
        return self.notify('notify_new', **kwargs)

    def notify_activate(self, **kwargs):
        """Sends notification of activated subscription

        """
        return self.notify('notify_activate', **kwargs)

    def notify_deactivate(self, **kwargs):
        """Sends notification of deactivated subscription

        """
        return self.notify('notify_deactivate', **kwargs)

    def notify_payment_error(self, **kwargs):
        """Sends notification of a payment error

        """
        return self.notify('notify_payment_error', **kwargs)

    def notify_payment_success(self, **kwargs):
        """Sends notifiation of a payment success

        """
        return self.notify('notify_payment_success', **kwargs)


class BaseSubscriptionTransaction(models.Model):
    """Details for a subscription plan billing."""
    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
        verbose_name='ID',
    )
    user = models.ForeignKey(
        get_user_model(),
        help_text=_('the user that this subscription was billed for'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='subscription_transactions'
    )
    subscription = models.ForeignKey(
        UserSubscriptionModel,
        help_text=_('the Subscription that were billed'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='transactions'
    )
    date_transaction = models.DateTimeField(
        help_text=_('the datetime the transaction was billed'),
        verbose_name='transaction date',
    )
    amount = models.DecimalField(
        blank=True,
        decimal_places=2,
        help_text=_('how much was billed for the user'),
        max_digits=19,
        null=True,
    )

    paid = models.BooleanField(default=False, help_text=_('Mark transaction has paid'))

    class Meta:
        ordering = ('date_transaction', 'user',)
        abstract = True
