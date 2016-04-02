# -*- coding: utf-8 -*-
'''
Copyright 2011-2015 ramusus
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from social_api.tests import SocialApiTestCase

from .api import api_call, FacebookApi

TOKEN = 'CAAGPdaGocPIBANyHk4GO3HJYhNalf78scXf5CprODAIYELOjW7DBkYG6uV5hip71fEv19jZBrQdN1nUhsrcvghxKtuxEIMgPqr4XUQMnvx8SApZBU3C6ccyknaNunFqgMbZB0VQFaYukP6NEGDfvcZBbRk6DdxnCZCO7z20KkBd3ZB5Rusgskxx0S2ARZCfN8KZAzgAq3F3KSgZDZD'  # noqa


class FacebookApiTestCase(SocialApiTestCase):
    provider = 'facebook'
    token = TOKEN


class FacebookApiTest(FacebookApiTestCase):

    def test_api_instance_singleton(self):
        self.assertEqual(id(FacebookApi()), id(FacebookApi()))

    def test_request(self):
        response = api_call('me')
        self.assertEqual(response['id'], '100005428301237')
        self.assertEqual(response['last_name'], 'Djangov')
        self.assertEqual(response['first_name'], 'Travis')
        self.assertEqual(response['gender'], 'male')

    # def test_empty_result(self):
    #     # strange error sometimes appear
    #     with self.assertRaises(Exception):
    #         api_call('135161613191462/posts', **{'limit': 250, 'since': 1416258000})
