import inspect
import importlib
from subscriptions_api.app_settings import SETTINGS


class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


def get_plans_module():
    module_str = SETTINGS['plans_concrete_module']
    module = importlib.import_module(module_str)
    return inspect.getmembers(module)


def get_plans():
    plans_data = {}
    for name, obj in get_plans_module():
        if isinstance(obj, dict) and name.endswith('_PLAN'):
            obj = dotdict(obj)
            plans_data[obj._name] = obj
    return plans_data


def get_plan_feature(plan_name):
    return get_plans().get(plan_name, None)


def get_planlist_features(feature_ref=None):
    for name, obj in get_plans_module():
        if isinstance(obj, dict):
            if feature_ref and name == 'FEATURES_%s' % (feature_ref):
                return obj
            if not feature_ref and name == 'DEFAULT_FEATURES':
                return obj
    return {}


BASE_PLAN = {'_name': 'BasePlan'}
FEATURES_ONE = {'_name': 'Plan Name'}
