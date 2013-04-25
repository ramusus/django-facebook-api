# -*- coding: utf-8 -*-
from django.test import TestCase
from facebook_api.utils import graph

class FacebookApiTest(TestCase):

    def test_request(self):

        response = graph('zuck')
        self.assertEqual(response.id, '4')
        self.assertEqual(response.last_name, 'Zuckerberg')
        self.assertEqual(response.first_name, 'Mark')
        self.assertEqual(response.gender, 'male')

    def test_empty_result(self):

        result = graph('8576093908/posts', **{'limit': 1000, 'until': 1345661805, 'offset': 0})
        if result is not None:
            self.assertEqual(result.error_code, 1)