# Docker Hello App

Небольшое веб-приложение на стандартной библиотеке Python в Docker-контейнере
и `docker-compose.yml`, который поднимает несколько контейнеров сразу.

## Запуск

```bash
docker build -t docker-hello-app:1.0.0 .
docker run -d --name hello-app -p 8000:8000 docker-hello-app:1.0.0
```

Открыть http://localhost:8000

```bash
docker ps
docker logs hello-app
curl http://localhost:8000/api/info
docker stop hello-app && docker rm hello-app
```

Сменить порт без правки кода:

```bash
docker build --build-arg PORT=8080 -t docker-hello-app:8080 .
docker run -d -p 8080:8080 docker-hello-app:8080
```

## Docker Compose

```bash
docker compose up -d --build
docker compose ps
docker compose down
```

| Порт | Контейнер |
|---|---|
| 8000 | nginx, обратный прокси |
| 8081 | web |
| 8082 | web-2 |

nginx ждёт, пока оба приложения станут healthy, и чередует запросы между ними.
Проверить:

```bash
for i in {1..4}; do curl -s http://localhost:8000/api/info | grep hostname; done
```

## Эндпоинты

| Путь | Ответ |
|---|---|
| `/` | главная страница |
| `/api/health` | `{"status": "ok"}` |
| `/api/info` | hostname, порт, версия, uptime, счётчик запросов |
