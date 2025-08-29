# backend/schemas/ws_manager.py
from __future__ import annotations
from typing import Dict, Set, Optional
from collections import defaultdict
import asyncio
import json
from fastapi import WebSocket

class WebSocketHub:
    """
    - clients: { "robot_1/left_arm": {WebSocket, ...}, ... }
    - queues:  { "robot_1/left_arm": asyncio.Queue[str], ... }
    - 每個 path 一個 broadcaster（單協程扇出），避免競態
    """
    def __init__(self, loop: asyncio.AbstractEventLoop, queue_maxsize: int = 1000):
        self.loop = loop
        self.clients: Dict[str, Set[WebSocket]] = defaultdict(set)
        self.queues: Dict[str, asyncio.Queue[str]] = {}
        self.broadcasters: Dict[str, asyncio.Task] = {}
        self.queue_maxsize = queue_maxsize
        self.lock = asyncio.Lock()

    async def attach(self, path: str, ws: WebSocket) -> None:
        async with self.lock:
            self.clients[path].add(ws)
            if path not in self.queues:
                self.queues[path] = asyncio.Queue(maxsize=self.queue_maxsize)
            if path not in self.broadcasters or self.broadcasters[path].done():
                self.broadcasters[path] = asyncio.create_task(self._broadcaster(path))
        print(f"[WebSocket] Client connected {path} -> {len(self.clients[path])} clients")

    async def detach(self, path: str, ws: WebSocket) -> None:
        async with self.lock:
            s = self.clients.get(path)
            if s:
                s.discard(ws)
                n = len(s)
                print(f"[WebSocket] Client disconnected {path} -> {n} clients")
                if n == 0:
                    # 回收資源
                    self.clients.pop(path, None)
                    task = self.broadcasters.pop(path, None)
                    if task and not task.done():
                        task.cancel()
                    self.queues.pop(path, None)

    async def publish(self, path: str, message: dict | str) -> None:
        """在 APP loop 上呼叫；若在其他執行緒，請用 run_coroutine_threadsafe 包裝"""
        if isinstance(message, dict):
            data = json.dumps(message, ensure_ascii=False)
        else:
            data = message

        async with self.lock:
            q = self.queues.get(path)
            if q is None:
                q = asyncio.Queue(maxsize=self.queue_maxsize)
                self.queues[path] = q
            if path not in self.broadcasters or self.broadcasters[path].done():
                self.broadcasters[path] = asyncio.create_task(self._broadcaster(path))

        # 佇列滿則丟掉最舊，避免阻塞
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            try:
                _ = q.get_nowait()
            except Exception:
                pass
            q.put_nowait(data)

    async def _broadcaster(self, path: str) -> None:
        q = self.queues[path]
        while True:
            data = await q.get()
            clients = list(self.clients.get(path, set()))
            if not clients:
                continue
            dead: list[WebSocket] = []
            for ws in clients:
                try:
                    await ws.send_text(data)
                except Exception:
                    dead.append(ws)
            if dead:
                async with self.lock:
                    s = self.clients.get(path)
                    if s:
                        for d in dead:
                            s.discard(d)

# ===== 全域單例（啟動時初始化） =====
_APP_LOOP: Optional[asyncio.AbstractEventLoop] = None
_HUB: Optional[WebSocketHub] = None

def init_ws_hub(loop: Optional[asyncio.AbstractEventLoop] = None, queue_maxsize: int = 1000) -> WebSocketHub:
    """在 FastAPI 啟動時呼叫一次"""
    global _APP_LOOP, _HUB
    _APP_LOOP = loop or asyncio.get_running_loop()
    _HUB = WebSocketHub(_APP_LOOP, queue_maxsize=queue_maxsize)
    print("[WS Hub] ✅ initialized (event loop ready)")
    return _HUB

def get_ws_hub() -> WebSocketHub:
    if _HUB is None:
        raise RuntimeError("WebSocketHub not initialized. Call init_ws_hub() at startup.")
    return _HUB

def get_app_loop() -> asyncio.AbstractEventLoop:
    if _APP_LOOP is None:
        raise RuntimeError("APP event loop not set. Call init_ws_hub() at startup.")
    return _APP_LOOP

