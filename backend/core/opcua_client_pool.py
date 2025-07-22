from asyncua import Client

_clients: dict[str, Client] = {}

async def get_or_create_client(endpoint: str) -> Client:
    c = _clients.get(endpoint)
    if c is None:
        c = Client(endpoint)
        await c.connect()
        _clients[endpoint] = c
    return c

async def shutdown_clients():
    for c in _clients.values():
        await c.disconnect()
    _clients.clear()
