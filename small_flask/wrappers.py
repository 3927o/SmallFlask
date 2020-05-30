from werkzeug.wrappers import Request as RequestBase
from werkzeug.wrappers import Response as ResponseBase


class Request(RequestBase):
    routing_exception = None
    url_rule = None
    view_args = None
    url_adapter = None

    def __init__(self, environ, app):
        super(Request, self).__init__(environ)
        self.url_adapter = app.url_map.bind_to_environ(environ)
        try:
            result = self.url_adapter.match(return_rule=True)
            self.url_rule, self.view_args = result
        except Exception as e:
            self.routing_exception = e

    @property
    def endpoint(self):
        if self.url_rule is not None:
            return self.url_rule.endpoint


class Response(ResponseBase):
    pass