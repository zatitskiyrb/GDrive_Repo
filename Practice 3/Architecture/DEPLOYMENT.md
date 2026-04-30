# Deployment Architecture

**Product:** Dice Randomizer
**Environment:** Docker (локально) / любой VPS с Docker
**Last Updated:** 2026-04-30

---

## Структура деплоя

```
dice-randomizer/
├── index.html
├── style.css
├── app.js
├── assets/
│   └── roll.mp3
└── Dockerfile
```

---

## Dockerfile

```dockerfile
FROM nginx:1.25-alpine
COPY . /usr/share/nginx/html
EXPOSE 80
```

- Базовый образ: `nginx:1.25-alpine` (~8 MB)
- Копирует всю статику в корень nginx
- Порт 80 внутри контейнера

---

## Деплой через Docker

### Сборка образа

```bash
docker build -t dice-randomizer .
```

### Запуск контейнера

```bash
docker run -p 8080:80 dice-randomizer
```

### Открыть в браузере

```
http://localhost:8080
```

### Остановка

```bash
docker stop $(docker ps -q --filter ancestor=dice-randomizer)
```

### Альтернативный порт (если 8080 занят)

```bash
docker run -p 3000:80 dice-randomizer
# открыть: http://localhost:3000
```

---

## Локальный запуск (без Docker)

Открыть файл напрямую в браузере:

```bash
open index.html          # macOS
start index.html         # Windows
xdg-open index.html      # Linux
```

> **Ограничение:** некоторые браузеры блокируют `Audio()` при открытии через `file://`. Звук может не воспроизвестись. Для полноценной работы — использовать Docker.

---

## Окружения

| Окружение | Способ запуска | URL |
|---|---|---|
| Локальное (без Docker) | `open index.html` | `file:///.../index.html` |
| Локальное (Docker) | `docker run -p 8080:80` | `http://localhost:8080` |
| Production (VPS) | `docker run -p 80:80` | `http://<IP>` |

---

## Rollback

Так как нет CI/CD и нет базы данных, откат — это просто запуск предыдущей версии:

```bash
docker run -p 8080:80 dice-randomizer:previous-tag
```
