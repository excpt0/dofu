from uuid import uuid4

from asyncio_redis import Connection


class Watcher:
    def watch_active(self):
        raise NotImplementedError

class Agent:
    def set_node_health(self):
        raise NotImplementedError

REDIS_ALL_SERVICES_PATTERN = 'dofu-service'
REDIS_SERVICE_KEY_PATTERN = '%s:{name}' % REDIS_ALL_SERVICES_PATTERN
REDIS_NODE_KEY_PATTERN = '%s:{name}:{node_id}' % REDIS_ALL_SERVICES_PATTERN


class RedisWatcher(Watcher):
    pass


class RedisAgent(Agent):
    pass


class ServiceDiscovery:
    watcher = None
    agent = None

    def get_node_name(self):
        raise NotImplementedError

    def run_agent(self):
        raise NotImplementedError

    def run_watcher(self):
        raise NotImplementedError


class RedisServiceDiscovery(ServiceDiscovery):
    _redis_con = None

    def __init__(self, host, port, db=0, ttl=10):
        self._settings = {'host': host, 'port': port, 'db': db}
        self.ttl = ttl
        self.watcher = RedisWatcher()
        self.agent = RedisAgent()

    def get_node_id(self):
        if not self.node_id:
            self.node_id = uuid4()

        return self.node_id

    async def run(self):
        await self.connect_redis()

    async def connect_redis(self):
        self._redis_con = await Connection.create(**self._settings)

    async def run_agent(self):
        pass

    async def run_watcher(self):
        pass

