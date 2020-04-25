"""Models Gotten from the Flexible Subscriptions app.
    with minor changes
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from subscriptions_api.base_models import BaseUserSubscription, BaseSubscriptionTransaction, \
    SubscriptionTransactionModel, SubscriptionPlan, UserSubscriptionModel


# ----------------------------------------------------------------------------

class UserSubscription(BaseUserSubscription):
    class Meta:
        swappable = UserSubscriptionModel


class SubscriptionTransaction(BaseSubscriptionTransaction):
    class Meta:
        swappable = SubscriptionTransactionModel


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

    def __str__(self):
        return self.title


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
        help_text=_('HTML content to display for plan'),
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
