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

    try:
        return Page.objects.get(graph_id=resource['id'])
    except Page.DoesNotExist:
        try:
            return User.objects.get(graph_id=resource['id'])
        except User.DoesNotExist:
            try:
                return Application.objects.get(graph_id=resource['id'])
            except Application.DoesNotExist:
                pass

    keys = sorted(resource.keys())
    defaults = dict(resource)
    del defaults['id']
    if keys == ['category', 'id', 'name'] or keys == ['category', 'category_list', 'id', 'name']:
        # resource is a page
        if 'category_list' in defaults:
            del defaults['category_list']
        return Page.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name']:
        # resource is a user
        return User.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    elif keys == ['id', 'name', 'namespace']:
        # resource is a application
        return Application.objects.get_or_create(graph_id=resource['id'], defaults=defaults)[0]
    else:
        raise UnknownResourceType("Resource with strange keys: %s" % keys)
