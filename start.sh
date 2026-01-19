#!/bin/bash

set -e  # Остановка при ошибке

echo "🚀 Starting Netflix API Application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для вывода с цветом
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Проверка переменных окружения
log_info "Checking environment variables..."
if [ -z "$DATABASE_URL" ]; then
    log_error "DATABASE_URL is not set!"
    exit 1
fi
log_info "✓ Environment variables OK"

# 2. Ожидание готовности базы данных
log_info "Waiting for PostgreSQL to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if pg_isready -h db -p 5432 -U netflix_user > /dev/null 2>&1; then
        log_info "✓ PostgreSQL is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_warn "Waiting for PostgreSQL... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    log_error "PostgreSQL is not available after $MAX_RETRIES attempts!"
    exit 1
fi

# Дополнительная пауза для стабильности
sleep 2

# 3. Проверка подключения к базе данных
log_info "Testing database connection..."
python << END
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ Database connection successful!")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)
END

if [ $? -ne 0 ]; then
    log_error "Database connection test failed!"
    exit 1
fi

# 4. Проверка существования Alembic
log_info "Checking Alembic setup..."
if [ ! -d "alembic" ]; then
    log_warn "Alembic directory not found, initializing..."
    alembic init alembic
fi

# 5. Создание начальной миграции (если не существует)
log_info "Checking for migrations..."
if [ ! "$(ls -A alembic/versions 2>/dev/null)" ]; then
    log_info "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
else
    log_info "✓ Migrations already exist"
fi

# 6. Применение миграций
log_info "Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    log_info "✓ Migrations applied successfully!"
else
    log_error "Migration failed!"
    exit 1
fi

# 7. Проверка таблиц
log_info "Verifying database tables..."
python << END
from sqlalchemy import create_engine, inspect
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"Found {len(tables)} tables:")
for table in tables:
    print(f"  - {table}")

required_tables = ['users', 'netflix_content']
missing_tables = [t for t in required_tables if t not in tables]

if missing_tables:
    print(f"✗ Missing tables: {missing_tables}")
    exit(1)
else:
    print("✓ All required tables exist!")
END

# 8. Запуск приложения
log_info "Starting Uvicorn server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log_info "Application will be available at: http://0.0.0.0:8000"
log_info "API Documentation: http://0.0.0.0:8000/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Запуск Uvicorn
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info