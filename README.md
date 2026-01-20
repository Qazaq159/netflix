# 🎬 Netflix API Application

Полнофункциональное REST API приложение для работы с каталогом контента Netflix, построенное на FastAPI с аутентификацией, фильтрацией и поиском.

---

## 📋 Содержание

- [Требования](#требования)
- [Getting started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Примеры использования](#примеры-использования)
- [Аутентификация](#аутентификация)
- [Тестирование](#тестирование)

---

<a id="требования"></a>
## 📦 Требования

- **Python**: 3.13+
- **PostgreSQL**: 12+
- **Docker**

---
<a id="getting-started"></a>
## 🚀 Установка

Самый простой способ запустить приложение с базой данных:

# 1. Клонируйте репозиторий
```
git clone https://github.com/Qazaq159/netflix.git
cd netflix
```
# 2. Создайте .env файл (или используйте существующий)
```
cat > .env << EOF
DATABASE_URL=postgresql://netflix_user:netflix_password@db:5432/netflix_db
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
```

# 3. Запустите Docker Compose
```
docker-compose up -d
```
# 4. Проверьте логи
```
docker-compose logs -f web
```
✅ Приложение будет доступно по адресу: **http://localhost:8000**

---

## 📂 Структура проекта
```

netflix/
├── app/
│   ├── core/               # Конфигурация и утилиты
│   ├── models/             # SQLAlchemy модели БД
│   ├── routers/            # API endpoints
│   ├── schemas/            # Pydantic схемы валидации
│   ├── services/           # Бизнес логика
│   └── main.py             # Точка входа
├── alembic/                # Миграции БД
├── data/                   # CSV данные
├── docker-compose.yml      # Docker конфигурация
├── Dockerfile              # Docker образ
├── requirements.txt        # Зависимости Python
├── .env                    # Переменные окружения
└── start.sh                # Скрипт запуска
```
---

<a id="api-endpoints"></a>
## 🎯 API Endpoints

### 📋 Общая информация

| Метод | Endpoint | Описание | Авторизация |
|-------|----------|---------|------------|
| GET | `/` | Проверка работоспособности | ❌ |
| GET | `/health` | Health check | ❌ |
| GET | `/stats` | Общая статистика | ❌ |
| GET | `/filters` | Доступные фильтры | ❌ |

### 🔐 Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/auth/register` | Регистрация пользователя |
| POST | `/auth/login` | Вход в систему (получение токена) |
| GET | `/auth/me` | Информация о текущем пользователе |

### 🎬 Контент

| Метод | Endpoint | Описание | Авторизация |
|-------|----------|---------|------------|
| GET | `/content/` | Получить контент с фильтрацией | ✅ |
| GET | `/content/{id}` | Получить контент по ID | ✅ |
| GET | `/content/search/query` | Поиск по ключевому слову | ✅ |
| GET | `/content/by-rating/{rating}` | Поиск по рейтингу | ✅ |
| GET | `/content/by-category/{category}` | Поиск по категории | ✅ |
| GET | `/content/filters/ratings` | Доступные рейтинги | ✅ |
| GET | `/content/filters/categories` | Доступные категории | ✅ |
| GET | `/content/filters/countries` | Доступные страны | ✅ |
| GET | `/content/stats/overview` | Статистика контента | ✅ |

### 📥 Загрузка данных

| Метод | Endpoint | Описание |
|-------|----------|---------|
| POST | `/load-data` | Загрузить CSV файл |

---
<a id="примеры-использования"></a>
## 💡 Примеры использования

### 1️⃣ Регистрация и вход

**Регистрация:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
  }'
```
**Ответ:**
```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true
}
```
**Вход и получение токена:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```
**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```
### 2️⃣ Сохранение токена в переменную

**Linux/Mac:**
```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123" | jq -r '.access_token')
```
```bash
echo $TOKEN
```

**PowerShell (Windows):**
```powershell
$response = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post `
  -Body @{username="testuser";password="testpass123"} `
  -ContentType "application/x-www-form-urlencoded"

$TOKEN = $response.access_token
echo $TOKEN
```
### 3️⃣ Получение контента

**Первые 10 записей:**
```bash
curl -X GET "http://localhost:8000/content/?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
**Все фильмы:**
```bash
curl -X GET "http://localhost:8000/content/?type=Movie&limit=20" \
  -H "Authorization: Bearer $TOKEN"
```
**Фильмы 2019 года с рейтингом R:**
```bash
curl -X GET "http://localhost:8000/content/?type=Movie&rating=R&release_year=2019&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
### 4️⃣ Поиск

**По названию:**
```bash
curl -X GET "http://localhost:8000/content/?title=Stranger&limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
**По ключевому слову:**
```bash
curl -X GET "http://localhost:8000/content/search/query?q=Matrix&limit=5" \
  -H "Authorization: Bearer $TOKEN"
```
**По рейтингу:**
```bash
curl -X GET "http://localhost:8000/content/by-rating/TV-MA?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
**По категории:**
```bash
curl -X GET "http://localhost:8000/content/by-category/Action?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```
### 5️⃣ Загрузка данных
```bash
curl -X POST "http://localhost:8000/load-data?csv_path=/app/data/netflix.csv"
```
**Ответ (займет 15-30 секунд):**
```json
{
  "status": "success",
  "records_processed": 6235,
  "records_inserted": 6235,
  "records_updated": 0,
  "records_skipped": 0,
  "statistics": {
    "total_content": 6235,
    "movies": 4265,
    "tv_shows": 1970
  }
}
```
---
<a id="аутентификация"></a>
## 🔐 Аутентификация

Приложение использует **JWT (JSON Web Tokens)** для аутентификации:

1. **Регистрация** → Создание новой учетной записи
2. **Вход** → Получение access token
3. **Запросы** → Передача токена в заголовке `Authorization: Bearer <token>`

### Формат Authorization заголовка:
```

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
⚠️ **Важно**: Большинство endpoints требуют авторизацию (исключение: `/`, `/health`, `/stats`, `/filters`)

---
<a id="тестирование"></a>
## 🧪 Тестирование

### Проверка работоспособности
```bash
# Health check
curl http://localhost:8000/health

# Получить статистику
curl http://localhost:8000/stats

# Получить доступные фильтры
curl http://localhost:8000/filters
```
### Тестирование ошибок

**Без токена (должна вернуть 401):**
```bash
curl -X GET "http://localhost:8000/content/" -v
```
**Неверный пароль (должна вернуть 401):**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=wrongpassword"
```
**Несуществующий контент (должна вернуть 404):**
```bash
curl -X GET "http://localhost:8000/content/999999" \
  -H "Authorization: Bearer $TOKEN"
```
### Интерактивная документация

Приложение автоматически генерирует документацию:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛠️ Управление базой данных
### Применение миграций
```bash
alembic upgrade head
```
---

## 📊 Docker команды

### Запуск контейнеров
```bash
docker-compose up -d
```
### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Только приложение
docker-compose logs -f web

# Только база данных
docker-compose logs -f db
```
### Остановка контейнеров
```bash
docker-compose down
```
### Удаление всех данных
```bash
docker-compose down -v
```
---

## 🔧 Решение проблем

### Ошибка подключения к БД
```bash
# Проверьте, запущен ли PostgreSQL
docker-compose logs db

# Перезагрузите контейнер
docker-compose restart db
```
### Ошибка миграции
```bash
# Просмотрите статус миграций
alembic current

# Примените все миграции
alembic upgrade head
```
### Ошибка порта

Если порт 8000 или 5432 занят:
```bash
# Измените порты в docker-compose.yml
ports:
  - "8001:8000"  # Новый порт
```
---

## 📝 Переменные фильтрации

### Допустимые рейтинги

- `TV-MA`, `TV-14`, `TV-PG`, `R`, `PG-13`, `PG`, `G`, `NC-17`

### Популярные категории

- `Action`, `Comedies`, `Documentaries`, `Dramas`, `Horror`, `Romance`, `Thriller`, `Animation`

### Параметры пагинации

- `limit`: количество результатов (по умолчанию: 10, максимум: 100)
- `offset`: смещение от начала (для страницы 2: offset=20 при limit=10)

## 📞 Поддержка

Для вопросов и проблем обратитесь к разработчику<br>
telegram: @tischtennisspiele

---

**Версия**: 1.0  
**Последнее обновление**: 2025-01-19
