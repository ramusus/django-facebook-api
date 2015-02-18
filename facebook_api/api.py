import time

from django.conf import settings
from facegraph import Graph, GraphException as FacebookError
from oauth_tokens.models import AccessToken
from oauth_tokens.api import ApiAbstractBase, Singleton

__all__ = ['api_call', 'FacebookError']


class FacebookApi(ApiAbstractBase):

    __metaclass__ = Singleton

    provider = 'facebook'
    error_class = FacebookError

    def call(self, method, methods_access_tag=None, *args, **kwargs):
        response = super(FacebookApi, self).call(method, methods_access_tag=methods_access_tag, *args, **kwargs)

        if getattr(response, 'error_code', None):
            error = "Error %s: %s returned while executing method %s with params %s" % (
                response.error_code, response.error_msg, self.method, kwargs)
            self.logger.error(error)
            if self.recursion_count >= 3:
                raise Exception(error)
            time.sleep(1)
            return self.repeat_call(*args, **kwargs)

        return response

    def get_consistent_token(self):
        return getattr(settings, 'FACEBOOK_API_ACCESS_TOKEN', None)

    def get_tokens(self, **kwargs):
        return AccessToken.objects.filter_active_tokens_of_provider(self.provider, **kwargs)

    def get_api(self, **kwargs):
        return Graph(self.get_token(**kwargs))

    def get_api_response(self, *args, **kwargs):
        try:
            return getattr(self.api, self.method)(*args, **kwargs)
        except ValueError, e:
            self.logger.warning("ValueError: %s registered while executing method %s with params %s" %
                                (e, self.method, kwargs))
            # sometimes returns this dictionary, sometimes empty response, covered by test "test_empty_result"
            # data = {"error_code":1,"error_msg":"An unknown error occurred"}
            # TODO: perhaps, exception should be raisen here
            return None

    def handle_error_code(self, e, *args, **kwargs):
        if 'An unexpected error has occurred. Please retry your request later' in str(e):
            time.sleep(1)
            return self.repeat_call(*args, **kwargs)
        else:
            return super(FacebookApi, self).handle_error_code(e, *args, **kwargs)

    def handle_error_code_190(self, e, *args, **kwargs):
        self.update_token()
        return self.repeat_call(*args, **kwargs)

    def handle_error_code_17(self, e, *args, **kwargs):
        self.logger.warning("Error 'User request limit reached', try access_token of another user %s with params %s, \
            recursion count: %d" % (self.method, kwargs, self.recursion_count))
        time.sleep(1)
        self.used_access_tokens += [self.api.access_token]
        return self.repeat_call(*args, **kwargs)


def api_call(*args, **kwargs):
    api = FacebookApi()
    return api.call(*args, **kwargs)
