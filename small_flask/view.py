# from six import with_metaclass

from .globals import request


http_method_funcs = frozenset(
    ["get", "post", "head", "options", "delete", "put", "trace", "patch"]
)


def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instantiation that replaces
    # itself with the actual metaclass.
    class metaclass(type):
        def __new__(metacls, name, this_bases, d):
            return meta(name, bases, d)

    return type.__new__(metaclass, "temporary_class", (), {})

# class MethodView:
#     # operate on the instance
#     def __init__(self):
#         self.method_funcs = dict()
#         for method in http_method_funcs:
#             self.method_funcs[method.lower()] = None
#
#     def add_method(self, method, func):
#         self.method_funcs[method.lower()] = func
#
#     def register_method(self, method):
#         # decorator to register func to a method
#         def decorator(f):
#             self.add_method(method, f)
#             return f
#         return decorator
#
#     def __call__(self, **view_args):
#         # get request method from request obj
#         return self.method_funcs[request.method](**view_args)


# def MetaFunction(classname, superclasses, attributedict):
#     if 'methods' not in attributedict:
#         methods = set()
#         for method in http_method_funcs:
#             if method in attributedict:
#                 methods.add(method)
#         attributedict['methods'] = methods
#     return type(classname, superclasses, attributedict)


class MethodViewType(type):
    """Metaclass for :class:`MethodView` that determines what methods the view
    defines.
    """

    def __init__(cls, name, bases, d):
        super(MethodViewType, cls).__init__(name, bases, d)

        if "methods" not in d:
            methods = set()

            for base in bases:
                if getattr(base, "methods", None):
                    methods.update(base.methods)

            for key in http_method_funcs:
                if hasattr(cls, key):
                    methods.add(key.upper())

            if methods:
                cls.methods = methods


class MethodView(with_metaclass(MethodViewType, object)):
    decorators = ()
    methods = None

    def __init__(self, *class_args, **class_kwargs):
        pass

    def dispatch_request(self, **view_args):
        method = request.method
        method_func = getattr(self, method.lower(), None)
        if method_func is None and method.lower() == 'head':
            method_func = getattr(self, 'get', None)
        if method_func is None:
            from werkzeug.exceptions import MethodNotAllowed
            raise MethodNotAllowed
        return method_func(**view_args)

    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        def func(**view_args):
            return cls.dispatch_request(cls(*class_args, **class_kwargs), **view_args)
        for decorator in cls.decorators:
            decorator(func)
        func.__name__ = name
        func.methods = cls.methods
        return func