"""Models Gotten from the Flexible Subscriptions app.
    with minor changes
"""
from datetime import timedelta
from uuid import uuid4
import swapper
import json
from django.contrib.auth.models import Group
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from subscriptions_api.app_settings import SETTINGS
from subscriptions_api.base_models import BaseUserSubscription, BaseSubscriptionTransaction

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


# ----------------------------------------------------------------------------

class UserSubscription(BaseUserSubscription):
    class Meta:
        swappable = swapper.swappable_setting('subscriptions_api', 'UserSubscription')


class SubscriptionTransaction(BaseSubscriptionTransaction):
    class Meta:
        swappable = swapper.swappable_setting('subscriptions_api', 'SubscriptionTransaction')


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
    feature_ref = models.CharField(
        blank=True,
        help_text=_('Reference to select list of allowed features for this plan'),
        max_length=100,
        null=True,
        unique=True,
    )
    features = models.TextField(
        blank=True,
        help_text=_('list of json allowed features for this plan'),
        null=True
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
    trial_period = models.PositiveIntegerField(
        default=0,
        help_text=_(
            'how many days to give free before the subscription '
            'subscription begins'
        ),
    )

    class Meta:
        ordering = ('plan_name',)
        permissions = (
            ('subscriptions', 'Can interact with subscription details'),
        )

    def get_features(self):
        if self.features:
            return json.loads(self.features)
        return {}

    def __getattr__(self, name):
        feature_dict = self.get_features()
        if feature_dict:
            try:
                return feature_dict[name]
            except KeyError:
                pass
        raise AttributeError

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

    def activate_default_subscription(self, user):
        activate_default_user_subscription(user=user)

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

    def __str__(self):
        return '{} {} {}'.format(self.plan.plan_name, self.display_billing_frequency_text, self.cost)


class PlanList(models.Model):
    """Model to record details of a display list of SubscriptionPlans."""
    title = models.TextField(
        blank=True,
        help_text=_('title to display on the subscription plan list page'),
        null=True,
    )
    slug = models.SlugField(
        blank=True,
        help_text=_('slug to reference the subscription plan list'),
        max_length=128,
        null=True,
        unique=True,
    )
    features = models.TextField(
        blank=True,
        help_text=_('Json dict for allowed features to display for the plan list'),
        null=True
    )
    subtitle = models.TextField(
        blank=True,
        help_text=_('subtitle to display on the subscription plan list page'),
        null=True,
    )
    header = models.TextField(
        blank=True,
        help_text=_('header text to display on the subscription plan list page'),
        null=True,
    )
    footer = models.TextField(
        blank=True,
        help_text=_('header text to display on the subscription plan list page'),
        null=True,
    )
    active = models.BooleanField(
        default=True,
        help_text=_('whether this plan list is active or not.'),
    )

    def get_features(self):
        if self.features:
            return json.loads(self.features)
        return {}

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title',)


class PlanListDetail(models.Model):
    """Model to add additional details to plans when part of PlanList."""
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='plan_list_details',
    )
    plan_list = models.ForeignKey(
        PlanList,
        on_delete=models.CASCADE,
        related_name='plan_list_details',
    )
    html_content = models.TextField(
        blank=True,
        help_text=_('HTML content can also be json object to display for plan'),
        null=True,
    )
    subscribe_button_text = models.CharField(
        blank=True,
        default='Subscribe',
        max_length=128,
        null=True,
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text=_('Order to display plan in (lower numbers displayed first)'),
    )

    def __str__(self):
        return 'Plan List {} - {}'.format(
            self.plan_list, self.plan.plan_name
        )

    class Meta:
        ordering = ('order',)


def activate_default_user_subscription(user):
    plan_cost_id = SETTINGS['default_plan_cost_id']
    if plan_cost_id:
        cost_obj = PlanCost.objects.get(pk=plan_cost_id)
        cost_obj.setup_user_subscription(user, active=True, no_multipe_subscription=True,
                                         record_transaction=True, mark_transaction_paid=True,
                                         resuse=True)
