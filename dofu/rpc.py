from random import choice

import aiohttp

from dofu.protocol import Request, Response


class SessionCache:
    ses = None

    def __init__(self):
        if not self.ses:
            SessionCache.ses = aiohttp.ClientSession()

    def __getattr__(self, item):
        getattr(self.ses, item)


async def perform_rpc_request(url, ver=1, **kwargs):
    ses = SessionCache()
    async with ses.post(url=url, data=Request(**kwargs).to_json()) as http_resp:
        return Response(**http_resp).to_dict()


class RPCWrap:
    service_discovery = None
    service_name = None

    def __init__(self, service_discovery, service_name=None, method=None):
        self.service_discovery = service_discovery
        self.service_name = service_name
        self.method = method

    def __call__(self, ver=1, **kwargs):
        urls = self.service_discovery.service_urls(self.service_name)
        return perform_rpc_request(choice(urls), ver, **kwargs)

    def __getattr__(self, item):
        if not self.service_name:
            return RPCWrap(self.service_discovery, item)
        elif not self.method:
            return RPCWrap(self.service_discovery, self.service_name, item)
