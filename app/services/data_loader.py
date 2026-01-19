import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.netflix import NetflixContent
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


def load_netflix_data_from_csv(db: Session, csv_path: str) -> Dict:
    """
    Загрузка данных из CSV файла в базу данных

    Args:
        db: Сессия базы данных
        csv_path: Путь к CSV файлу

    Returns:
        Словарь с результатами загрузки
    """
    try:
        # Чтение CSV с помощью pandas
        logger.info(f"Чтение файла: {csv_path}")
        df = pd.read_csv(csv_path)

        logger.info(f"Загружено строк из CSV: {len(df)}")
        logger.info(f"Колонки: {df.columns.tolist()}")

        # Обработка данных
        # Заполнение пустых значений
        df = df.fillna('')

        # Конвертация show_id в строку
        df['show_id'] = df['show_id'].astype(str)

        # Конвертация release_year в integer
        df['release_year'] = pd.to_numeric(df['release_year'], errors='coerce')
        df['release_year'] = df['release_year'].fillna(0).astype(int)

        # Очистка существующих данных (опционально)
        # db.query(NetflixContent).delete()
        # db.commit()

        records_inserted = 0
        records_updated = 0
        records_skipped = 0

        # Вставка данных батчами
        batch_size = 100
        for start_idx in range(0, len(df), batch_size):
            end_idx = min(start_idx + batch_size, len(df))
            batch = df.iloc[start_idx:end_idx]

            for _, row in batch.iterrows():
                # Проверка существования записи
                existing = db.query(NetflixContent).filter(
                    NetflixContent.show_id == row['show_id']
                ).first()

                if not existing:
                    # Создание новой записи
                    content = NetflixContent(
                        show_id=row['show_id'],
                        type=row['type'] if row['type'] else None,
                        title=row['title'] if row['title'] else None,
                        director=row['director'] if row['director'] else None,
                        cast=row['cast'] if row['cast'] else None,
                        country=row['country'] if row['country'] else None,
                        date_added=row['date_added'] if row['date_added'] else None,
                        release_year=row['release_year'] if row['release_year'] > 0 else None,
                        rating=row['rating'] if row['rating'] else None,
                        duration=row['duration'] if row['duration'] else None,
                        listed_in=row['listed_in'] if row['listed_in'] else None,
                        description=row['description'] if row['description'] else None
                    )
                    db.add(content)
                    records_inserted += 1
                else:
                    records_skipped += 1

            # Коммит батча
            db.commit()
            logger.info(f"Обработано записей: {end_idx}/{len(df)}")

        # Получение статистики
        stats = get_statistics(db)

        return {
            "status": "success",
            "records_processed": len(df),
            "records_inserted": records_inserted,
            "records_updated": records_updated,
            "records_skipped": records_skipped,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {str(e)}")
        db.rollback()
        raise e


def get_statistics(db: Session) -> Dict:
    """Получение статистики базы данных"""

    # Общее количество
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

    # Статистика по категориям (топ 20)
    # Получаем все категории
    genres_query = db.query(NetflixContent.listed_in).filter(
        NetflixContent.listed_in != ''
    ).all()

    category_counts = {}
    for row in genres_query:
        if row[0]:
            categories = [cat.strip() for cat in row[0].split(',')]
            for category in categories:
                category_counts[category] = category_counts.get(category, 0) + 1

    # Сортировка по количеству
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


def get_unique_values(db: Session) -> Dict:
    """Получение уникальных значений для фильтров"""

    # Уникальные рейтинги
    ratings = db.query(NetflixContent.rating).distinct().filter(
        NetflixContent.rating != ''
    ).all()
    ratings_list = sorted([r[0] for r in ratings if r[0]])

    # Уникальные страны
    countries_query = db.query(NetflixContent.country).filter(
        NetflixContent.country != ''
    ).distinct().all()

    countries_set = set()
    for country_row in countries_query:
        if country_row[0]:
            for country in country_row[0].split(','):
                countries_set.add(country.strip())

    # Уникальные категории
    genres_query = db.query(NetflixContent.listed_in).filter(
        NetflixContent.listed_in != ''
    ).all()

    genres_set = set()
    for genre_row in genres_query:
        if genre_row[0]:
            for genre in genre_row[0].split(','):
                genres_set.add(genre.strip())

    return {
        "ratings": ratings_list,
        "countries": sorted(list(countries_set)),
        "categories": sorted(list(genres_set))
    }
