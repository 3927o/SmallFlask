from redis import Redis
from mimetypes import guess_type

from werkzeug.wsgi import wrap_file

from .globals import current_app, request
from .wrappers import Response


def get_redis(app, **options):
    host = app.config['REDIS_HOST']
    port = app.config['REDIS_PORT']
    pwd = app.config['REDIS_PWD']
    redis = Redis(host, port, pwd, **options)
    return redis


def render_template(template_name, **context):
    template = current_app.jinja_env.get_template(template_name)
    return template.render(context)


def url_for():
    pass


def send_file(filename, mimetype=None, cache_timeout=60*60*24):
    if mimetype is None:
        mimetype = guess_type(filename)[0]
    file = open(filename, "rb")
    data = wrap_file(request.environ, file)
    resp = Response(data, direct_passthrough=True, mimetype=mimetype)
    resp.cache_control.public = True
    resp.cache_control.max_age = cache_timeout
    return resp


def send_from_directory(directory, filename, **options):
    from posixpath import join
    filename = join(directory, filename)
    return send_file(filename, **options)
