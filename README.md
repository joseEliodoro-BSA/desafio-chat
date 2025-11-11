# Serviço de Chat em Tempo Real

## Descrição

Serviço de chat em tempo real que permite aos usuários se comunicarem através de diferentes canais: **chat geral**, **chats privados** e **chats em grupo**.

## Funcionalidades

- **Chats Privados**: Comunicação direta entre dois usuários
- **Chats em Grupo**: Comunicação entre múltiplos usuários
- **Chat Geral**: Todos os usuários conectados recebem mensagens compartilhadas em tempo real

## Tecnologias

O projeto utiliza:
- **FastAPI**: Framework web assíncrono para Python
- **WebSockets**: Comunicação bidirecional em tempo real
- **Pub/Sub**: Sistema de publicação e subscrição para gerenciamento de mensagens, foi utilizado o pub/sub do redis.
- **Docker**: Containerização da aplicação

## Rotas
* Acesse a rota``http://localhost:8000/docs``
    * Criar novo usuário.
    * Listar usuários cadastrados.
    * Listar todas as mensagens enviadas.

* Conecte-se à rota `ws://localhost:8000/ws/{{chat_name}}?username={{username}}` onde:
    * `chat_name`: `geral` (chat público), `privado` (chat privado), ou qualquer outro nome customizado
    * Ao conectar em qualquer chat, você receberá mensagens do chat privado destinadas a você e mensagens do chat geral

* **Chat Privado**: Envie mensagens para um usuário específico
    * Payload: `{command: "send_message", msg: "sua mensagem", username_receive: "usuário destinatário"}`

* **Chat Geral e Customizado**: Envie mensagens para todos os usuários no canal
    * Payload: `{command: "send_message", msg: "sua mensagem"}`
