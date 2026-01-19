from pydantic import BaseModel
from typing import Optional, List


class NetflixContentBase(BaseModel):
    """Базовая схема контента Netflix"""
    show_id: str
    type: Optional[str] = None
    title: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    country: Optional[str] = None
    date_added: Optional[str] = None
    release_year: Optional[int] = None
    rating: Optional[str] = None
    duration: Optional[str] = None
    listed_in: Optional[str] = None
    description: Optional[str] = None


class NetflixContentCreate(NetflixContentBase):
    """Схема для создания контента"""
    pass


class NetflixContentResponse(NetflixContentBase):
    """Схема ответа с ID"""
    id: int

    class Config:
        from_attributes = True


class NetflixContentFilter(BaseModel):
    """Схема для фильтрации контента"""
    type: Optional[str] = None
    rating: Optional[str] = None
    release_year: Optional[int] = None
    country: Optional[str] = None
    listed_in: Optional[str] = None
    title: Optional[str] = None
    director: Optional[str] = None
    cast: Optional[str] = None
    limit: int = 20
    offset: int = 0


class CategoryStats(BaseModel):
    """Статистика по категориям"""
    category: str
    count: int


class RatingStats(BaseModel):
    """Статистика по рейтингам"""
    rating: str
    count: int


class ContentStats(BaseModel):
    """Общая статистика"""
    total_content: int
    movies: int
    tv_shows: int
    by_rating: List[RatingStats]
    by_category: List[CategoryStats]
