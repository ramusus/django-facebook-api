# -*- coding: utf-8 -*-
#
# Copyright 2011-2015 ramusus
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup
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
