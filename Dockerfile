FROM python:3.12.0-slim

WORKDIR /chat

COPY requirements.txt Dockerfile docker-compose.yml /chat

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY app /chat/app

WORKDIR /chat

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
