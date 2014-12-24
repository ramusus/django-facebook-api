import re

from setuptools import setup, find_packages
setup(
    name='django-facebook-api',
    version=__import__('facebook_api').__version__,
    description='Django implementation for Facebook Graph API',
    long_description=open('README.md').read(),
    author='ramusus',
    author_email='ramusus@gmail.com',
    url='https://github.com/ramusus/django-facebook-api',
    download_url='http://pypi.python.org/pypi/django-facebook-api',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,  # because we're including media that Django needs
    dependency_links=[
        'https://github.com/iplatform/pyFaceGraph/tarball/master#egg=pyfacegraph-0.0.36',
    ],
    install_requires=[
        'django',
        'django-annoying',
        'django-oauth-tokens>=0.4.5',
        'pyfacegraph>=0.0.36',
        'python-dateutil>=1.5',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
