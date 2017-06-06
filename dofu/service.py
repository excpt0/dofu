from asyncio import iscoroutine
from collections import defaultdict

from sanic import Sanic
from sanic.exceptions import InvalidUsage
from sanic.handlers import ErrorHandler
from sanic.request import Request as SanicReq
from sanic.response import json

from dofu import errmsg
from dofu.exceptions import RequestError, UnknownMethodError
from dofu.log import log_svc
from dofu.protocol import Request, Response


class ErrHandler(ErrorHandler):
    def default(self, request, exception):
        if isinstance(exception, RequestError):
            msg = errmsg.BAD_REQUEST
        elif isinstance(exception, UnknownMethodError):
            msg = errmsg.UNKNOWN_METHOD
        else:
            msg = errmsg.SERVER_ERROR

        return json(Response(error={'msg': msg}).to_dict())


class DofuService:
    def __init__(self, name, host='127.0.0.1', port=8080, uri='/', ssl=None, service_discover=None):
        self.name = name
        self._sanic = Sanic(error_handler=ErrHandler)
        self.methods = defaultdict(dict)
        self.service_discover = service_discover

        self.settings = {
            'host': host,
            'port': port,
            'ssl': ssl,
        }
        self._sanic.add_route(self.rpc_router, uri=uri, methods=frozenset({'POST'}))

    async def rpc_router(self, request:SanicReq):
        try:
            rpc_req = Request(**request.json())
        except (InvalidUsage, TypeError) as e:
            log_svc.error(RequestError, exc_info=True)
            raise RequestError

        try:
            m = self.methods[rpc_req.method][rpc_req.ver]
        except KeyError:
            log_svc.error(UnknownMethodError, exc_info=True)
            raise UnknownMethodError

        result = m(**rpc_req.payload)
        if iscoroutine(result):
            result = await result

        return json(Response(result=result).to_dict())

    def add_pre_task(self, task):
        self._sanic.listeners['before_server_start'].append(task)

    def run(self):
        self._sanic.run(**self.settings)

