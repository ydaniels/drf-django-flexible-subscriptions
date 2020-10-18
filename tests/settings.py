DEBUG = True

SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'subscriptions_api'
]
SUBSCRIPTIONS_API_SUBSCRIPTIONTRANSACTION_MODEL = 'subscriptions_api.SubscriptionTransaction'
SUBSCRIPTIONS_API_USERSUBSCRIPTION_MODEL = 'subscriptions_api.UserSubscription'
