# -*- coding: utf-8 -*-
import sys

from django.conf import settings
from facebook import GraphAPI, GraphAPIError as FacebookError
from oauth_tokens.api import ApiAbstractBase, Singleton
from oauth_tokens.models import AccessToken

__all__ = ['api_call', 'FacebookError']


@property
def code(self):
    try:
        return self.result['error']['code']
    except (KeyError, TypeError):
        return self.type


FacebookError.code = code


class FacebookApi(ApiAbstractBase):
    __metaclass__ = Singleton

    provider = 'facebook'
    error_class = FacebookError
    sleep_repeat_error_messages = ['An unexpected error has occurred. Please retry your request later']

    def call(self, method, methods_access_tag=None, *args, **kwargs):
        response = super(FacebookApi, self).call(method, methods_access_tag=methods_access_tag, *args, **kwargs)

        # TODO: check if its heritage of previous api lib pyfacegraph
        if getattr(response, 'error_code', None):
            error = "Error %s: %s returned while executing method %s with params %s" % (
                response.error_code, response.error_msg, self.method, kwargs)
            self.logger.error(error)
            if self.recursion_count >= 3:
                raise Exception(error)
            return self.sleep_repeat_call(*args, **kwargs)

        return response

    def get_consistent_token(self):
        return getattr(settings, 'FACEBOOK_API_ACCESS_TOKEN', None)

    def get_tokens(self, **kwargs):
        return AccessToken.objects.filter_active_tokens_of_provider(self.provider, **kwargs)

    def get_api(self, token):
        return GraphAPI(access_token=token, version='2.3')

    def get_api_response(self, *args, **kwargs):
        return self.api.get_object(self.method, *args, **kwargs)

    def handle_error_code_1(self, e, *args, **kwargs):
        if 'limit' in kwargs:
            self.logger.warning("Error 'An unknown error has occurred.', decrease limit. Method %s with params %s, "
                                "recursion count: %d" % (self.method, kwargs, self.recursion_count))
            kwargs['limit'] /= 2
            return self.repeat_call(*args, **kwargs)
        else:
            return self.log_and_raise(e, *args, **kwargs)

    def handle_error_code_4(self, e, *args, **kwargs):
        self.logger.warning("Error 'Application request limit reached', wait for 600 secs. Method %s with params %s, "
                            "recursion count: %d" % (self.method, kwargs, self.recursion_count))
        return self.sleep_repeat_call(seconds=600, *args, **kwargs)

    def handle_error_code_12(self, e, *args, **kwargs):
        return self.log_and_raise(e, *args, **kwargs)

    def handle_error_code_17(self, e, *args, **kwargs):
        self.logger.warning("Error 'User request limit reached', try access_token of another user. Method %s with "
                            "params %s, recursion count: %d" % (self.method, kwargs, self.recursion_count))
        self.used_access_tokens += [self.api.access_token]
        return self.sleep_repeat_call(*args, **kwargs)

    def handle_error_code_100(self, e, *args, **kwargs):
        self.logger.error("Error 'Unsupported get request. Please read the Graph API documentation'. Method %s with "
                          "params %s, access_token: %s, recursion count: %d" % (
            self.method, kwargs, self.api.access_token, self.recursion_count))
        self.used_access_tokens += [self.api.access_token]
        return self.repeat_call(*args, **kwargs)

    def handle_error_code_190(self, e, *args, **kwargs):
        self.update_token()
        return self.repeat_call(*args, **kwargs)


def api_call(*args, **kwargs):
    api = FacebookApi()
    return api.call(*args, **kwargs)
