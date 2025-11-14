import asyncio
import websockets
from websockets import ClientConnection
import os
import sys
import json

username = None
async def send(ws, loop): 
    room = None
    while True:
        os.system("clear")
        print(f"USER: ({username}) | ROOM: ({room})")
        print('COMMAND 1: connect_room')
        print('COMMAND 2: send_message')
        print('COMMAND 3: send_private_message')
        print('COMMAND 4: disconnect_room')
        print('COMMAND 5: create_room')
        
        user_input = await loop.run_in_executor(None, input, "DIGITE COMMAND: ")

        if(user_input == "1"):
            room = await loop.run_in_executor(None, input, "DIGITE ROOM: ")
            password = await loop.run_in_executor(None, input, "DIGITE SENHA: ")
            await ws.send(json.dumps({ 
                "command": "connect_room", 
                "room": room,
                "password": password 
            }))
        elif(user_input == "2"):
            message = await loop.run_in_executor(None, input, "DIGITE MESSAGE: ") 
            await ws.send(json.dumps({ 
                "command": "send_message",
                "msg": message or "mensagem enviada pelo client "
            }))
        elif(user_input == "3"):
            remetente = await loop.run_in_executor(None, input, "DIGITE remetente: ") 
            await ws.send(json.dumps({ 
                "command": "send_message", 
                "msg": "mensagem enviada pelo client ",
                "username_receive": remetente
            }))
        elif(user_input == "4"):
            await ws.send(json.dumps({ 
                "command": "disconnect_room", 
            }))
            room = None
        elif(user_input == "5"):
            room = await loop.run_in_executor(None, input, "DIGITE ROOM: ")
            password = await loop.run_in_executor(None, input, "DIGITE SENHA: ")
            await ws.send(json.dumps({ 
                "command": "create_room",
                "room": room or "reservado",
                "password": password 
                
            }))

        await loop.run_in_executor(None, input, "PRECIONE ENTER PARA APAGAR TUDO")

async def reveice(ws: ClientConnection):
    async for msg in ws:
      print(f"\rSERVER: {msg}")


async def connection():
    global username
    print("[geral, privado, *]")
    # chat = input("Digite o chat: ")
    if username == "":
        username = "test"
    # async with websockets.connect(f"ws://localhost:8000/ws/{chat}?username={username}") as websocket:
    async with websockets.connect(f"ws://localhost:8000/ws?username={username}") as websocket:
        loop = asyncio.get_event_loop()
        await asyncio.gather(reveice(websocket), send(websocket, loop))



if __name__ == "__main__":
    try:
        username = sys.argv[1] or None
    except:
        if not username:
            username = input("Digite seu username: ")
    os.system("clear")
    try:
        asyncio.run(connection())
    except KeyboardInterrupt:
        os._exit(0)