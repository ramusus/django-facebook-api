Django Facebook Graph API
=========================

[![PyPI version](https://badge.fury.io/py/django-facebook-api.png)](http://badge.fury.io/py/django-facebook-api) [![Build Status](https://travis-ci.org/ramusus/django-facebook-api.png?branch=master)](https://travis-ci.org/ramusus/django-facebook-api) [![Coverage Status](https://coveralls.io/repos/ramusus/django-facebook-api/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-facebook-api)

Application for interacting with Facebook Graph API objects using Django model interface

Installation
------------

    pip install django-facebook-api

Add into `settings.py` lines:

    INSTALLED_APPS = (
        ...
        'oauth_tokens',
        'facebook-api',
    )

    # oauth-tokens settings
    OAUTH_TOKENS_HISTORY = True                                        # to keep in DB expired access tokens
    OAUTH_TOKENS_FACEBOOK_CLIENT_ID = ''                               # application ID
    OAUTH_TOKENS_FACEBOOK_CLIENT_SECRET = ''                           # application secret key
    OAUTH_TOKENS_FACEBOOK_SCOPE = ['offline_access']                   # application scopes
    OAUTH_TOKENS_FACEBOOK_USERNAME = ''                                # user login
    OAUTH_TOKENS_FACEBOOK_PASSWORD = ''                                # user password

Usage examples
--------------

### Simple API Graph request

    >>> from facebook_api.api import api_call
    >>> api_call('4')
    {u'first_name': u'Mark',
     u'id': u'4',
     u'last_name': u'Zuckerberg',
     u'link': u'https://www.facebook.com/app_scoped_user_id/10101334100533631/',
     u'name': u'Mark Zuckerberg',
     u'updated_time': u'2015-09-29T14:42:17+0000'}

    >>> api_call('4', fields='id,name')
    {u'id': u'4', u'name': u'Mark Zuckerberg'}

Licensing
---------

This library uses the [Apache License, version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html). 
Please see the library's individual files for more information.
