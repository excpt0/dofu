from asyncio import sleep
from collections import defaultdict
from ujson import loads, dumps

from asyncio_redis import Connection


REDIS_ALL_SERVICES_PATTERN = 'dofu-service'
REDIS_ALL_NODES_PATTERN = 'dofu-node'
REDIS_SERVICE_KEY_PATTERN = '%s:{name}' % REDIS_ALL_SERVICES_PATTERN
REDIS_NODE_KEY_PATTERN = '%s:{node_id}' % REDIS_ALL_NODES_PATTERN


class ServiceDiscovery:

    def get_node_name(self):
        raise NotImplementedError

    def watch_alive(self):
        raise NotImplementedError

    def set_node_health(self):
        raise NotImplementedError


class ServiceNode:
    def __init__(self, node_id, service_name, host, port, uri, protocol='http', is_alive=True):
        self.node_id = node_id
        self.service_name = service_name
        self.host = host
        self.port = port
        self.uri = uri
        self.protocol = protocol
        self.is_alive = is_alive

    @property
    def url(self):
        uri = self.uri
        if not self.uri.startswith('/'):
            uri = '/' + self.uri
        return '{proto}://{host}:{port}{uri}'.format(proto=self.protocol, host=self.host, port=self.port, uri=uri)

    def to_dict(self):
        return {
            'node_id': self.node_id,
            'host': self.host,
            'service_name': self.service_name,
            'port': self.port,
            'uri': self.uri,
            'protocol': self.protocol,
        }


class AliveService:
    def __init__(self, service_name, stype, tags=None, nodes=None):
        self.stype = stype
        self.tags = tags or []
        self.service_name = service_name
        self._nodes = {n.node_id: n for n in nodes} if nodes else {}

    @property
    def nodes_list(self):
        return self._nodes.values()

    @property
    def nodes_ids(self):
        return self._nodes.keys()

    def append_node(self, node):
        self._nodes[node.node_id] = node

    def remove_node(self, node_id):
        del self._nodes[node_id]

    def to_dict(self):
        return {
            'stype': self.stype,
            'tags': self.tags,
            'service_name': self.service_name,
        }


class NodeProxy:
    def __init__(self, node, service):
        self.node = node
        self.node_id = node.node_id
        self.service = service
        self.service.append_node(node)

    def remove(self):
        self.service.remove_node(self.node_id)

    def is_alive(self, val):
        self.node.is_alive = val


class RedisServiceDiscovery(ServiceDiscovery):
    _redis_con = None
    is_running = False
    _health_task = None
    _watch_task = None
    _current_node = None
    _current_node_cache = None

    def __init__(self, rdbhost='127.0.0.1', rdbport=6379, db=0, ttl=10, health_set_interval=2, watch=True, health_set=True):
        self._rdb_settings = {'host': rdbhost, 'port': rdbport, 'db': db}
        self._alive_services = {}
        self._alive_nodes = {}
        self.ttl = ttl
        self.health_set_interval = health_set_interval
        self.watch = watch
        self.health_set = health_set
        self._services_urls_cache = defaultdict(list)

    async def declare_service(self, service):
        await self._redis_con.set(
            REDIS_SERVICE_KEY_PATTERN.format(name=service.service_name),
            dumps(service.to_dict()), only_if_not_exists=True)

    def service_urls(self, service_name):
        if not self._services_urls_cache[service_name]:
            s = self.get_service_by_name(service_name)
            for n in s.nodes_list:
                self._services_urls_cache[s.service_name].append(n.url)
        return self._services_urls_cache[service_name]

    def stop(self):
        if self._watch_task:
            self._watch_task.cancel()
        if self._health_task:
            self._health_task.cancel()
        self.is_running = False

    async def run(self, loop, service, node):
        self._current_node = node
        await self.connect_redis()
        await self.declare_service(service)

        if self.watch:
            self._watch_task = loop.create_task(self.watch_alive())

        if self.health_set:
            self._health_task = loop.create_task(self.set_node_health())
        self.is_running = True

    async def connect_redis(self):
        self._redis_con = await Connection.create(**self._rdb_settings)

    async def _get_service_desc_from_rdb(self, service_name):
        r = await self._redis_con.get(REDIS_SERVICE_KEY_PATTERN.format(name=service_name))
        if r:
            return AliveService(**loads(r))
        return None

    async def _get_node_desc_from_rdb(self, node_id):
        r = await self._redis_con.get(REDIS_NODE_KEY_PATTERN.format(node_id=node_id))
        if r:
            return ServiceNode(**loads(r))
        return None

    async def append_services_by_name(self, names):
        for n in names:
            svc = await self._get_service_desc_from_rdb(n)
            if not svc:
                continue
            self._alive_services[svc.service_name] = svc

    def get_service_by_name(self, name):
        return self._alive_services[name]

    async def append_nodes(self, nodes_ids):
        for n in nodes_ids:
            node = await self._get_node_desc_from_rdb(n)

            if not node:
                continue

            self._alive_nodes[node.node_id] = NodeProxy(node, self.get_service_by_name(node.service_name))

    def remove_services(self, names, delete_nodes=False):
        for n in names:
            if delete_nodes:
                self.remove_nodes(self._alive_services[n].nodes_ids)
            del self._alive_services[n]

    def remove_nodes(self, nodes_ids):
        for n in nodes_ids:
            try:
                self._alive_nodes[n].is_alive = False
                self._alive_nodes[n].remove()
                del self._alive_nodes[n]
                del self._services_urls_cache[n]
            except KeyError:
                pass

    async def watch_alive(self):
        while True:
            svc_keys = await (await self._redis_con.keys(REDIS_ALL_SERVICES_PATTERN + '*')).aslist()
            current_svc = [x.replace(REDIS_ALL_SERVICES_PATTERN + ':', '') for x in svc_keys]

            new_svc_names = (set(current_svc)) - set(self._alive_services.keys())
            dead_svc = set(self._alive_services.keys()) - (set(current_svc))

            self.remove_services(dead_svc)
            await self.append_services_by_name(new_svc_names)

            node_keys = await (await self._redis_con.keys(REDIS_ALL_NODES_PATTERN + '*')).aslist()
            current_nodes = [x.replace(REDIS_ALL_NODES_PATTERN + ':', '') for x in node_keys]
            current_nodes_set = set(current_nodes)
            stored_nodes_set = set(self._alive_nodes.keys())

            new_nodes_ids = current_nodes_set - stored_nodes_set
            dead_nodes = stored_nodes_set - current_nodes_set

            self.remove_nodes(dead_nodes)
            await self.append_nodes(new_nodes_ids)
            await sleep(0.01)

    async def set_node_health(self):
        while True:
            if not self._current_node_cache:
                self._current_node_cache = dumps(self._current_node.to_dict())
            await self._redis_con.set(
                REDIS_NODE_KEY_PATTERN.format(node_id=self._current_node.node_id),
                self._current_node_cache,
                expire=self.ttl,
                only_if_not_exists=True)
            await sleep(self.health_set_interval)
