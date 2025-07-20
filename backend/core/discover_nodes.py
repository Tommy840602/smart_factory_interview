from asyncua import Client

async def discover_opcua_nodes(endpoint: str, robot: str) -> list[str]:
    async with Client(url=endpoint) as client:
        root = client.nodes.root
        robot_node = await root.get_child(["0:Objects", f"2:RobotGroup", f"2:{robot}"])
        all_vars = await robot_node.get_variables()
        return [v.nodeid.to_string() for v in all_vars]
