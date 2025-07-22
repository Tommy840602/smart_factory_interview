from asyncua import Client
from asyncua.ua.uaerrors import UaError

class OPCUAStreamer:
    def __init__(self, client: Client, node_ids: list[str]):
        self.client = client
        self.node_ids = node_ids
        self.nodes = [self.client.get_node(nid) for nid in node_ids]

    async def read_all(self):
        try:
            values = await self.client.read_values(self.nodes)
            return dict(zip(self.node_ids, values))
        except UaError as e:
            raise e




