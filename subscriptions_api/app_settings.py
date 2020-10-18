from django.conf import settings


def string_to_module_and_class(string):
    """Breaks a string to a module and class name component."""
    components = string.split('.')
    component_class = components.pop()
    component_module = '.'.join(components)

    return {
        'module': component_module,
        'class': component_class,
    }


def compile_settings():
    """Compiles and validates all package settings and defaults.
        Provides basic checks to ensure required settings are declared
        and applies defaults for all missing settings.
        Returns:
            dict: All possible Django Flexible Subscriptions settings.
    """
    default_plan_cost_id = getattr(settings, 'DFS_DEFAULT_PLAN_COST_ID', None)
    plans_concrete_module = getattr(
        settings, 'DFS_CONCRETE_PLANS_MODULE', 'subscriptions_api.plans'
    )
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

    subscribe_notify_activate = getattr(
        settings, 'DFS_NOTIFY_ACTIVATE', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_activate_class = string_to_module_and_class(subscribe_notify_activate)

    subscribe_notify_deactivate = getattr(
        settings, 'DFS_NOTIFY_DEACTIVATE', 'subscriptions_api.notifications.EmailNotification'
    )
    subscribe_notify_deactivate_class = string_to_module_and_class(subscribe_notify_deactivate)

    return {
        'notify_processing': subscribe_notify_processing_class,
        'notify_expired': subscribe_notify_expired_class,
        'notify_overdue': subscribe_notify_overdue_class,
        'notify_new': subscribe_notify_new_class,
        'notify_activate': subscribe_notify_activate_class,
        'notify_deactivate': subscribe_notify_deactivate_class,
        'notify_payment_error': subscribe_notify_payment_error_class,
        'notify_payment_success': subscribe_notify_payment_success_class,
        'plans_concrete_module': plans_concrete_module,
        'default_plan_cost_id': default_plan_cost_id
    }


SETTINGS = compile_settings()
