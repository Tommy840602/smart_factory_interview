from fastapi import WebSocket
from typing import Dict, Set
from collections import defaultdict

ws_clients: Dict[str, Set[WebSocket]] = defaultdict(set)

def register_ws_client(topic: str, ws: WebSocket):
    ws_clients[topic].add(ws)

def unregister_ws_client(topic: str, ws: WebSocket):
    ws_clients[topic].discard(ws)
