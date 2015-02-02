# -*- coding: utf-8 -*-
from datetime import datetime
import logging
import re

import dateutil.parser
from django.conf import settings
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils.translation import ugettext as _

from . import fields
from .api import api_call
from .decorators import atomic
from .signals import facebook_api_post_fetch

log = logging.getLogger('facebook_api.models')


MASTER_DATABASE = getattr(settings, 'FACEBOOK_API_MASTER_DATABASE', 'default')


class FacebookContentError(Exception):
    pass


class FacebookGraphManager(models.Manager):

    '''
    Facebook Graph Manager for RESTful CRUD operations
    '''

    def __init__(self, remote_pk=None, resource_path='%s', *args, **kwargs):
        if '%s' not in resource_path:
            raise ValueError('Argument resource_path must contains %s character')

        self.resource_path = resource_path
        self.remote_pk = remote_pk or ('graph_id',)
        if not isinstance(self.remote_pk, tuple):
            self.remote_pk = (self.remote_pk,)

        super(FacebookGraphManager, self).__init__(*args, **kwargs)

    def get_by_url(self, url):
        '''
        Return object by url
        '''
        m = re.findall(r'(?:https?://)?(?:www\.)?facebook\.com/(.+)/?', url)
        if not len(m):
            raise ValueError("Url should be started with http://facebook.com/")

        return self.get_by_slug(m[0])

    def get_by_slug(self, slug):
        '''
        Return object by slug
        '''
        if 'pages' in slug:
            parts = slug.split('/')
            if len(parts) == 3:
                slug = parts[2]

        return self.get(slug)

    def get_or_create_from_instance(self, instance):

        old_instance = None
        remote_pk_dict = {}
        for field_name in self.remote_pk:
            remote_pk_dict[field_name] = getattr(instance, field_name)

        try:
            old_instance = self.model.objects.using(MASTER_DATABASE).get(**remote_pk_dict)
            instance._substitute(old_instance)
            instance.save()
        except self.model.DoesNotExist:
            instance.save()
            log.debug('Fetch and create new object %s with remote pk %s' % (self.model, remote_pk_dict))

        facebook_api_post_fetch.send(sender=instance.__class__, instance=instance, created=(not old_instance))
        return instance

    def get_or_create_from_resource(self, response, extra_fields=None):
        instance = self.parse_response_dict(response, extra_fields)
        return self.get_or_create_from_instance(instance)

    @atomic
    def fetch(self, *args, **kwargs):
        '''
        Retrieve and save object to local DB
        '''
        result = self.get(*args, **kwargs)
        if isinstance(result, list):
            return [self.get_or_create_from_instance(instance) for instance in result]
        else:
            return self.get_or_create_from_instance(result)

    def get(self, *args, **kwargs):
        '''
        Retrieve objects from remote server
        '''
        extra_fields = kwargs.pop('extra_fields', {})
#        extra_fields['fetched'] = datetime.now()

        response = api_call(self.resource_path % args[0], **kwargs)

        return self.parse_response(response.toDict(), extra_fields)

    def parse_response(self, response, extra_fields=None):
        if isinstance(response, (list, tuple)):
            return self.parse_response_list(response, extra_fields)
        elif isinstance(response, dict):
            return self.parse_response_dict(response, extra_fields)
        else:
            raise FacebookContentError('Facebook response should be list or dict, not %s' % response)

    def parse_response_dict(self, resource, extra_fields=None):

        instance = self.model()
        # important to do it before calling parse method
        if extra_fields:
            instance.__dict__.update(extra_fields)
        instance.parse(resource)

        return instance

    def parse_response_list(self, response_list, extra_fields=None):

        instances = []
        for resource in response_list:

            try:
                resource = dict(resource)
            except (TypeError, ValueError), e:
                log.error("Resource %s is not dictionary" % resource)
                raise e

            instance = self.parse_response_dict(resource, extra_fields)
            instances += [instance]

        return instances


class FacebookGraphModel(models.Model):

    class Meta:
        abstract = True

    remote_pk_field = 'id'

#    fetched = models.DateTimeField(u'Обновлено', null=True, blank=True)

    objects = models.Manager()

    @property
    def slug(self):
        raise NotImplementedError("Property %s.slug should be specified" % self.__class__.__name__)

    def get_url(self):
        return 'http://facebook.com/%s' % self.slug

    def __init__(self, *args, **kwargs):
        super(FacebookGraphModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_post_save = []
        self._external_links_to_add = {}

    def _substitute(self, old_instance):
        '''
        Substitute new user with old one while updating in method Manager.get_or_create_from_instance()
        Can be overrided in child models
        '''
        self.id = old_instance.id

    def parse(self, response):
        '''
        Parse API response and define fields with values
        '''
        for key, value in response.items():

            if key == self.remote_pk_field:
                key = 'graph_id'

            try:
                field, model, direct, m2m = self._meta.get_field_by_name(key)
            except FieldDoesNotExist:
                log.debug('Field with name "%s" doesn\'t exist in the model %s' % (key, type(self)))
                continue

            if isinstance(field, RelatedObject) and value:
                for item in value:
                    rel_instance = field.model()
                    rel_instance.parse(dict(item))
                    self._external_links_post_save += [(field.field.name, rel_instance)]
            else:
                if isinstance(field, models.DateTimeField) and value:
                    value = dateutil.parser.parse(value)  # .replace(tzinfo=None)

                elif isinstance(field, (models.IntegerField)) and value:
                    try:
                        value = int(value)
                    except:
                        pass

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to()
                    rel_instance.parse(dict(value))
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_post_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField, models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, (str, unicode)):
                        value = value.strip()

                setattr(self, key, value)

    def save(self, *args, **kwargs):
        '''
        Save all related instances before or after current instance
        '''
        for field, instance in self._foreignkeys_post_save:
            instance = instance.__class__.remote.get_or_create_from_instance(instance)
            instance.save()
            setattr(self, field, instance)
        self._foreignkeys_post_save = []

        super(FacebookGraphModel, self).save(*args, **kwargs)

        for field, instance in self._external_links_post_save:
            # set foreignkey to the main instance
            setattr(instance, field, self)
            instance.__class__.remote.get_or_create_from_instance(instance)
        self._external_links_post_save = []

        # process self._external_links_to_add
        for field, instances in self._external_links_to_add.items():
            getattr(self, field).all().delete()
            for instance in instances:
                getattr(self, field).add(instance)
        self._external_links_to_add = {}


class FacebookGraphIDModel(FacebookGraphModel):

    graph_id = models.CharField(u'ID', max_length=70, help_text=_('Unique graph ID'), unique=True)

    class Meta:
        abstract = True

    @property
    def slug(self):
        return self.graph_id


class FacebookGraphPKModelMixin:

    @property
    def slug(self):
        return self.graph_id

    @property
    def id(self):
        return self.pk

    def _substitute(self, old_instance):
        return


class FacebookGraphStrPKModel(FacebookGraphPKModelMixin, FacebookGraphModel):

    graph_id = models.CharField(u'ID', primary_key=True, max_length=70, help_text=_('Unique graph ID'))

    class Meta:
        abstract = True


class FacebookGraphIntPKModel(FacebookGraphPKModelMixin, FacebookGraphModel):

    graph_id = models.BigIntegerField(u'ID', primary_key=True, help_text=_('Unique graph ID'))

    class Meta:
        abstract = True
