# -*- coding: utf-8 -*-
import logging

from dateutil.parser import parse as datetime_parse
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.six import string_types
from facebook_users.models import User
from m2m_history.fields import ManyToManyHistoryField

from .api import api_call
from .decorators import fetch_all, atomic
from .fields import JSONField
from .utils import get_or_create_from_small_resource, UnknownResourceType

log = logging.getLogger('facebook_api')


class OwnerableModelMixin(models.Model):

    owner_content_type = models.ForeignKey(
        ContentType, null=True, related_name='content_type_owners_%(app_label)s_%(class)ss')
    owner_id = models.BigIntegerField(null=True, db_index=True)
    owner = generic.GenericForeignKey('owner_content_type', 'owner_id')

    class Meta:
        abstract = True


class AuthorableModelMixin(models.Model):

    # object containing the name and Facebook id of the user who posted the message
    author_json = JSONField(null=True, help_text='Information about the user who posted the message')

    author_content_type = models.ForeignKey(
        ContentType, null=True, related_name='content_type_authors_%(app_label)s_%(class)ss')
    author_id = models.BigIntegerField(null=True, db_index=True)
    author = generic.GenericForeignKey('author_content_type', 'author_id')

    class Meta:
        abstract = True

    def parse(self, response):
        if 'from' in response:
            response['author_json'] = response.pop('from')

        super(AuthorableModelMixin, self).parse(response)

        if self.author is None and self.author_json:
            self.author = get_or_create_from_small_resource(self.author_json)


class ActionableModelMixin(models.Model):

    actions_count = models.PositiveIntegerField(null=True, help_text='The number of total actions with this item')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.actions_count = sum([getattr(self, field, None) or 0
                                  for field in ['likes_count', 'shares_count', 'comments_count']])
        super(ActionableModelMixin, self).save(*args, **kwargs)


class LikableModelMixin(models.Model):

    likes_users = ManyToManyHistoryField(User, related_name='like_%(class)ss')
    likes_count = models.PositiveIntegerField(null=True, help_text='The number of likes of this item')

    class Meta:
        abstract = True

    def parse(self, response):
        if 'like_count' in response:
            response['likes_count'] = response.pop('like_count')
        super(LikableModelMixin, self).parse(response)

    def update_count_and_get_like_users(self, instances, *args, **kwargs):
        self.likes_users = instances
        self.likes_count = instances.count()
        self.save()
        return instances

    @atomic
    @fetch_all(return_all=update_count_and_get_like_users, paging_next_arg_name='after')
    def fetch_likes(self, limit=1000, **kwargs):
        '''
        Retrieve and save all likes of post
        '''
        ids = []
        response = api_call('%s/likes' % self.graph_id, limit=limit, **kwargs)
        if response:
            log.debug('response objects count=%s, limit=%s, after=%s' %
                      (len(response.data), limit, kwargs.get('after')))
            for resource in response.data:
                try:
                    user = get_or_create_from_small_resource(resource)
                    ids += [user.pk]
                except UnknownResourceType:
                    continue

        return User.objects.filter(pk__in=ids), response


class ShareableModelMixin(models.Model):

    shares_users = ManyToManyHistoryField(User, related_name='shares_%(class)ss')
    shares_count = models.PositiveIntegerField(null=True, help_text='The number of shares of this item')

    class Meta:
        abstract = True

    def update_count_and_get_shares_users(self, instances, *args, **kwargs):
#        self.shares_users = instances
        # becouse here are not all shares: "Some posts may not appear here because of their privacy settings."
        if self.shares_count is None:
            self.shares_count = instances.count()
            self.save()
        return instances

    @atomic
    @fetch_all(return_all=update_count_and_get_shares_users, paging_next_arg_name='after')
    def fetch_shares(self, limit=1000, **kwargs):
        '''
        Retrieve and save all shares of post
        '''
        from facebook_api.models import MASTER_DATABASE  # here, becouse cycling import

        ids = []

        graph_id = self.graph_id
        if isinstance(graph_id, string_types):
            graph_id = graph_id.split('_').pop()

        response = api_call('%s/sharedposts' % graph_id, **kwargs)
        if response:
            timestamps = dict(
                [(int(post['from']['id']), datetime_parse(post['created_time'])) for post in response.data])
            ids_new = timestamps.keys()
            # becouse we should use local pk, instead of remote, remove it after pk -> graph_id
            ids_current = map(int, User.objects.filter(pk__in=self.shares_users.get_query_set(
                only_pk=True).using(MASTER_DATABASE).exclude(time_from=None)).values_list('graph_id', flat=True))
            ids_add = set(ids_new).difference(set(ids_current))
            ids_add_pairs = []
            ids_remove = set(ids_current).difference(set(ids_new))

            log.debug('response objects count=%s, limit=%s, after=%s' %
                      (len(response.data), limit, kwargs.get('after')))
            for post in response.data:
                graph_id = int(post['from']['id'])
                if sorted(post['from'].keys()) == ['id', 'name']:
                    try:
                        user = get_or_create_from_small_resource(post['from'])
                        ids += [user.pk]
                        # this id in add list and still not in add_pairs (sometimes in response are duplicates)
                        if graph_id in ids_add and graph_id not in map(lambda i: i[0], ids_add_pairs):
                            # becouse we should use local pk, instead of remote
                            ids_add_pairs += [(graph_id, user.pk)]
                    except UnknownResourceType:
                        continue

            m2m_model = self.shares_users.through
            # '(album|post)_id'
            field_name = [f.attname for f in m2m_model._meta.local_fields
                          if isinstance(f, models.ForeignKey) and f.name != 'user'][0]

            # remove old shares without time_from
            self.shares_users.get_query_set_through().filter(time_from=None).delete()

            # in case some ids_add already left
            self.shares_users.get_query_set_through().filter(
                **{field_name: self.pk, 'user_id__in': map(lambda i: i[1], ids_add_pairs)}).delete()

            # add new shares with specified `time_from` value
            get_share_date = lambda id: timestamps[id] if id in timestamps else self.created_time
            m2m_model.objects.bulk_create([m2m_model(
                **{field_name: self.pk, 'user_id': pk, 'time_from': get_share_date(graph_id)}) for graph_id, pk in ids_add_pairs])

        return User.objects.filter(pk__in=ids), response
