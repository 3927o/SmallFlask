import sys
from werkzeug.wrappers import Request, Response


handler_map = dict()  # handler_map[exc] = handler
view_func_map = dict()  # view_func_map[path] = view_func
request = Request


def add_url_rule(path, view_func):
    view_func_map[path] = view_func


def add_errorhandler(exc, handler):
    handler_map[exc] = handler


def not_found():
    return "page not found"


def url_mapper(path):
    if path in view_func_map:
        return view_func_map[path]

    return not_found


def handle_exceptions(e):
    exc_type = type(e)

    if exc_type in handler_map:
        handler = handler_map[exc_type]
        resp = handler(e)
    else:
        raise e

    return resp


def application(environ, start_response):

    global request
    request = Request(environ)

    view_func = url_mapper(request.path)

    try:
        response_body = view_func()
    except Exception as e:  # e 是异常类的一个实例化对象
        response_body = handle_exceptions(e)

    response = Response(response_body)
    iterable = response(environ, start_response)

    return iterable

# request对象
# endpoint
