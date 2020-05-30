from redis import Redis
import pickle
import uuid

from .helpers import get_redis


class Session(dict):
    def __init__(self, data, sid):
        super(Session, self).__init__(data)
        self.sid = sid


class SessionInterface:

    serializer = pickle
    session_class = Session

    def __init__(self, app):
        self.key_prefix = app.session_key_prefix
        self.session_cookie_name = app.session_cookie_name

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name, None)
        if sid is None:
            sid = self.generate_sid()
            data = {"sid": sid}
            return self.session_class(data, sid)
        data = self.get_data(sid)
        if data is not None:
            return self.session_class(data, sid)
        else:
            pass

    def save_session(self, session, response, session_lifetime=60 * 10):
        self.save_to_db(session, session_lifetime)
        response.set_cookie(self.session_cookie_name, str(session.sid), max_age=session_lifetime)

    def generate_sid(self):
        raise NotImplementedError()

    def get_data(self, sid):
        # return a dict
        raise NotImplementedError()

    def save_to_db(self, session, session_lifetime):
        raise NotImplementedError()


# class RedisSessionInterface:
#
#     serializer = pickle
#     session_class = Session
#
#     def __init__(self, app):
#         self.redis = get_redis(app)
#         self.key_prefix = app.session_key_prefix
#         self.session_cookie_name = app.session_cookie_name
#
#     def open_session(self, app, request):
#         sid = request.cookies.get(app.session_cookie_name, None)
#         if sid is None:
#             sid = uuid.uuid4()
#             data = {"sid": sid}
#             return self.session_class(data, sid)
#         val = self.redis.get(self.key_prefix + str(sid))
#         if val is not None:
#             data = self.serializer.loads(val)
#             return self.session_class(data, sid)
#         else:  # cookies 和 redis 同步更新
#             pass
#
#     def save_session(self, session, response, session_lifetime=60*10):
#         val = self.serializer.dumps(dict(session))
#         self.redis.setex(name=self.key_prefix + str(session.sid), value=val, time=session_lifetime)
#         response.set_cookie(self.session_cookie_name, str(session.sid), max_age=session_lifetime)


class RedisSessionInterface(SessionInterface):

    def __init__(self, app):
        super(RedisSessionInterface, self).__init__(app)
        self.redis = get_redis(app)

    def generate_sid(self):
        return uuid.uuid4()

    def get_data(self, sid):
        val = self.redis.get(self.key_prefix+str(sid))
        if val is not None:
            return self.serializer.loads(val)

    def save_to_db(self, session, session_lifetime=60 * 10):
        val = self.serializer.dumps(dict(session))
        self.redis.setex(name=self.key_prefix+str(session.sid), value=val, time=session_lifetime)