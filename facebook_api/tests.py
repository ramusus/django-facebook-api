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
from django.test import TestCase

from .api import api_call, FacebookApi


class FacebookApiTest(TestCase):

    def test_api_instance_singleton(self):

        self.assertEqual(id(FacebookApi()), id(FacebookApi()))

    def test_request(self):

        response = api_call('zuck')
        self.assertEqual(response.id, '4')
        self.assertEqual(response.last_name, 'Zuckerberg')
        self.assertEqual(response.first_name, 'Mark')
        self.assertEqual(response.gender, 'male')

    def test_empty_result(self):

        # strange error sometimes appear
        with self.assertRaises(Exception):
            api_call('135161613191462/posts', **{'limit': 250, 'since': 1416258000})
