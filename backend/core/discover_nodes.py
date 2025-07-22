# backend/core/discover_nodes.py
from __future__ import annotations

import os
from typing import Dict, Tuple, Optional, Any
from asyncua import Client, ua
from asyncua.ua.uaerrors import UaStatusCodeError

URI = os.getenv("OPCUA_NS_URI", "http://example.com/robots")


async def get_ns_idx(client: Client, uri: str) -> int:
    uris = await client.get_namespace_array()
    try:
        return uris.index(uri)
    except ValueError:
        print(f"⚠️ Namespace '{uri}' not in server list: {uris}")
        # 取第一個非 0 的 namespace 當 fallback
        return next((i for i, _ in enumerate(uris) if i != 0), 1)


async def _find_child_by_name(parent, target_name: str):
    """
    只比對 BrowseName.Name，不理會 NamespaceIndex，避免 BadNoMatch。
    找不到回傳 None。
    """
    for ch in await parent.get_children():
        bn = await ch.read_browse_name()
        if bn.Name == target_name:
            return ch
    return None


async def discover_opcua_nodes(
    *,
    client: Client,
    robot: str,
    uri: str = URI,
    return_tree: bool = False,
) -> Tuple[Dict[str, str], int, Optional[Dict[str, Any]]]:
    """
    掃描 Objects/RobotGroup/<robot> 底下所有 Variable，回傳：
    - flat_map: { 'robot_1/left_arm/VarX': 'ns=2;i=1234', ... }
    - ns_idx  : 你的自訂 namespace index
    - tree    : （可選）樹狀 dict
    """
    ns_idx = await get_ns_idx(client, uri)

    objects = client.nodes.objects

    robot_group = await _find_child_by_name(objects, "RobotGroup")
    if robot_group is None:
        raise RuntimeError("找不到 RobotGroup（不論 ns）")

    robot_node = await _find_child_by_name(robot_group, robot)
    if robot_node is None:
        raise RuntimeError(f"找不到 RobotGroup/{robot}")

    flat: Dict[str, str] = {}
    tree: Dict[str, Any] = {}

    async def walk(node, path, subtree):
        for ch in await node.get_children():
            ncls = await ch.read_node_class()
            name = (await ch.read_browse_name()).Name
            if ncls == ua.NodeClass.Variable:
                flat_path = "/".join(path + [name])
                flat[flat_path] = ch.nodeid.to_string()
                subtree[name] = ch.nodeid.to_string()
            else:
                next_tree: Dict[str, Any] = {}
                subtree[name] = next_tree
                await walk(ch, path + [name], next_tree)

    await walk(robot_node, [robot], tree)

    return flat, ns_idx, (tree if return_tree else None)


