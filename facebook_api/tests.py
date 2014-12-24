# -*- coding: utf-8 -*-
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
