from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from app.core.database import get_db
from app.models.netflix import NetflixContent
from app.models.user import User
from app.schemas.netflix import (
    NetflixContentResponse,
    NetflixContentFilter,
    ContentStats,
    RatingStats,
    CategoryStats
)
from app.routers.auth import get_current_user

router = APIRouter(prefix="/content", tags=["Netflix Контент"])


@router.get("/", response_model=List[NetflixContentResponse])
async def get_content(
        type: Optional[str] = Query(None, description="Фильтр по типу: Movie или TV Show"),
        rating: Optional[str] = Query(None, description="Фильтр по рейтингу (напр. TV-MA, PG, R)"),
        release_year: Optional[int] = Query(None, description="Фильтр по году выпуска"),
        country: Optional[str] = Query(None, description="Фильтр по стране"),
        category: Optional[str] = Query(None, description="Фильтр по категории/жанру"),
        title: Optional[str] = Query(None, description="Поиск по названию"),
        director: Optional[str] = Query(None, description="Поиск по режиссеру"),
        cast: Optional[str] = Query(None, description="Поиск по актерам"),
        limit: int = Query(20, ge=1, le=100, description="Количество результатов"),
        offset: int = Query(0, ge=0, description="Смещение для пагинации"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получение контента с фильтрами

    Требуется авторизация
    """
    query = db.query(NetflixContent)

    # Применение фильтров
    if type:
        query = query.filter(NetflixContent.type == type)

    if rating:
        query = query.filter(NetflixContent.rating == rating)

    if release_year:
        query = query.filter(NetflixContent.release_year == release_year)

    if country:
        query = query.filter(NetflixContent.country.ilike(f"%{country}%"))

    if category:
        query = query.filter(NetflixContent.listed_in.ilike(f"%{category}%"))

    if title:
        query = query.filter(NetflixContent.title.ilike(f"%{title}%"))

    if director:
        query = query.filter(NetflixContent.director.ilike(f"%{director}%"))

    if cast:
        query = query.filter(NetflixContent.cast.ilike(f"%{cast}%"))

    # Применение пагинации
    results = query.offset(offset).limit(limit).all()

    return results


@router.get("/{content_id}", response_model=NetflixContentResponse)
async def get_content_by_id(
        content_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение контента по ID"""
    content = db.query(NetflixContent).filter(NetflixContent.id == content_id).first()

    if not content:
        raise HTTPException(status_code=404, detail="Контент не найден")

    return content


@router.get("/search/query", response_model=List[NetflixContentResponse])
async def search_content(
        q: str = Query(..., min_length=1, description="Поисковый запрос"),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Универсальный поиск по названию, режиссеру, актерам и описанию

    Требуется авторизация
    """
    search_pattern = f"%{q}%"

    query = db.query(NetflixContent).filter(
        or_(
            NetflixContent.title.ilike(search_pattern),
            NetflixContent.director.ilike(search_pattern),
            NetflixContent.cast.ilike(search_pattern),
            NetflixContent.description.ilike(search_pattern)
        )
    )

    results = query.offset(offset).limit(limit).all()

    return results


@router.get("/filters/ratings", response_model=List[str])
async def get_all_ratings(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение всех уникальных рейтингов"""
    ratings = db.query(NetflixContent.rating).distinct().filter(
        NetflixContent.rating != ''
    ).all()
    return sorted([r[0] for r in ratings if r[0]])


@router.get("/filters/categories", response_model=List[str])
async def get_all_categories(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение всех уникальных категорий/жанров"""
    genres_query = db.query(NetflixContent.listed_in).filter(
        NetflixContent.listed_in != ''
    ).all()

    genres_set = set()
    for genre_row in genres_query:
        if genre_row[0]:
            for genre in genre_row[0].split(','):
                genres_set.add(genre.strip())

    return sorted(list(genres_set))


@router.get("/filters/countries", response_model=List[str])
async def get_all_countries(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение всех уникальных стран"""
    countries_query = db.query(NetflixContent.country).filter(
        NetflixContent.country != ''
    ).distinct().all()

    countries_set = set()
    for country_row in countries_query:
        if country_row[0]:
            for country in country_row[0].split(','):
                countries_set.add(country.strip())

    return sorted(list(countries_set))


@router.get("/stats/overview", response_model=ContentStats)
async def get_statistics(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Получение детальной статистики базы данных

    Включает:
    - Общее количество контента
    - Количество фильмов и сериалов
    - Разбивка по рейтингам
    - Разбивка по категориям (топ 20)
    """
    # Общие счетчики
    total_count = db.query(NetflixContent).count()
    movie_count = db.query(NetflixContent).filter(NetflixContent.type == 'Movie').count()
    tv_show_count = db.query(NetflixContent).filter(NetflixContent.type == 'TV Show').count()

    # Статистика по рейтингам
    rating_stats = db.query(
        NetflixContent.rating,
        func.count(NetflixContent.id).label('count')
    ).filter(
        NetflixContent.rating != ''
    ).group_by(
        NetflixContent.rating
    ).order_by(
        func.count(NetflixContent.id).desc()
    ).all()

    # Статистика по категориям
    genres_query = db.query(NetflixContent.listed_in).filter(
        NetflixContent.listed_in != ''
    ).all()

    category_counts = {}
    for row in genres_query:
        if row[0]:
            categories = [cat.strip() for cat in row[0].split(',')]
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1

    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "total_content": total_count,
        "movies": movie_count,
        "tv_shows": tv_show_count,
        "by_rating": [
            {"rating": rating, "count": count}
            for rating, count in rating_stats
        ],
        "by_category": [
            {"category": category, "count": count}
            for category, count in sorted_categories
        ]
    }


@router.get("/by-rating/{rating}", response_model=List[NetflixContentResponse])
async def get_content_by_rating(
        rating: str,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение контента по конкретному рейтингу"""
    query = db.query(NetflixContent).filter(NetflixContent.rating == rating)
    results = query.offset(offset).limit(limit).all()
    return results


@router.get("/by-category/{category}", response_model=List[NetflixContentResponse])
async def get_content_by_category(
        category: str,
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получение контента по конкретной категории"""
    query = db.query(NetflixContent).filter(NetflixContent.listed_in.ilike(f"%{category}%"))
    results = query.offset(offset).limit(limit).all()
    return results
