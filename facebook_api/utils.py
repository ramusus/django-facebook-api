from datetime import datetime
import logging
import time

from django.conf import settings
from facegraph import Graph, GraphException
from oauth_tokens.models import AccessToken

__all__ = ['graph']

log = logging.getLogger('facebook_api')


def get_tokens(**kwargs):
    '''
    Get all vkontakte tokens list
    '''
    return AccessToken.objects.filter(provider='facebook', **kwargs).order_by('-granted')


def update_token():
    '''
    Update token from provider and return it
    '''
    return AccessToken.objects.fetch('facebook')


def get_api(used_access_tokens=None, *args, **kwargs):
    '''
    Return API instance with latest token from database
    '''
    token = getattr(settings, 'FACEBOOK_API_ACCESS_TOKEN', None)
    if not token:
        tokens = get_tokens(**kwargs)
        if not tokens:
            update_token()
            tokens = get_tokens(**kwargs)

        if used_access_tokens:
            tokens = tokens.exclude(access_token__in=used_access_tokens)

        token = tokens[0].access_token

    return Graph(token)


def graph(method, recursion_count=0, methods_access_tag=None, used_access_tokens=None, **kwargs):
    '''
    Call API using access_token
    '''
    api = get_api(tag=methods_access_tag, used_access_tokens=used_access_tokens)
    try:
        response = api[method](**kwargs)
    except GraphException, e:
        if e.code == 190:
            update_token()
            return graph(method, **kwargs)
        elif e.code == 17:
            # "User request limit reached", try access_token of another user
            #            log.info("Vkontakte error 'Too many requests per second' on method: %s, recursion count: %d" % (method, recursion_count))
            used_access_tokens = [api.access_token] + (used_access_tokens or [])
            return graph(method, methods_access_tag, used_access_tokens, **kwargs)
        elif 'An unexpected error has occurred. Please retry your request later' in str(e):
            time.sleep(1)
            return graph(method, recursion_count + 1, **kwargs)
        else:
            raise e
    except ValueError, e:
        log.warning("ValueError: %s registered while executing method %s with params %s" % (e, method, kwargs))
        # sometimes returns this dictionary, sometimes empty response, covered by test "test_empty_result"
        # data = {"error_code":1,"error_msg":"An unknown error occurred"}
        return None
    except Exception, e:
        log.error("Unhandled error: %s registered while executing method %s with params %s" % (e, method, kwargs))
        raise e

    if getattr(response, 'error_code', None):
        error = "Error %s: %s returned while executing method %s with params %s" % (
            response.error_code, response.error_msg, method, kwargs)
        log.error(error)
        if recursion_count >= 3:
            raise Exception(error)
        time.sleep(1)
        return graph(method, recursion_count + 1, **kwargs)

    return response


def get_improperly_configured_field(app_name, decorate_property=False):
    def field(self):
        raise ImproperlyConfigured("Application '%s' not in INSTALLED_APPS" % app_name)
    if decorate_property:
        field = property(field)
    return field


class UnknownResourceType(Exception):
    pass


def get_or_create_from_small_resource(resource):
    '''
    Return instance of right type based on dictionary resource from Facebook API Graph
    '''
    from facebook_applications.models import Application
    from facebook_pages.models import Page
    from facebook_users.models import User

    try:
        return Page.objects.get(graph_id=resource['id'])
    except Page.DoesNotExist:
        try:
            return User.objects.get(graph_id=resource['id'])
        except User.DoesNotExist:
            try:
                return Application.objects.get(graph_id=resource['id'])
            except Application.DoesNotExist:
                pass

    keys = sorted(resource.keys())
    defaults = dict(resource)
    del defaults['id']
    if keys == ['category', 'id', 'name'] or keys == ['category', 'category_list', 'id', 'name']:
        # resource is a page
        if 'category_list' in defaults:
            del defaults['category_list']
        return Page.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name']:
        # resource is a user
        return User.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name', 'namespace']:
        # resource is a application
        return Application.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    else:
        raise UnknownResourceType("Resource with strange keys: %s" % keys)
