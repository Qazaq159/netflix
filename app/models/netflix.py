from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class NetflixContent(Base):
    """
    Модель для контента Netflix
    Название колонок совпадает с CSV файлом
    """
    __tablename__ = "netflix_content"

    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(String, unique=True, index=True, nullable=False)  # Строковое поле для внешнего ID
    type = Column(String, index=True)  # Movie или TV Show
    title = Column(String, index=True)
    director = Column(Text)
    cast = Column(Text)
    country = Column(String)
    date_added = Column(String)
    release_year = Column(Integer, index=True)
    rating = Column(String, index=True)  # Рейтинг: TV-MA, PG, R и т.д.
    duration = Column(String)
    listed_in = Column(Text, index=True)  # Категории/Жанры
    description = Column(Text)
