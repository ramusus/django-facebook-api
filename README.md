# Django Facebook Graph API

[![PyPI version](https://badge.fury.io/py/django-facebook-api.png)](http://badge.fury.io/py/django-facebook-api) [![Build Status](https://travis-ci.org/ramusus/django-facebook-api.png?branch=master)](https://travis-ci.org/ramusus/django-facebook-api) [![Coverage Status](https://coveralls.io/repos/ramusus/django-facebook-api/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-facebook-api)

Application for interacting with Facebook Graph API objects using Django model interface

## Installation

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

## Usage examples

### Simple API Graph request

    >>> from facebook_api.utils import graph
    >>> graph('zuck')
    Node(<Graph(u'https://graph.facebook.com/zuck') at 0xb1cbfac>,
         {'first_name': 'Mark',
          'gender': 'male',
          'id': '4',
          'last_name': 'Zuckerberg',
          'link': 'http://www.facebook.com/zuck',
          'locale': 'en_US',
          'name': 'Mark Zuckerberg',
          'updated_time': '2013-03-13T20:36:43+0000',
          'username': 'zuck'})

    >>> graph('zuck', fields='id,name')
    Node(<Graph(u'https://graph.facebook.com/zuck') at 0xb1d2a8c>,
         {'id': '4', 'name': 'Mark Zuckerberg'})