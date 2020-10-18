from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save

from subscriptions_api.models import activate_default_user_subscription


@receiver(post_save, sender=get_user_model(), dispatch_uid='assign_default_subscription')
def create_default_subscription(sender, instance, created, **kwargs):
    if created:
        activate_default_user_subscription(instance)
