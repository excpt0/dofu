from ujson import dumps


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
        self.extra = extra or {}

    def to_dict(self):
        return {
            'ver': self.ver,
            'method': self.method,
            'payload': self.payload,
            'extra': self.extra
        }

    def to_json(self):
        return dumps(self.to_dict())


class Response(object):
    __slots__ = ['result', 'error']

    def __init__(self, result=None, error=None):
        assert any([result, error])
        assert not all([result, error])

        self.result = result
        self.error = error

    def to_dict(self):
        if self.result:
            return {'result': self.result}
        else:
            return {'error': self.error}

    def to_json(self):
        return dumps(self.to_dict())
