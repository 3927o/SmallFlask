from werkzeug import run_simple
from my_flask import Application, request, MethodView, g, session
from my_flask.helpers import send_file

app = Application()


@app.before_request("index")
def intercept_request():
    return "request is intercepted"


def index():
    g.name = "lin"
    return "Hello World!<div>233</div>you are visiting " + request.url


def error():
    raise MyException


class MyException(Exception):
    pass


@app.error_handler(MyException)
def my_exc(e):
    return "raised a exception"


class MyView(MethodView):
    def get(self, id_):
        return "my method_view, id is " + str(id_) + ", method is get"

    def post(self, id_):
        return "my method_view, id is " + str(id_) + ", method is post"

    def delete(self, id_):
        return "my method_view, id is " + str(id_) + ", method is delete"
    

def test_session(value):
    resp = ""
    if session.get('test', None) is not None:
        return "session already be set "+"value is {}".format(session['test'])
    session['test'] = value
    return "set session succeed, "+"value is "+value


def test_file():
    return send_file('./my_flask/app.py')


@app.route('/static_file')
def test_send_static_file():
    return app.send_static_file('test.jpg')


@app.route('/template')
def test_template():
    g.name = 'g,name'
    return app.render_template('test.html', name='lin', bool_len=False)


app.add_url_rule('/', index)
app.add_url_rule('/error', error)
app.add_url_rule('/index/<int:id_>', MyView.as_view('test_view'))
app.add_url_rule('/session/<string:value>', test_session)
app.add_url_rule('/file', test_file)
# app.register_error_handler(MyException, my_exc)

run_simple('127.0.0.1', 5000, app, use_reloader=True, use_debugger=False)