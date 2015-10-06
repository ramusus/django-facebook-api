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
from django.core.exceptions import ImproperlyConfigured


def get_improperly_configured_field(app_name, decorate_property=False):
    def field(self):
        raise ImproperlyConfigured("Application '%s' not in INSTALLED_APPS" % app_name)
    if decorate_property:
        field = property(field)
    return field


class UnknownResourceType(Exception):
    pass


def get_or_create_from_small_resource(resource):
    '''
    Return instance of right type based on dictionary resource from Facebook API Graph
    '''
    from facebook_applications.models import Application
    from facebook_pages.models import Page
    from facebook_users.models import User

    keys = sorted(resource.keys())
    defaults = dict(resource)
    del defaults['id']
    if keys == ['category', 'id', 'name'] or keys == ['category', 'category_list', 'id', 'name']:
        # resource is a page
        if 'category_list' in defaults:
            del defaults['category_list']
        return Page.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name', 'namespace']:
        # resource is a application
        return Application.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name'] or keys == ['id']:
        # resource is a user
        return User.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    else:
        raise UnknownResourceType("Strange structure of resource: %s" % resource)
