from asyncua import Client
import asyncio

class OPCUAStreamer:
    def __init__(self, endpoint: str, node_ids: list[str]):
        self.endpoint = endpoint
        self.node_ids = node_ids
        self.client = Client(url=endpoint)
        self.nodes = []
        self.connected = False

    async def connect(self):
        await self.client.connect()
        self.nodes = [self.client.get_node(nodeid) for nodeid in self.node_ids]
        self.connected = True

    async def read_all(self):
        if not self.connected:
            await self.connect()
        values = await asyncio.gather(*(n.read_value() for n in self.nodes))
        return dict(zip(self.node_ids, values))

