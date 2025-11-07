FROM python:3.12.0-slim

WORKDIR /chat

COPY requirements.txt Dockerfile docker-compose.yml /chat
COPY app /chat/app


RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /chat

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
