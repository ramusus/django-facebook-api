# -*- coding: utf-8 -*-
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.related import RelatedObject
from django.utils.translation import ugettext as _
from utils import graph
import fields
import dateutil.parser
import logging

log = logging.getLogger('facebook_api.models')

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

    def get_or_create_from_instance(self, instance):

        remote_pk_dict = {}
        for field_name in self.remote_pk:
            remote_pk_dict[field_name] = getattr(instance, field_name)

        try:
            old_instance = self.model.objects.get(**remote_pk_dict)
            instance._substitute(old_instance)
            instance.save()
        except self.model.DoesNotExist:
            instance.save()
            log.debug('Fetch and create new object %s with remote pk %s' % (self.model, remote_pk_dict))

        return instance

    def get_or_create_from_resource(self, resource):

        instance = self.model()
        instance.parse(dict(resource))

        return self.get_or_create_from_instance(instance)

    def fetch(self, *args, **kwargs):
        '''
        Retrieve and save object to local DB
        '''
        response = graph(self.resource_path % args[0], **kwargs)
        instance = self.get_or_create_from_resource(response.toDict())

        return instance

class FacebookGraphModel(models.Model):
    class Meta:
        abstract = True

    remote_pk_field = 'id'

    objects = models.Manager()

    def __init__(self, *args, **kwargs):
        super(FacebookGraphModel, self).__init__(*args, **kwargs)

        # different lists for saving related objects
        self._external_links_post_save = []
        self._foreignkeys_post_save = []
        self._external_links_to_add = []

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
                    value = dateutil.parser.parse(value)#.replace(tzinfo=None)

                elif isinstance(field, (models.OneToOneField, models.ForeignKey)) and value:
                    rel_instance = field.rel.to()
                    rel_instance.parse(dict(value))
                    value = rel_instance
                    if isinstance(field, models.ForeignKey):
                        self._foreignkeys_post_save += [(key, rel_instance)]

                elif isinstance(field, (fields.CommaSeparatedCharField, models.CommaSeparatedIntegerField)) and isinstance(value, list):
                    value = ','.join([unicode(v) for v in value])

                elif isinstance(field, (models.CharField, models.TextField)) and value:
                    if isinstance(value, str):
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

        for field, instance in self._external_links_to_add:
            # if there is already connected instances, then continue, because it's hard to check for duplicates
            if getattr(self, field).count():
                continue
            getattr(self, field).add(instance)
        self._external_links_to_add = []

class FacebookGraphIDModel(FacebookGraphModel):
    class Meta:
        abstract = True

    graph_id = models.CharField(u'ID', max_length=100, help_text=_('Unique graph ID'), unique=True)

    def get_url(self):
        return 'http://facebook.com/%s' % self.graph_id