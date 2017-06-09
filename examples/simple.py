from sanic.response import json

from dofu.discovery import RedisServiceDiscovery
from dofu.service import DofuService


service = DofuService('simple', rpc_uri='/', service_discovery=RedisServiceDiscovery())


@service.register('foo', pass_svc=True)
async def foo_handler(svc, arg):
    rpc_res = await svc.rpc.simple.bar(arg=arg)
    return {'foo': 'exec', 'rpc': rpc_res['result']}


@service.register('bar')
async def bar_handler(arg):
    return {'bar': arg}


@service.register_http('/hello', {'POST'})
async def http_handler(request):
    return json({'hello': 'world'})


if __name__ == '__main__':
    service.run()
