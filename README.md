# Library API

REST API для учёта книг, авторов и выдачи/возврата экземпляров в библиотеке.

## Стек

- Python 3.11, Django 5.2, Django REST Framework
- PostgreSQL
- JWT-аутентификация (djangorestframework-simplejwt)
- drf-spectacular (Swagger / OpenAPI)
- Docker / docker-compose

## Запуск

1. Скопируйте `.env.example` в `.env` и заполните значения (как минимум `SECRET_KEY`, `POSTGRES_*`).
2. Соберите и запустите контейнеры:

```bash
docker compose up --build
```

При старте контейнер `web` автоматически применяет миграции (`python manage.py migrate`)
и поднимается под gunicorn на `0.0.0.0:8000`.

3. Создайте суперпользователя (для доступа к выдаче/возврату книг):

```bash
docker compose exec web python manage.py createsuperuser
```

## Тесты

```bash
docker compose exec web python manage.py test
```

## Документация API

- Swagger UI: `GET /api/docs/`
- OpenAPI-схема: `GET /api/schema/`

## Аутентификация

```bash
curl -X POST http://localhost:8000/api/account/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

Полученный `access`-токен передавайте в заголовке:

```
Authorization: Bearer <access_token>
```

## Примеры запросов

### Список книг с поиском и фильтрами

```bash
curl "http://localhost:8000/api/books/?search=Django&available=1&ordering=title"
```

### Создание книги (только staff)

```bash
curl -X POST http://localhost:8000/api/books/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Django для профи", "authors": [1], "isbn": "978-5-00000-000-0", "total_copies": 3, "available_copies": 3}'
```

### Выдача книги (только staff)

```bash
curl -X POST http://localhost:8000/api/loans/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "reader_id": 2}'
```

### Возврат книги (только staff)

```bash
curl -X POST http://localhost:8000/api/loans/5/return/ \
  -H "Authorization: Bearer <access_token>"
```

### Просроченные выдачи (только staff)

```bash
curl "http://localhost:8000/api/loans/?overdue=1" \
  -H "Authorization: Bearer <access_token>"
```
