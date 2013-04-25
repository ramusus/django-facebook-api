from oauth_tokens.models import AccessToken
from facegraph import Graph, GraphException
from datetime import datetime
import logging

__all__ = ['api_call']

log = logging.getLogger('facebook_api')

def get_tokens():
    '''
    Get all vkontakte tokens list
    '''
    return AccessToken.objects.filter(provider='facebook').order_by('-granted')

def update_token():
    '''
    Update token from provider and return it
    '''
    return AccessToken.objects.get_from_provider('facebook')

def get_api():
    '''
    Return API instance with latest token from database
    '''
    tokens = get_tokens()
    if not tokens:
        update_token()
        tokens = get_tokens()
    t = tokens[0]
    return Graph(t.access_token)

def graph(method, **kwargs):
    '''
    Call API using access_token
    '''
    try:
        return get_api()[method](**kwargs)
    except GraphException, e:
        if e.code == 190:
            update_token()
            return graph(method, **kwargs)
        elif 'An unexpected error has occurred. Please retry your request later' in str(e):
            sleep(1)
            return graph(method, **kwargs)
        else:
            raise e
    except JSONDecodeError, e:
        log.error("JSONDecodeError error: %s registered while executing method %s with params %s" % (e, method, kwargs))
        raise e
    except Exception, e:
        log.error("Unhandled error: %s registered while executing method %s with params %s" % (e, method, kwargs))
        raise e