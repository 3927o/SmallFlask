from werkzeug.local import Local, LocalProxy, LocalStack
from .wrappers import Request


class Global(dict):
    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("'Global' instance g has no attribute '{}'".format(name))


local = Local()
setattr(local, "request", None)
# getattr(local, "request").__class__ = Request
setattr(local, "g", None)
setattr(local, "session", None)
setattr(local, "current_app", None)

g = local('g')
request = local("request")
session = local("session")
current_app = local("current_app")