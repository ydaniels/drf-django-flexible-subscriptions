drf-django-flexible-subscriptions
======================================

|build-status-image| |pypi-version| |PythonVersions| |DjangoVersions| |DRFVersions|

Overview
--------

Expose API views for Django Flexible Subscriptions

Requirements
------------

-  Python (3.6, 3.7, 3.8)
-  Django (2.0, 2.1, 2.2, 3.0)
-  Django REST Framework (3.9, 3.10, 3.11)

Installation
------------

Install using ``pip``\ …

.. code:: bash

    $ pip install drf-django-flexible-subscriptions

Example
-------
To use in
   *settings.py*

.. code:: python

    INSTALLED_APPS = [
                        ...,
                        'rest_framework',
                        'subscriptions_api',
                        ]

*urls.py**

.. code-block:: python

        url(r'^api/subscriptions/', include('subscriptions_api.urls')),

This will expose the following **django-flexible-subscriptions** endpoints with only read access for normal user and write access for admin
 - api/subscriptions/plan-tags/
 - api/subscriptions/plan-costs/
 - api/subscriptions/planlist-details/
 - api/subscriptions/planlist/
 - api/subscriptions/subscription-plans/
 - api/subscriptions/subscription-transactions/
 - api/subscriptions/user-subscriptions/

For subscribing user to a plan **drf-django-flexible-subscriptions** provides few helper method through a proxy model to the main  django-flexible-subscriptions  **PlanCost** and **UserSubscriptions** models, so you can implement your payment logic in any way you want without binding to a specific view e.g

*models.py*

.. code-block:: python

     from subscriptions_api.models import PlanCost, UserSubscription

     class PaymentModel(models.Model):
          cost = models.ForeignKey(PlanCost, null=True, on_delete=models.SET_NULL)

*views.py*

.. code-block:: python

    #you can subscribe user to a plan by
    subscription = cost.setup_user_subscription(request.user, active=False, no_multipe_subscription=True)

    #with active=False user subscription would not be activated immediately use active=True for otherwise

    #no_multiple_sub prevents user from being subscribed to more than one plan at time previous plan will be removed

    #After successful user payment you can activate_subscription by using subscription above from setup or

    subscription = UserSubscription.objects.get(user=request.user)

    #or for user with multiple active subscription when no_multipe_sub=False

    subscription = UserSubscription.objects.get(user=request.user, cost=cost)

    subscription.activate_user_subscription() #Activate  subscription

    #deactivate subscription with

    subscription.deactivate_user_subscription()

    #You can also record transaction

    subscription.record_transaction()




Testing
-------

Install testing requirements.

.. code:: bash

    $ pip install -r requirements.txt

Run with runtests.

.. code:: bash

    $ ./runtests.py

You can also use the excellent `tox`_ testing tool to run the tests
against all supported versions of Python and Django. Install tox
globally, and then simply run:

.. code:: bash

    $ tox

Documentation
-------------

To build the documentation, you’ll need to install ``mkdocs``.

.. code:: bash

    $ pip install mkdocs

To preview the documentation:

.. code:: bash

    $ mkdocs serve
    Running at: http://127.0.0.1:8000/

To build the documentation:

.. code:: bash

    $ mkdocs build

.. _tox: http://tox.readthedocs.org/en/latest/

.. |build-status-image| image:: https://secure.travis-ci.org/ydaniels/drf-django-flexible-subscriptions.svg?branch=master
   :target: http://travis-ci.org/ydaniels/drf-django-flexible-subscriptions?branch=master
.. |pypi-version| image:: https://img.shields.io/pypi/v/drf-django-flexible-subscriptions.svg
   :target: https://pypi.python.org/pypi/drf-django-flexible-subscriptions
.. |PythonVersions| image:: https://img.shields.io/badge/python-3.6%7C3.7%7C3.8-blue
   :alt: PyPI - Python Version
.. |DjangoVersions| image:: https://img.shields.io/badge/django-2.0%7C2.1%7C2.2%7C3.0-blue
   :alt: Django Version
.. |DRFVersions| image:: https://img.shields.io/badge/drf-3.9%7C3.10%7C3.11-blue
   :alt: DRF Version