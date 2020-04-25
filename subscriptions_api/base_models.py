import swapper
from datetime import timedelta
import importlib
from uuid import uuid4
from django.contrib.auth.models import Group
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from subscriptions_api.app_settings import SETTINGS

# Convenience references for units for plan recurrence billing
# ----------------------------------------------------------------------------
ONCE = '0'
SECOND = '1'
MINUTE = '2'
HOUR = '3'
DAY = '4'
WEEK = '5'
MONTH = '6'
YEAR = '7'
RECURRENCE_UNIT_CHOICES = (
    (ONCE, 'once'),
    (SECOND, 'second'),
    (MINUTE, 'minute'),
    (HOUR, 'hour'),
    (DAY, 'day'),
    (WEEK, 'week'),
    (MONTH, 'month'),
    (YEAR, 'year'),
)

SubscriptionTransactionModel = swapper.get_model_name('subscriptions_api', 'SubscriptionTransaction')
UserSubscriptionModel = swapper.get_model_name('subscriptions_api', 'UserSubscription')


class PlanTag(models.Model):
    """A tag for a subscription plan."""
    tag = models.CharField(
        help_text=_('the tag name'),
        max_length=64,
        unique=True,
    )

    class Meta:
        ordering = ('tag',)

    def __str__(self):
        return self.tag


class SubscriptionPlan(models.Model):
    """Details for a subscription plan."""
    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
        verbose_name='ID',
    )
    plan_name = models.CharField(
        help_text=_('the name of the subscription plan'),
        max_length=128,
    )
    slug = models.SlugField(
        blank=True,
        help_text=_('slug to reference the subscription plan'),
        max_length=128,
        null=True,
        unique=True,
    )
    plan_description = models.CharField(
        blank=True,
        help_text=_('a description of the subscription plan'),
        max_length=512,
        null=True,
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        help_text=_('the Django auth group for this plan'),
        null=True,
        on_delete=models.SET_NULL,
        related_name='plans',
    )
    tags = models.ManyToManyField(
        PlanTag,
        blank=True,
        help_text=_('any tags associated with this plan'),
        related_name='plans',
    )
    grace_period = models.PositiveIntegerField(
        default=0,
        help_text=_(
            'how many days after the subscription ends before the '
            'subscription expires'
        ),
    )

    class Meta:
        ordering = ('plan_name',)
        permissions = (
            ('subscriptions', 'Can interact with subscription details'),
        )

    def __str__(self):
        return self.plan_name

    def display_tags(self):
        """Displays tags as a string (truncates if more than 3)."""
        if self.tags.count() > 3:
            return '{}, ...'.format(
                ', '.join(tag.tag for tag in self.tags.all()[:3])
            )

        return ', '.join(tag.tag for tag in self.tags.all()[:3])


class PlanCost(models.Model):
    """Cost and frequency of billing for a plan."""
    id = models.UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
        verbose_name='ID',
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        help_text=_('the subscription plan for these cost details'),
        on_delete=models.CASCADE,
        related_name='costs',
    )
    slug = models.SlugField(
        blank=True,
        help_text=_('slug to reference these cost details'),
        max_length=128,
        null=True,
        unique=True,
    )
    recurrence_period = models.PositiveSmallIntegerField(
        default=1,
        help_text=_('how often the plan is billed (per recurrence unit)'),
        validators=[MinValueValidator(1)],
    )
    recurrence_unit = models.CharField(
        choices=RECURRENCE_UNIT_CHOICES,
        default=MONTH,
        max_length=1,
    )
    cost = models.DecimalField(
        blank=True,
        decimal_places=2,
        help_text=_('the cost per recurrence of the plan'),
        max_digits=19,
        null=True,
    )

    class Meta:
        ordering = ('recurrence_unit', 'recurrence_period', 'cost',)

    @property
    def display_recurrent_unit_text(self):
        """Converts recurrence_unit integer to text."""
        conversion = {
            ONCE: 'one-time',
            SECOND: 'per second',
            MINUTE: 'per minute',
            HOUR: 'per hour',
            DAY: 'per day',
            WEEK: 'per week',
            MONTH: 'per month',
            YEAR: 'per year',
        }

        return conversion[self.recurrence_unit]

    @property
    def display_billing_frequency_text(self):
        """Generates human-readable billing frequency."""
        conversion = {
            ONCE: 'one-time',
            SECOND: {'singular': 'per second', 'plural': 'seconds'},
            MINUTE: {'singular': 'per minute', 'plural': 'minutes'},
            HOUR: {'singular': 'per hour', 'plural': 'hours'},
            DAY: {'singular': 'per day', 'plural': 'days'},
            WEEK: {'singular': 'per week', 'plural': 'weeks'},
            MONTH: {'singular': 'per month', 'plural': 'months'},
            YEAR: {'singular': 'per year', 'plural': 'years'},
        }

        if self.recurrence_unit == ONCE:
            return conversion[ONCE]

        if self.recurrence_period == 1:
            return conversion[self.recurrence_unit]['singular']

        return 'every {} {}'.format(
            self.recurrence_period, conversion[self.recurrence_unit]['plural']
        )

    def next_billing_datetime(self, current):
        """Calculates next billing date for provided datetime.
            Parameters:
                current (datetime): The current datetime to compare
                    against.
            Returns:
                datetime: The next time billing will be due.
        """
        if self.recurrence_unit == SECOND:
            return current + timedelta(seconds=self.recurrence_period)

        if self.recurrence_unit == MINUTE:
            return current + timedelta(minutes=self.recurrence_period)

        if self.recurrence_unit == HOUR:
            return current + timedelta(hours=self.recurrence_period)

        if self.recurrence_unit == DAY:
            return current + timedelta(days=self.recurrence_period)

        if self.recurrence_unit == WEEK:
            return current + timedelta(weeks=self.recurrence_period)

        if self.recurrence_unit == MONTH:
            # Adds the average number of days per month as per:
            # http://en.wikipedia.org/wiki/Month#Julian_and_Gregorian_calendars
            # This handle any issues with months < 31 days and leap years
            return current + timedelta(
                days=30.4368 * self.recurrence_period
            )

        if self.recurrence_unit == YEAR:
            # Adds the average number of days per year as per:
            # http://en.wikipedia.org/wiki/Year#Calendar_year
            # This handle any issues with leap years
            return current + timedelta(
                days=365.2425 * self.recurrence_period
            )

        return None

    def setup_user_subscription(self, user, active=True, subscription_date=None, no_multipe_subscription=False,
                                del_multipe_subscription=False, record_transaction=False, mark_transaction_paid=True,
                                resuse=False):
        """Adds subscription to user and adds them to required group if active.
            Parameters:
                user (obj): A Django user instance.
                active (bool): Add user to required group if active.
                subscription_date (date) :  Date to use for  creation subscription
            Returns:
                obj: The newly created UserSubscription instance.
        """
        if no_multipe_subscription:
            previous_subscriptions = user.subscriptions.filter(active=True).all()
            for sub in previous_subscriptions:
                sub.deactivate()
                if del_multipe_subscription:
                    sub.delete()

        # Add subscription plan to user
        subscription = None
        if resuse:
            subscription = user.subscriptions.filter(plan_cost=self).first()
        if not subscription:
            UserSubscription = swapper.load_model('subscriptions_api', 'UserSubscription')

            subscription = UserSubscription.objects.create(
                user=user,
                plan_cost=self,
                active=active,
                cancelled=False
            )
        # Add user to the proper group
        if record_transaction:
            subscription.record_transaction(transaction_date=subscription_date)
        if active:
            subscription.activate(subscription_date=subscription_date, mark_transaction_paid=mark_transaction_paid)
        return subscription

    @property
    def daily_cost(self):
        """
        Returns the daily cost for a plan cost period
        """
        if self.recurrence_unit == DAY:
            return float(self.cost) / (1 * self.recurrence_period)

        if self.recurrence_unit == WEEK:
            return float(self.cost) / (7 * self.recurrence_period)

        if self.recurrence_unit == MONTH:
            return float(self.cost) / (30.4368 * self.recurrence_period)

        if self.recurrence_unit == YEAR:
            # Adds the average number of days per year as per:
            # http://en.wikipedia.org/wiki/Year#Calendar_year
            # This handle any issues with leap years
            return float(self.cost) / (365.2425 * self.recurrence_period)

        return 0


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
        PlanCost,
        help_text=_('the plan costs and billing frequency for this user'),
        null=True,
        on_delete=models.CASCADE,
        related_name='subscriptions'
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