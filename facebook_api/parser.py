# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import re

from BeautifulSoup import BeautifulSoup
from django.conf import settings
from oauth_tokens.providers.facebook import FacebookAccessToken
import requests


class FacebookParseError(Exception):
    pass


class FacebookParser(object):

    auth_access = None
    content = ''

    def __init__(self, content='', url=None, **kwargs):
        self.content = content

    @property
    def html(self):
        return self.content

    @property
    def content_bs(self):
        return BeautifulSoup(self.html)

    def request(self, authorized=False, *args, **kwargs):
#        kwargs['headers'] = {'Accept-Language':'ru-RU,ru;q=0.8'}

        args = list(args)
        if 'url' in kwargs and 'http' not in kwargs['url']:
            kwargs['url'] = 'https://www.facebook.com' + kwargs['url']

        if authorized:
            if not self.auth_access:
                self.auth_access = FacebookAccessToken().auth_request
            response = self.auth_access.authorized_request(*args, **kwargs)
        else:
            response = getattr(requests, kwargs.pop('method', 'get'))(*args, **kwargs)

        self.content = response.content
