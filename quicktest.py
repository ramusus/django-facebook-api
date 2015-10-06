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

'''
QuickDjangoTest module for testing in Travis CI https://travis-ci.org
Change log:
 * 2014-10-24 updated for compatibility with Django 1.7
 * 2014-11-03 different databases support: sqlite3, mysql, postgres
 * 2014-12-31 pep8, python 3 compatibility
 * 2015-10-06 apache 2 license
'''

import argparse
import os
import sys

from django.conf import settings


class QuickDjangoTest(object):

    """
    A quick way to run the Django test suite without a fully-configured project.

    Example usage:

        >>> QuickDjangoTest('app1', 'app2')

    Based on a script published by Lukasz Dziedzia at:
    http://stackoverflow.com/questions/3841725/how-to-launch-tests-for-django-reusable-app
    """
    DIRNAME = os.path.dirname(__file__)
    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
    )

    def __init__(self, *args, **kwargs):
        self.apps = args

        # Get the version of the test suite
        self.version = self.get_test_version()

        # Call the appropriate one
        if self.version == '1.7':
            self._tests_1_7()
        elif self.version == '1.2':
            self._tests_1_2()
        else:
            self._tests_old()

    def get_test_version(self):
        """
        Figure out which version of Django's test suite we have to play with.
        """
        from django import VERSION
        if VERSION[0] == 1 and VERSION[1] >= 7:
            return '1.7'
        elif VERSION[0] == 1 and VERSION[1] >= 2:
            return '1.2'
        else:
            return

    def get_database(self):
        test_db = os.environ.get('DB', 'sqlite')
        if test_db == 'mysql':
            database = {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'django',
                'USER': 'root',
            }
        elif test_db == 'postgres':
            database = {
                'ENGINE': 'django.db.backends.postgresql_psycopg2',
                'USER': 'postgres',
                'NAME': 'django',
                'OPTIONS': {
                    'autocommit': True,
                }
            }
        else:
            database = {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(self.DIRNAME, 'database.db'),
                'USER': '',
                'PASSWORD': '',
                'HOST': '',
                'PORT': '',
            }
        return {'default': database}

    def get_custom_settings(self):
        try:
            import settings_test
            settings_test = dict([(k, v) for k, v in settings_test.__dict__.items() if k[0] != '_'])
            INSTALLED_APPS = settings_test.pop('INSTALLED_APPS', [])
        except ImportError:
            settings_test = {}
            INSTALLED_APPS = []

        return INSTALLED_APPS, settings_test

    def _tests_old(self):
        """
        Fire up the Django test suite from before version 1.2
        """
        INSTALLED_APPS, settings_test = self.get_custom_settings()

        settings.configure(DEBUG=True,
                           DATABASE_ENGINE='sqlite3',
                           DATABASE_NAME=os.path.join(self.DIRNAME, 'database.db'),
                           INSTALLED_APPS=self.INSTALLED_APPS + INSTALLED_APPS + self.apps,
                           **settings_test
                           )
        from django.test.simple import run_tests
        failures = run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)

    def _tests_1_2(self):
        """
        Fire up the Django test suite developed for version 1.2 and up
        """
        INSTALLED_APPS, settings_test = self.get_custom_settings()

        settings.configure(
            DEBUG=True,
            DATABASES=self.get_database(),
            INSTALLED_APPS=self.INSTALLED_APPS + INSTALLED_APPS + self.apps,
            **settings_test
        )

        from django.test.simple import DjangoTestSuiteRunner
        failures = DjangoTestSuiteRunner().run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)

    def _tests_1_7(self):
        """
        Fire up the Django test suite developed for version 1.7 and up
        """
        INSTALLED_APPS, settings_test = self.get_custom_settings()

        settings.configure(
            DEBUG=True,
            DATABASES=self.get_database(),
            MIDDLEWARE_CLASSES=('django.middleware.common.CommonMiddleware',
                                'django.middleware.csrf.CsrfViewMiddleware'),
            INSTALLED_APPS = self.INSTALLED_APPS + INSTALLED_APPS + self.apps,
            **settings_test
        )

        from django.test.simple import DjangoTestSuiteRunner
        import django
        django.setup()
        failures = DjangoTestSuiteRunner().run_tests(self.apps, verbosity=1)
        if failures:
            sys.exit(failures)


if __name__ == '__main__':
    """
    What do when the user hits this file from the shell.

    Example usage:

        $ python quicktest.py app1 app2

    """
    parser = argparse.ArgumentParser(
        usage="[args]",
        description="Run Django tests on the provided applications."
    )
    parser.add_argument('apps', nargs='+', type=str)
    args = parser.parse_args()
    QuickDjangoTest(*args.apps)
