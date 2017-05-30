from json import dumps


class Request(object):
    __slots__ = ['ver', 'method', 'payload', 'extra']

    def __init__(self, method, payload, ver=1, extra=None):
        assert isinstance(method, str)
        assert isinstance(payload, dict)
        assert isinstance(ver, (int, str))
        if extra:
            assert isinstance(extra, dict)
        self.method = method
        self.payload = payload
        self.ver = ver
        self.extra = extra

    def to_dict(self):
        val = {
            'ver': self.ver,
            'method': self.ver,
            'payload': self.ver,
        }

        if self.extra:
            val['extra'] = self.extra

        return val

    def to_json(self):
        return dumps(self.to_dict())


class Response(object):
    def __init__(self, payload, errmsg, errtype, code=200):
        pass
