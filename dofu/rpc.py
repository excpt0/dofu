from random import choice

import aiohttp

from dofu.protocol import Request, Response


class SessionCache:
    ses = None

    @classmethod
    def get(cls):
        if not cls.ses:
            SessionCache.ses = aiohttp.ClientSession()
        return cls.ses


async def perform_rpc_request(url, request):
    ses = SessionCache.get()
    request_data = request.to_json()
    async with ses.post(url=url, data=request_data) as http_resp:
        data = await http_resp.json()
        return Response(**data).to_dict()


class RPCWrap:
    service_discovery = None
    service_name = None

    def __init__(self, service_discovery, service_name=None, method=None):
        self.service_discovery = service_discovery
        self.service_name = service_name
        self.method = method

    def __call__(self, ver=1, **kwargs):
        urls = self.service_discovery.service_urls(self.service_name)
        if not urls:
            raise Exception('No alive nodes to execute the request')
        request = Request(self.method, kwargs, ver)
        return perform_rpc_request(choice(urls), request)

    def __getattr__(self, item):
        if not self.service_name:
            return RPCWrap(self.service_discovery, item)
        elif not self.method:
            return RPCWrap(self.service_discovery, self.service_name, item)
