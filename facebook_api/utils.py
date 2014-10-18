from django.conf import settings
from oauth_tokens.models import AccessToken
from facegraph import Graph, GraphException
from datetime import datetime
import time
import logging

__all__ = ['graph']

log = logging.getLogger('facebook_api')

ACCESS_TOKEN = getattr(settings, 'FACEBOOK_API_ACCESS_TOKEN', None)

def get_tokens():
    '''
    Get all vkontakte tokens list
    '''
    return AccessToken.objects.filter(provider='facebook').order_by('-granted')

def update_token():
    '''
    Update token from provider and return it
    '''
    return AccessToken.objects.fetch('facebook')

def get_api(used_access_tokens=None, *args, **kwargs):
    '''
    Return API instance with latest token from database
    '''
    if ACCESS_TOKEN:
        token = ACCESS_TOKEN
    else:
        tokens = get_tokens()
        if not tokens:
            update_token()
            tokens = get_tokens()

        if used_access_tokens:
            tokens = tokens.exclude(access_token__in=used_access_tokens)

        token = tokens[0].access_token

    return Graph(token)

def graph(method, methods_access_tag=None, used_access_tokens=None, **kwargs):
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
            return graph(method, **kwargs)
        else:
            raise e
    except ValueError, e:
        log.warning("ValueError: %s registered while executing method %s with params %s" % (e, method, kwargs))
        # sometimes returns this dictionary, sometimes empty response, covered by test "test_empty_result"
        data = {"error_code":1,"error_msg":"An unknown error occurred"}
        return None
    except Exception, e:
        log.error("Unhandled error: %s registered while executing method %s with params %s" % (e, method, kwargs))
        raise e

    if getattr(response, 'error_code', None):
        log.error("Error %s: %s returned while executing method %s with params %s" % (response.error_code, response.error_msg, method, kwargs))
        time.sleep(1)
        return graph(method, **kwargs)

    return response