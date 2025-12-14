# Auth Service

Микросервис аутентификации и управления пользователями на базе FastAPI и PostgreSQL.

## Структура проекта

```
auth/
├── main.py              # FastAPI приложение
├── models/
│   └── models.py        # SQLAlchemy модели
├── schemas.py           # Pydantic схемы
├── auth.py              # Логика аутентификации
├── database.py          # Подключение к БД
├── config.py            # Конфигурация
├── requirements.txt     # Зависимости
├── .env                 # Переменные окружения
└── Dockerfile           # Docker образ
```

## API Endpoints

### Аутентификация

- `POST /auth/login` - Вход (возвращает access и refresh токены)
- `POST /auth/refresh` - Обновление access токена
- `POST /auth/logout` - Выход (отзыв refresh токена)

### Управление пользователями

- `POST /auth/users` - Создание пользователя
- `GET /auth/users/{id}` - Получение пользователя по ID
- `PUT /auth/users/{id}` - Обновление пользователя
- `DELETE /auth/users/{id}` - Удаление пользователя

### Роли

- `GET /auth/roles` - Список доступных ролей (ADMIN, MANAGER, USER)

## Модель пользователя

```json
{
  "id": "UUID",
  "email": "string",
  "passwordHash": "string",
  "role": "ADMIN | MANAGER | USER",
  "createdAt": "timestamp"
}
```

## Запуск

### С помощью Docker Compose

```bash
docker-compose up --build
```

Сервис будет доступен по адресу: `http://localhost:8000`

### Документация API

После запуска документация доступна по адресу:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Переменные окружения

- `DATABASE_URL` - URL подключения к PostgreSQL
- `SECRET_KEY` - Секретный ключ для JWT (минимум 32 символа)
- `ALGORITHM` - Алгоритм шифрования (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Время жизни access токена (30 минут)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Время жизни refresh токена (7 дней)

## База данных

PostgreSQL 15 с автоматическим созданием таблиц при старте приложения:
- `users` - Пользователи
- `refresh_tokens` - Refresh токены

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены для аутентификации
- Refresh токены хранятся в БД и могут быть отозваны
- Валидация email и пароля
