from asyncio import iscoroutine
from collections import defaultdict
from traceback import format_exc
from uuid import uuid4

from sanic import Sanic
from sanic.exceptions import InvalidUsage
from sanic.handlers import ErrorHandler
from sanic.request import Request as SanicReq
from sanic.response import json

from dofu import errmsg
from dofu.descriptors import register_descriptor, PASS_SVC_DESCRIPTOR, has_descriptor
from dofu.discovery import AliveService, ServiceNode
from dofu.exceptions import RequestError, UnknownMethodError
from dofu.log import log_svc
from dofu.protocol import Request, Response
from dofu.rpc import RPCWrap


class ErrHandler(ErrorHandler):
    def default(self, request, exception):
        if isinstance(exception, RequestError):
            msg = errmsg.BAD_REQUEST
        elif isinstance(exception, UnknownMethodError):
            msg = errmsg.UNKNOWN_METHOD
        else:
            msg = errmsg.SERVER_ERROR
            self.log(format_exc())
            log_svc.error(str(exception))

        return json(Response(error={'msg': msg}).to_dict())


class DofuService:
    _node_id = None

    def __init__(self, name, host='127.0.0.1', port=8080, rpc_uri=None, ssl=None, service_discovery=None):
        self.name = name
        self._sanic = Sanic(error_handler=ErrHandler())
        self.rpc_methods = defaultdict(dict)
        self.service_discovery = service_discovery
        self._rpc_uri = rpc_uri

        self._sanic_settings = {
            'host': host,
            'port': port,
            'ssl': ssl,
        }
        if rpc_uri:
            self._sanic.add_route(self.rpc_router, uri=rpc_uri, methods=frozenset({'POST'}))

    @property
    def node_id(self):
        if not self._node_id:
            self._node_id = str(uuid4())
        return self._node_id

    @property
    def rpc(self):
        if not self.service_discovery:
            raise Exception('Discovery service does not initialized')
        return RPCWrap(self.service_discovery)

    async def rpc_router(self, request:SanicReq):
        log_svc.debug('rpc request: %s' % request.body)
        try:
            rpc_req = Request(**request.json)
        except (InvalidUsage, TypeError) as e:
            log_svc.error(RequestError, exc_info=True)
            raise RequestError
        method_args = rpc_req.payload

        try:
            m = self.rpc_methods[rpc_req.method][rpc_req.ver]
            if has_descriptor(m, PASS_SVC_DESCRIPTOR):
                method_args['svc'] = self
        except KeyError:
            log_svc.error(UnknownMethodError, exc_info=True)
            raise UnknownMethodError

        result = m(**method_args)
        if iscoroutine(result):
            result = await result

        return json(Response(result=result).to_dict())

    def add_pre_task(self, task):
        self._sanic.listeners['before_server_start'].append(task)

    def run(self):
        if self.service_discovery:
            svc = AliveService(service_name=self.name, stype='rpc')
            node = ServiceNode(
                service_name=self.name,
                node_id=self.node_id,
                host=self._sanic_settings['host'],
                port=self._sanic_settings['port'],
                uri=self._rpc_uri,
            )
            async def __init(app, loop):
                await self.service_discovery.run(loop, service=svc, node=node)
            self.add_pre_task(__init)

        self._sanic.run(**self._sanic_settings)

    def register_http(self, uri, method):
        def wrapped(handler):
            self._sanic.add_route(handler, uri, method)
            return handler
        return wrapped

    def register(self, method_name, ver=1, pass_svc=False):
        # decorator
        def wrapped(handler):
            self.rpc_methods[method_name][ver] = handler
            if pass_svc:
                register_descriptor(handler, PASS_SVC_DESCRIPTOR)
            return handler
        return wrapped
