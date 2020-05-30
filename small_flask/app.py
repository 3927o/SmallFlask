import os
import posixpath

from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, default_exceptions
from werkzeug.wrappers import BaseResponse
from werkzeug.datastructures import ImmutableDict
from jinja2 import Environment, FileSystemLoader

from .wrappers import Request, Response
from .globals import request, local, Global, session, g
from .sessions import Session, RedisSessionInterface
from .helpers import url_for, send_from_directory


class Application:

    default_config = {
        "SESSION_TYPE": "redis",
        "SESSION_COOKIE_NAME": "session",
        "SESSION_KEY_PREFIX": "session:",
        "SECRET_KEY": "secret",
        "SESSION_LIFETIME": 60*10,
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": 6379,
        "REDIS_PWD": None
    }

    session_interface_map = ImmutableDict({
        "redis": RedisSessionInterface
    })

    secret_key = 'secret'
    session_lifetime = 60*10

    def __init__(
        self,
        config=None,
        root_path=None,
        static_folder='static',
        template_folder='templates',
        template_loader=None,
        static_url_path='/static'
    ):
        if config is None:
            config = self.default_config
        self.config = ImmutableDict(config)
        for config in self.config:
            setattr(self, config.lower(), self.config[config])

        self.view_functions = dict()
        self.handler_map = dict()
        self.url_map = Map()
        self.before_request_funcs = dict()

        if root_path is None:
            root_path = os.path.dirname(os.path.abspath('<input>'))
        self.root_path = root_path
        self.static_folder = static_folder
        self.template_folder = template_folder
        self.static_url_path = static_url_path

        self.jinja_loader = template_loader
        self.jinja_env = self.create_jinja_env()

        self.session_interface = self.get_interface()

        self.add_url_rule(self.static_url_path+"/<path:filename>", endpoint='static', view_func=self.send_static_file)

    def wsgi_app(self, environ, start_response):

        local.request = Request(environ, self)
        local.current_app = self
        local.g = Global()
        local.session = self.session_interface.open_session(self, request)

        resp = self.full_dispatch_request()
        iterable = resp(environ, start_response)

        return iterable

    def send_static_file(self, filename):
        return send_from_directory(self.static_folder, filename)

    def before_request(self, endpoint=None):
        def decorator(f):
            self.before_request_funcs.setdefault(endpoint, []).append(f)
            return f()

        # 为了让before_request不用加( )而加的傻逼东西，迟早删了
        if type(endpoint) is not str:
            self.before_request_funcs.setdefault(None, []).append(endpoint)

        return decorator

    def add_before_request_func(self, func, endpoint=None):
        self.before_request_funcs.setdefault(endpoint, []).append(func)

    def preprocess_request(self):
        endpoint = request.url_rule.endpoint if request.url_rule is not None else None
        funcs = self.before_request_funcs.get(None, [])
        if endpoint is not None:
            for func in self.before_request_funcs.get(endpoint, ()):
                funcs.append(func)

        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def register_error_handler(self, exc_class_or_code, handler):
        exc_class = _find_exceptions(exc_class_or_code)
        if isinstance(exc_class, Exception):
            raise ValueError("Handler can only be registered for exception classes, not instance")
        self.handler_map[exc_class] = handler

    def route(self, path, **options):

        def decorator(f):
            self.add_url_rule(path, f, **options)
            return f

        return decorator

    def error_handler(self, exc_class):
        def decorator(f):
            self.register_error_handler(exc_class, f)
            return f
        return decorator

    def add_url_rule(self, path, view_func, endpoint=None, methods=None):
        if endpoint is None:
            endpoint = view_func.__name__

        old_func = self.view_functions.get(endpoint, None)
        if old_func is not None and old_func != view_func:
            raise AssertionError(
                "View function mapping is overwriting an "
                "existing endpoint function: %s" % endpoint
             )

        if methods is None:
            methods = getattr(view_func, "methods", None) or ("GET",)

        rule = Rule(path, endpoint=endpoint, methods=methods)
        self.url_map.add(rule)
        self.view_functions[endpoint] = view_func

    # match the commented out MethodView
    # def add_method_view(self, path, method_view, endpoint=None):
    #     if endpoint is None:
    #         endpoint = method_view.__name__
    #
    #     old_view = self.view_functions.get(endpoint, None)
    #     if old_view is not None and old_view != method_view:
    #         raise AssertionError(
    #             "View function mapping is overwriting an "
    #             "existing endpoint function(MethodView): %s" % endpoint
    #         )
    #
    #     rule = Rule(path, endpoint=endpoint, methods=method_view.methods)
    #     self.url_map.add(rule)
    #     self.view_functions[endpoint] = method_view

    def dispatch_request(self):
        # return value from view_function
        if request.routing_exception is not None:
            raise request.routing_exception
        rule = request.url_rule
        return self.view_functions[rule.endpoint](**request.view_args)

    def full_dispatch_request(self):
        # return a Response object
        try:
            resp = self.preprocess_request()
            if resp is None:
                resp = self.dispatch_request()
        except Exception as e:
            resp = self.handler_exceptions(e)

        return self.finalize_request(resp)

    def finalize_request(self, resp):
        if isinstance(resp, BaseResponse) or callable(resp):
            resp = resp
        else:
            resp = Response(resp)

        self.session_interface.save_session(session, resp, self.session_lifetime)
        return resp

    def handler_exceptions(self, e):
        exc_type = type(e)

        if exc_type in self.handler_map:
            handler = self.handler_map.get(exc_type)
            return handler(e)
        elif issubclass(exc_type, HTTPException):
            return e
        else:
            raise e

    def get_interface(self):
        session_type = self.config.get("SESSION_TYPE", 'redis')
        interface_class = self.session_interface_map[session_type]
        return interface_class(self)

    def render_template(self, template_name, **kws):
        template = self.jinja_env.get_template(template_name)
        return Response(template.render(**kws), content_type='text/html')

    def create_jinja_env(self):
        if self.jinja_loader is None:
            self.jinja_loader = FileSystemLoader(os.path.join(self.root_path, self.template_folder))
        env = Environment(loader=self.jinja_loader)
        env.globals.update(
            url_for=url_for,
            config=self.config,
            request=request,
            g=g,
            session=session
        )
        return env

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def _find_exceptions(exc_class_or_code):

    exc_class = exc_class_or_code
    if isinstance(exc_class_or_code, int):
        exc_class = default_exceptions[exc_class_or_code]

    return exc_class