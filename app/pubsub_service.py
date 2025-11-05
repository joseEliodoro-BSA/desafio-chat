from redis import Redis
from typing import Dict, Callable
import json
import os
import asyncio
from threading import Thread

class PubSub:
    def __init__(self):
        self.r = Redis(host="localhost", port=6379, encoding="utf-8", decode_responses=True)

    def sub(self, room: str, fn: Callable):
        pubsub = self.r.pubsub()
        pubsub.subscribe(room)
        for msg in pubsub.listen():
            if msg and msg["type"] == "message":
                asyncio.run(fn(msg))

    def pub(self, room: str, msg: Dict):
        self.r.publish(room, json.dumps(msg))

async def main():
    pubsub = PubSub()

    # Rodar subscribers em threads para não travar o event loop
    Thread(target=pubsub.sub, args=("test_1",), daemon=True).start()
    Thread(target=pubsub.sub, args=("test_2",), daemon=True).start()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        os._exit(0)
