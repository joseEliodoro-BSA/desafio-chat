from redis import Redis
from typing import Dict, Callable
import json
import os
import asyncio
from threading import Thread
from app.singleton import Singleton


class PubSub(metaclass=Singleton):
    def __init__(self):
        self.redis_client = Redis(
            # host="redis", 
            host="localhost", 
            port=6379, 
            encoding="utf-8", 
            decode_responses=True
        )

    def sub(self, room: str, fn: Callable | None = None):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(room)
        for msg in pubsub.listen():
            if msg and msg["type"] == "message":
                if fn:
                    asyncio.run(fn(msg))
                else:
                    print(msg["data"])
                

    def pub(self, room: str, msg: Dict):
        self.redis_client.publish(room, json.dumps(msg))

async def main():
    pubsub = PubSub()

    # Rodar subscribers em threads para não travar o event loop
    t1 = Thread(target=pubsub.sub, args=("test_1",), daemon=True)
    # t2 = Thread(target=pubsub.sub, args=("test_2",), daemon=True)

    t1.start()
    # t2.start()

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    os.system("clear")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        os._exit(0)
