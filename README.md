## dofu
Fast and simple framework for building http microservices on python 3.5+ with service discovery. Dofu is using sanic and aiohttp.

### Installation
```sh
$ python -m pip install git+https://github.com/excpt0/dofu
```

### Requirements
 - python 3.5+
 - redis (only for service discovery)

### Example
```python
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

```

```sh
$ curl -XPOST 127.0.0.1:8080 -d'{"method": "foo", "payload": {"arg": "hello!"}}'
$ curl -XPOST 127.0.0.1:8080 -d'{"method": "bar", "payload": {"arg": "foobar"}}'
$ curl -XPOST 127.0.0.1:8080/hello
```
