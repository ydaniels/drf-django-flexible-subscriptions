from django.conf import settings
from subscriptions.conf import string_to_module_and_class


def compile_settings():
    """Compiles and validates all package settings and defaults.
        Provides basic checks to ensure required settings are declared
        and applies defaults for all missing settings.
        Returns:
            dict: All possible Django Flexible Subscriptions settings.
    """
    subscribe_notify_processing = getattr(
        settings, 'DFS_NOTIFY_PROCESSING', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_processing_class = string_to_module_and_class(subscribe_notify_processing)

    subscribe_notify_expired = getattr(
        settings, 'DFS_NOTIFY_EXPIRED', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_expired_class = string_to_module_and_class(subscribe_notify_expired)

    subscribe_notify_overdue = getattr(
        settings, 'DFS_NOTIFY_OVERDUE', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_overdue_class = string_to_module_and_class(subscribe_notify_overdue)

    subscribe_notify_new = getattr(
        settings, 'DFS_NOTIFY_NEW', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_new_class = string_to_module_and_class(subscribe_notify_new)

    subscribe_notify_payment_error = getattr(
        settings, 'DFS_NOTIFY_ERROR', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_payment_error_class = string_to_module_and_class(subscribe_notify_payment_error)

    subscribe_notify_payment_success = getattr(
        settings, 'DFS_NOTIFY_PAYMENT_SUCCESS', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_payment_success_class = string_to_module_and_class(subscribe_notify_payment_success)

    return {
        'notify_processing_manager': subscribe_notify_processing_class,
        'notify_expired_manager': subscribe_notify_expired_class,
        'notify_overdue_manager': subscribe_notify_overdue_class,
        'notify_new_manager': subscribe_notify_new_class,
        'notify_payment_error_manager': subscribe_notify_payment_error_class,
        'notify_payment_success_manager': subscribe_notify_payment_success_class,
    }


SETTINGS = compile_settings()
