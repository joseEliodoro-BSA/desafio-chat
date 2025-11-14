import redis.asyncio as redis
from redis.client import PubSub
from typing import Dict, Callable, Tuple
import json
import os
import asyncio
from app.singleton import Singleton


class RedisClient(metaclass=Singleton):
    def __init__(self):
        self.redis_url = "redis://redis:6379"
        self._redis_client = None
        self._tasks: Dict[str, Tuple[asyncio.Task, PubSub]] = {}

    async def _get_client(self):
        """Obtém ou cria a conexão Redis async"""
        if self._redis_client is None:
            self._redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis_client

    async def sub(self, room: str, fn: Callable | None = None) \
        -> Tuple[asyncio.Task,PubSub]:
        """Subscribe a um canal com handler assíncrono"""
        client = await self._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(room)

        async def receive():
            async for msg in pubsub.listen():
                if msg and msg["type"] == "message":
                    if fn:
                        await fn(msg)
                    
        task = asyncio.create_task(receive())
        # self._tasks[room] = (task, pubsub)
        return (task, pubsub)

    async def unsub(self, room: str):
        if room in self._tasks:
            task, pubsub = self._tasks[room]
            await pubsub.unsubscribe()
            task.cancel()
            del self._tasks[room]

    async def pub(self, room: str, msg: Dict):
        client = await self._get_client()
        await client.publish(room, json.dumps(msg))


async def main():
    pubsub = RedisClient()

    async def callback(msg):
        print(f"Mensagem recebida: {msg}")

    # Inscrever em múltiplos canais de forma assíncrona
    print("Iniciando subscriptions...")
    
    task1, pubsub1= await pubsub.sub("test_1", callback)
    task2, pubsub2= await pubsub.sub("test_2", callback)

    # Aguardar um pouco e publicar mensagens
    await asyncio.sleep(2)
    await pubsub.pub("test_1", {"mensagem": "Hello canal 1"})
    await pubsub.pub("test_2", {"mensagem": "Hello canal 2"})

    # Manter rodando por 10 segundos para receber mensagens
    await asyncio.sleep(10)
    
    # Cleanup
    await pubsub1.unsubscribe()
    await pubsub2.unsubscribe()
    task1.cancel()
    task2.cancel()


    await pubsub.pub("test_1", {"mensagem": "segundo teste no canal 1"})
    await pubsub.pub("test_2", {"mensagem": "segundo teste no canal 2"})


if __name__ == "__main__":
    os.system("clear")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        os._exit(0)
