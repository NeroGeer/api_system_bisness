# Project API (FastAPI + SQLAlchemy + Redis)

Backend система управления командами, задачами, встречами и календарём с RBAC, JWT-аутентификацией и административной панелью SQLAdmin.

##  Author

- Name: NeroGeer  
- GitHub: https://github.com/NeroGeer  
- Email: nerogeerjob@gmail.com
- License: MIT  

---

##  Основной стек

- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0 (Async ORM)** — работа с БД
- **PostgreSQL** — основная база данных
- **Redis** — кеширование и ускорение запросов
- **JWT (python-jose)** — аутентификация
- **Passlib (bcrypt)** — хеширование паролей
- **SQLAdmin** — административная панель
- **Pydantic v2 + Settings** — конфигурация и валидация
- **Uvicorn** — ASGI сервер
- **Docker / Docker Compose** — деплой

---

##  Функциональность

###  Пользователи
- Регистрация / авторизация
- JWT access + refresh tokens
- Обновление профиля
- Удаление аккаунта

---

###  Команды
- Создание команд
- Инвайт по коду
- Управление ролями (owner / manager / employee)
- Добавление и удаление участников

---

###  Задачи
- CRUD задач
- Назначение исполнителей
- Статусы задач (open / work / closed)
- Оценка (grade)
- Фильтрация по датам и исполнителю

---

###  Встречи
- Создание встреч
- Добавление участников
- Проверка конфликтов расписания
- Обновление времени и участников
- Удаление встреч и участников

---

###  Комментарии к задачам
- Создание / обновление / удаление комментариев
- Redis кеширование комментариев
- Инвалидация кеша при изменениях

---

###  Календарь
- Объединённое представление:
  - задачи
  - встречи
- Фильтрация по диапазону дат
- Группировка по дням

---

###  RBAC (Role Based Access Control)
- Roles
- Permissions system
- Team-based access control
- Task executor checks

---

###  JWT система
- Access token
- Refresh token rotation
- Blacklist/DB storage refresh tokens
- Expiration control

---

###  Redis caching
- Кеш комментариев задач
- TTL (например 300s)
- Автоматическая инвалидация при изменениях

---

### Admin panel (SQLAdmin)
- Управление пользователями
- Управление ролями
- Управление задачами и командами
- Просмотр данных БД

---

##  Конфигурация

Все настройки задаются через `.env`

---

## Запуск проекта

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск через Docker
```bash
docker-compose up --build
```

## API документация
- http://localhost:8000/docs

## Архитектура проекта
- src/
  -  ├── core/          # security, jwt, rbac
  -  ├── database/      # session, config
  -  ├── models/        # SQLAlchemy models
  -  ├── repositories/  # DB queries layer
  -  ├── services/      # business logic
  -  ├── scheme/        # pydantic schemas
  -  ├── utils/         # helpers
  -  ├── logger/        # logging setup
  -  └── route/           # routes


## Основные принципы безопасности
- Пароли хранятся только в hashed виде (bcrypt)
- JWT access + refresh separation
- Проверка ролей и прав на уровне сервисов
- Проверка принадлежности к команде
- Проверка исполнителя задач

## Особенности реализации
- Async-first архитектура
- Чистое разделение layers:
- API → Service → Repository → DB
- Redis caching layer
- SQLAlchemy 2.0 style queries
- Flexible RBAC system

## Планы развития
- WebSocket уведомления
- Celery background tasks
- Audit logs
- Rate limiting
- Full RBAC policy engine
- GraphQL layer (optional)