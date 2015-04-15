# -*- coding: utf-8 -*-
from django.conf import settings
from facebook import GraphAPI, GraphAPIError as FacebookError
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

    def handle_error_code(self, e, *args, **kwargs):
        e.code = e.type
        if 'An unexpected error has occurred. Please retry your request later' in str(e) \
                or 'Unsupported get request. Please read the Graph API documentation' in str(e):
            return self.sleep_repeat_call(*args, **kwargs)
        else:
            return super(FacebookApi, self).handle_error_code(e, *args, **kwargs)

    def handle_error_code_4(self, e, *args, **kwargs):
        self.logger.warning("Error 'Application request limit reached', wait for 600 secs. Method %s with params %s, "
                            "recursion count: %d" % (self.method, kwargs, self.recursion_count))
        return self.sleep_repeat_call(seconds=600, *args, **kwargs)

    def handle_error_code_12(self, e, *args, **kwargs):
        self.logger.error("Error '%s'. Method %s with params %s, recursion count: %d" % (
            e, self.method, kwargs, self.recursion_count))
        raise e

    def handle_error_code_17(self, e, *args, **kwargs):
        self.logger.warning("Error 'User request limit reached', try access_token of another user. Method %s with "
                            "params %s, recursion count: %d" % (self.method, kwargs, self.recursion_count))
        self.used_access_tokens += [self.api.access_token]
        return self.sleep_repeat_call(*args, **kwargs)

    def handle_error_code_190(self, e, *args, **kwargs):
        self.update_token()
        return self.repeat_call(*args, **kwargs)

def api_call(*args, **kwargs):
    api = FacebookApi()
    return api.call(*args, **kwargs)
