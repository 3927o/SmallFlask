from werkzeug import run_simple

from simple_demo import application, add_url_rule, add_errorhandler, request


class MyException(Exception):
    pass


def index():
    return "hello world"


def my_exc(e):
    return "raised a exception"


def errors():
    raise MyException


add_url_rule('/', index)
add_url_rule('/error', errors)
add_errorhandler(MyException, my_exc)  # 传入一个类，而非对象

run_simple('127.0.0.1', 5000, application, use_reloader=True, use_debugger=False)