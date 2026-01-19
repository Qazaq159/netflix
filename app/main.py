from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers import auth, netflix
from app.services.data_loader import load_netflix_data_from_csv, get_statistics, get_unique_values
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# НЕ создаем таблицы вручную - это делает Alembic!
# Base.metadata.create_all(bind=engine)  <-- УДАЛИТЬ ЭТУ СТРОКУ

app = FastAPI(
    title="Netflix Content API",
    description="""
    REST API для работы с базой данных Netflix контента

    ## Возможности:

    * **Аутентификация**: Регистрация и вход пользователей с JWT токенами
    * **Поиск**: Универсальный поиск по названию, режиссеру, актерам и описанию
    * **Фильтры**: Фильтрация по типу, рейтингу, году, стране и категории
    * **Статистика**: Детальная статистика по рейтингам и категориям
    * **Загрузка данных**: Импорт данных из CSV файла

    ## Использование:

    1. Зарегистрируйтесь: `POST /auth/register`
    2. Войдите: `POST /auth/login` (получите токен)
    3. Используйте токен в заголовке: `Authorization: Bearer <token>`
    4. Загрузите данные: `POST /load-data`
    5. Используйте API для поиска и фильтрации контента
    """,
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(netflix.router)


@app.get("/")
async def root():
    """Корневой endpoint с информацией об API"""
    return {
        "message": "Netflix Content REST API",
        "version": "1.0.0",
        "documentation": "/docs",
        "endpoints": {
            "auth": {
                "register": "POST /auth/register",
                "login": "POST /auth/login",
                "me": "GET /auth/me"
            },
            "content": {
                "list": "GET /content/",
                "get_by_id": "GET /content/{id}",
                "search": "GET /content/search/query",
                "by_rating": "GET /content/by-rating/{rating}",
                "by_category": "GET /content/by-category/{category}",
                "filters": {
                    "ratings": "GET /content/filters/ratings",
                    "categories": "GET /content/filters/categories",
                    "countries": "GET /content/filters/countries"
                },
                "stats": "GET /content/stats/overview"
            },
            "admin": {
                "load_data": "POST /load-data",
                "stats": "GET /stats"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy"}


@app.post("/load-data")
async def load_data(
        csv_path: str = "/app/data/netflix.csv",
        db: Session = Depends(get_db)
):
    """
    Загрузка данных из CSV файла в базу данных

    Это одноразовая операция для заполнения базы данных.
    Данные читаются с помощью pandas, обрабатываются и загружаются в PostgreSQL.

    **Параметры:**
    - **csv_path**: Путь к CSV файлу (по умолчанию: /app/data/netflix.csv)

    **Возвращает:**
    - Статус операции
    - Количество обработанных записей
    - Детальную статистику базы данных
    """
    try:
        result = load_netflix_data_from_csv(db, csv_path)
        return result
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке данных: {str(e)}"
        )


@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """
    Получение общей статистики базы данных (публичный endpoint)

    Возвращает:
    - Общее количество контента
    - Количество фильмов
    - Количество сериалов
    - Статистику по рейтингам
    - Статистику по категориям (топ 20)
    """
    try:
        stats = get_statistics(db)
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


@app.get("/filters")
async def get_filters(db: Session = Depends(get_db)):
    """
    Получение всех доступных значений для фильтров (публичный endpoint)

    Возвращает уникальные значения для:
    - Рейтингов
    - Стран
    - Категорий
    """
    try:
        filters = get_unique_values(db)
        return filters
    except Exception as e:
        logger.error(f"Ошибка при получении фильтров: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при получении фильтров: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
