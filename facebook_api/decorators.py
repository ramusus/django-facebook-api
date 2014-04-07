# -*- coding: utf-8 -*-
from django.utils.functional import wraps
from django.db.models.query import QuerySet
from bunch import Bunch

def opt_arguments(func):
    '''
    Meta-decorator for ablity use decorators with optional arguments
    from here http://www.ellipsix.net/blog/2010/08/more-python-voodoo-optional-argument-decorators.html
    '''
    def meta_wrapper(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            # No arguments, this is the decorator
            # Set default values for the arguments
            return func(args[0])
        else:
            def meta_func(inner_func):
                return func(inner_func, *args, **kwargs)
            return meta_func
    return meta_wrapper

@opt_arguments
def fetch_all(func, return_all=None):
    """
    Class method decorator for fetching all items. Add parameter `all=False` for decored method.
    If `all` is True, method runs as many times as it returns any results.
    Decorator receive parameters:
      * callback method `return_all`. It's called with the same parameters
        as decored method after all itmes are fetched.
    Usage:

        @fetch_all(return_all=lambda self,instance,*a,**k: instance.items.all())
        def fetch_something(self, ..., *kwargs):
        ....
    """
    def wrapper(self, all=False, instances_all=None, *args, **kwargs):

        instances = func(self, *args, **kwargs)
        if len(instances) == 2 and isinstance(instances[1], Bunch):
            instances, response = instances

        if all:
            if isinstance(instances, QuerySet):
                if not instances_all:
                    instances_all = QuerySet().none()
                instances_all |= instances
            elif isinstance(instances, list):
                if not instances_all:
                    instances_all = []
                instances_all += instances
            else:
                raise ValueError("Wrong type of response from func %s. It should be QuerySet or list, not a %s" % (func, type(instances)))

            if getattr(response.paging, 'next', None):
                kwargs['after'] = response.paging.cursors.after
                return wrapper(self, all=all, instances_all=instances_all, *args, **kwargs)

            if return_all:
                return return_all(self, instances_all=instances_all, *args, **kwargs)
            else:
                return instances_all
        else:
            return instances

    return wraps(func)(wrapper)

def opt_generator(func):
    """
    Class method or function decorator makes able to call generator methods as usual methods.
    Usage:

        @method_decorator(opt_generator)
        def some_method(self, ...):
            ...
            for count in some_another_method():
                yield (count, total)

    It's possible to call this method 2 different ways:

        * instance.some_method() - it will return nothing
        * for count, total in instance.some_method(as_generator=True):
            print count, total
    """
    def wrapper(*args, **kwargs):
        as_generator = kwargs.pop('as_generator', False)
        result = func(*args, **kwargs)
        return result if as_generator else list(result)
    return wraps(func)(wrapper)