# -*- coding: utf-8 -*-
from django.contrib import admin

class FacebookModelAdmin(admin.ModelAdmin):

#    def fb_link(self, obj):
#        return u'<a href="%s" target="_blank">%s</a>' % (obj.get_url(), getattr(obj, 'slug', 'vk.com'))
#    fb_link.short_description = u'vk.com'
#    fb_link.allow_tags = True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields if field.name not in ['id']]
        return []