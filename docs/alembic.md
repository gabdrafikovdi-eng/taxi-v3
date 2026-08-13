# 🗄️ Alembic + PostgreSQL Async — универсальное руководство

Актуально для:

- Python 3.11+
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- async driver: `asyncpg` или `psycopg` 3
- локальная разработка и деплой в Docker/VPS

---

## 1. Главное правило

| Где | Что делаем |
|---|---|
| Локально | Создаём миграции, проверяем, коммитим в Git |
| CI/тесты | Прогоняем `upgrade head`, иногда `downgrade` |
| Сервер/VPS | Только применяем миграции: `alembic upgrade head` |

Никогда не создавай миграции на проде через `--autogenerate`.

---

## 2. Установка

### Вариант 1: asyncpg

```bash
uv add alembic "sqlalchemy[asyncio]" asyncpg
```

### Вариант 2: psycopg 3

```bash
uv add alembic "sqlalchemy[asyncio]" "psycopg[binary]"
```

Если не используешь `uv`, замени `uv run ...` на:

```bash
python -m alembic ...
# или
poetry run alembic ...
```

---

## 3. Формат DATABASE_URL

Для Alembic с async SQLAlchemy URL должен содержать async-драйвер.

### asyncpg

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app_db
```

### psycopg 3

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/app_db
```

Важно:

- `postgresql://` — обычный sync URL.
- `postgres://` — старый alias, лучше не использовать.
- Для Alembic и приложения лучше использовать один и тот же async-драйвер.
- Если в пароле есть спецсимволы, закодируй их в URL.

Пример:

```env
# плохо, если пароль содержит @, #, %, /
DATABASE_URL=postgresql+asyncpg://user:p@ss@localhost:5432/app_db

# правильно: пароль должен быть URL-encoded
DATABASE_URL=postgresql+asyncpg://user:p%40ss@localhost:5432/app_db
```

---

## 4. Инициализация Alembic

Из корня проекта:

```bash
uv run alembic init -t async alembic
```

Получится структура:

```text
project/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── *.py
└── app/
    ├── db/
    │   └── base.py
    └── models/
        └── *.py
```

Если у тебя уже есть папка `migrations`, можно использовать её:

```bash
uv run alembic init -t async migrations
```

Но дальше в гайде используется `alembic/`.

---

## 5. Настройка alembic.ini

После `alembic init` открой `alembic.ini`.

Минимально важные настройки:

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
truncate_slug_length = 60

# Не храни здесь пароль.
# URL берём из переменной окружения DATABASE_URL в alembic/env.py.
# sqlalchemy.url =
```

Если у тебя src-layout:

```ini
prepend_sys_path = src
```

Остальные секции логирования, которые сгенерировал Alembic, обычно можно оставить как есть.

---

## 6. Настройка alembic/env.py для async PostgreSQL

Пример универсального `alembic/env.py`.

Адаптируй импорты под свой проект:

- `app.db.base.Base`
- `app.models` — пакет, где зарегистрированы все модели

```python
from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Опционально: если используешь .env
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ВАЖНО: подгони импорты под структуру своего проекта.
from app.db.base import Base  # noqa: E402
import app.models  # noqa: F401,E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    return url


def run_migrations_offline() -> None:
    """Миграция без подключения к БД: генерация SQL."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_schemas=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = get_database_url()

    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Разбор важных моментов:

- Alembic использует async engine, но сами миграции выполняются синхронно внутри `connection.run_sync(...)`.
- `target_metadata = Base.metadata` обязателен для `--autogenerate`.
- `compare_type=True` заставляет Alembic замечать изменения типов.
- `compare_server_default=True` заставляет замечать изменения default-значений.
- `include_schemas=False` подходит для обычного `public` schema. Если используешь кастомные схемы, включи и настрой отдельно.

---

## 7. Base и naming convention

Рекомендую сразу задать naming convention для индексов и констрейнтов. Это сильно упрощает миграции и откаты.

Пример `app/db/base.py`:

```python
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```

Пример модели:

```python
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
```

Убедись, что все модели импортируются до запуска Alembic.

Например:

```python
# app/models/__init__.py
from app.models.user import User  # noqa: F401
```

Или в `alembic/env.py`:

```python
import app.models  # noqa: F401
```

---

## 8. Workflow локально

### 1. Изменил модели

Например, добавил колонку в модель.

### 2. Создал миграцию

```bash
uv run alembic revision --autogenerate -m "add users table"
```

### 3. Обязательно проверил файл миграции глазами

Autogenerate не является гарантией правильности.

Проверяй:

- нет ли лишних `DROP TABLE`, `DROP COLUMN`;
- правильно ли создаются индексы;
- не теряются ли данные;
- корректны ли типы;
- есть ли `server_default`;
- есть ли `downgrade()`.

### 4. Применил миграцию локально

```bash
uv run alembic upgrade head
```

### 5. Проверил откат

```bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

### 6. Закоммитил

```bash
git add alembic/versions/
git commit -m "feat(db): add users table"
git push
```

---

## 9. Шпаргалка команд

### Локально

| Действие | Команда |
|---|---|
| Инициализация async Alembic | `uv run alembic init -t async alembic` |
| Создать авто-миграцию | `uv run alembic revision --autogenerate -m "описание"` |
| Создать пустую миграцию | `uv run alembic revision -m "описание"` |
| Применить все миграции | `uv run alembic upgrade head` |
| Применить одну следующую | `uv run alembic upgrade +1` |
| Откатить на 1 шаг | `uv run alembic downgrade -1` |
| Откатить до ревизии | `uv run alembic downgrade <revision_id>` |
| Откатить всё | `uv run alembic downgrade base` |
| Текущая ревизия БД | `uv run alembic current` |
| История миграций | `uv run alembic history` |
| Список heads | `uv run alembic heads` |
| Объединить heads | `uv run alembic merge heads -m "merge migrations"` |
| Показать ревизию | `uv run alembic show <revision_id>` |
| Сгенерировать SQL без применения | `uv run alembic upgrade head --sql` |
| Пометить БД ревизией без миграций | `uv run alembic stamp <revision_id>` |
| Пометить как head | `uv run alembic stamp head` |
| Проверить, нужны ли новые миграции | `uv run alembic check` |

### Docker / VPS

Замени `app` на имя твоего сервиса в `docker-compose.yml`.

| Действие | Команда |
|---|---|
| Применить миграции в запущенном контейнере | `docker compose exec app uv run alembic upgrade head` |
| Применить миграции one-off командой | `docker compose run --rm app uv run alembic upgrade head` |
| Текущая ревизия | `docker compose exec app uv run alembic current` |
| История | `docker compose exec app uv run alembic history` |
| Откат на 1 шаг | `docker compose exec app uv run alembic downgrade -1` |

Если в контейнере нет `uv`, используй:

```bash
docker compose exec app alembic upgrade head
```

или:

```bash
docker compose exec app python -m alembic upgrade head
```

### Проверка через psql

Замени `db`, `app`, `app_db` на свои значения.

```bash
docker compose exec db psql -U app -d app_db -c "\dt"
```

Проверить версию Alembic:

```bash
docker compose exec db psql -U app -d app_db -c "SELECT * FROM alembic_version;"
```

---

## 10. Примеры миграций

### Пустая миграция

Создание:

```bash
uv run alembic revision -m "manual migration example"
```

Файл:

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
```

---

## 11. Добавить колонку в таблицу с данными

Плохо:

```python
op.add_column(
    "users",
    sa.Column("status", sa.String(length=20), nullable=False),
)
```

Если таблица уже содержит строки, PostgreSQL не даст добавить `NOT NULL` без значения.

Правильно:

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("status", sa.String(length=20), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET status = 'active'
            WHERE status IS NULL
            """
        )
    )

    op.alter_column(
        "users",
        "status",
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("users", "status")
```

Если нужно сразу задать server default:

```python
op.add_column(
    "users",
    sa.Column(
        "status",
        sa.String(length=20),
        nullable=True,
        server_default=sa.text("'active'"),
    ),
)
```

---

## 12. Создать таблицу

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_events_name",
        "events",
        ["name"],
    )


def downgrade() -> None:
    op.drop_index("ix_events_name", table_name="events")
    op.drop_table("events")
```

---

## 13. UUID primary key

Для PostgreSQL 13+ можно использовать `gen_random_uuid()`.

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column(
            "id",
            sa.Uuid(),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("profiles")
```

Для старых версий PostgreSQL может понадобиться расширение:

```python
op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
```

---

## 14. ENUM в PostgreSQL

### Создание ENUM

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."

user_status = sa.Enum("active", "banned", name="user_status")


def upgrade() -> None:
    user_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "status",
            user_status,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "status")
    user_status.drop(op.get_bind(), checkfirst=True)
```

### Добавить значение в ENUM

`ALTER TYPE ... ADD VALUE` часто нельзя выполнять внутри обычной транзакции.

Используй `autocommit_block`:

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            sa.text(
                "ALTER TYPE user_status ADD VALUE IF NOT EXISTS 'pending'"
            )
        )


def downgrade() -> None:
    # Удалить значение из ENUM безопасно и универсально нельзя.
    # Обычно downgrade оставляют пустым или пересоздают тип вручную.
    pass
```

---

## 15. Индекс CONCURRENTLY

Обычный `CREATE INDEX` может блокировать запись.

Для production-таблиц лучше использовать `CONCURRENTLY`.

Важно: `CONCURRENTLY` нельзя выполнять внутри обычной транзакции.

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            sa.text(
                """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_users_email
                ON users (email)
                """
            )
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute(
            sa.text(
                """
                DROP INDEX CONCURRENTLY IF EXISTS ix_users_email
                """
            )
        )
```

---

## 16. Foreign key с минимальной блокировкой

Для больших таблиц полезный паттерн:

1. Создать FK как `NOT VALID`.
2. Затем валидировать его отдельно.

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE orders
            ADD CONSTRAINT fk_orders_user_id
            FOREIGN KEY (user_id)
            REFERENCES users(id)
            NOT VALID
            """
        )
    )

    op.execute(
        sa.text(
            """
            ALTER TABLE orders
            VALIDATE CONSTRAINT fk_orders_user_id
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE orders
            DROP CONSTRAINT IF EXISTS fk_orders_user_id
            """
        )
    )
```

---

## 17. Переименование таблицы

Autogenerate может попытаться удалить старую таблицю и создать новую. Это опасно.

Для переименования лучше ручная миграция:

```python
from alembic import op

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.rename_table("old_users", "users")


def downgrade() -> None:
    op.rename_table("users", "old_users")
```

Но после переименования проверь:

- sequence;
- индексы;
- foreign keys;
- представления;
- триггеры;
- права доступа.

---

## 18. Data migration

Схема и данные лучше разделять.

Пример безопасной data-миграции:

```python
from alembic import op
import sqlalchemy as sa

revision = "..."
down_revision = "..."


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
            SET full_name = ''
            WHERE full_name IS NULL
            """
        )
    )


def downgrade() -> None:
    # Если данные невозможно безопасно вернуть, оставь pass
    # и опиши причину.
    pass
```

Для больших таблиц:

- не обновляй миллионы строк одной транзакцией;
- делай батчи;
- проверяй нагрузку;
- иногда лучше вынести data-миграцию в отдельный скрипт.

---

## 19. Существующая база и первая миграция

Если база уже существует, есть два основных пути.

### Вариант A: база уже соответствует моделям

1. Создай пустую baseline-миграцию:

```bash
uv run alembic revision -m "baseline"
```

2. Проверь, что в ней нет опасных операций.

3. Пометь базу как `head`:

```bash
uv run alembic stamp head
```

4. Дальше развивай миграции как обычно.

### Вариант B: нужно поймать diff

```bash
uv run alembic revision --autogenerate -m "initial"
```

Затем очень внимательно проверь файл.

Если Alembic предлагает удалить таблицы или колонки, которые нужны, не применяй такую миграцию.

---

## 20. alembic stamp

`stamp` меняет версию в `alembic_version`, но не применяет миграции.

Используй только когда понимаешь состояние схемы.

Примеры:

```bash
uv run alembic stamp head
uv run alembic stamp <revision_id>
uv run alembic stamp base
```

Типичные случаи:

- база уже создана вручную;
- миграция была применена частично;
- нужно синхронизировать состояние после ручных правок;
- нужно вернуть указатель на рабочую ревизию.

Опасный случай:

```bash
uv run alembic stamp head
```

Нельзя делать, если реальная схема БД не соответствует `head`.

---

## 21. Multiple heads

Если два разработчика создали миграции от одной ревизии:

```bash
uv run alembic heads
```

Ты можешь увидеть несколько heads.

Решение:

```bash
uv run alembic merge heads -m "merge migrations"
uv run alembic upgrade head
```

Если миграция ещё не была влита в основную ветку и не применялась нигде, иногда проще удалить файл миграции и создать заново после `git pull`.

---

## 22. Autogenerate: что обязательно проверять

`--autogenerate` не понимает всё.

Всегда проверяй:

- `DROP TABLE`;
- `DROP COLUMN`;
- переименования;
- изменение типов;
- изменение nullable;
- server defaults;
- индексы;
- уникальные ограничения;
- foreign keys;
- ENUM;
- кастомные типы;
- схемы, отличные от `public`;
- данные, которые могут быть потеряны.

Если Alembic хочет удалить таблицу, частая причина:

- модель не импортирована;
- модель удалена;
- используется другой `Base`;
- модель лежит в другом модуле и не зарегистрирована.

---

## 23. Что коммитить в Git

Обязательно:

```text
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/versions/*.py
```

Не коммитить:

```text
__pycache__/
*.pyc
.env
alembic/__pycache__/
alembic/versions/__pycache__/
```

Пример `.gitignore`:

```gitignore
__pycache__/
*.pyc
.env
.venv/
```

---

## 24. Docker

В Dockerfile обязательно должны попасть файлы Alembic.

Пример фрагмента:

```dockerfile
COPY alembic.ini ./
COPY alembic/ ./alembic/
```

Если используешь src-layout:

```dockerfile
COPY src/ ./src/
```

В `.dockerignore` не должно быть:

```text
alembic/
alembic.ini
```

Иначе Alembic не найдёт миграции внутри образа.

---

## 25. Деплой на VPS

Базовый workflow:

```bash
git pull
docker compose build
docker compose up -d db
docker compose run --rm app uv run alembic upgrade head
docker compose up -d
```

Если сервис уже запущен:

```bash
git pull
docker compose up -d --build
docker compose exec app uv run alembic upgrade head
```

Проверка:

```bash
docker compose exec app uv run alembic current
docker compose exec db psql -U app -d app_db -c "\dt"
docker compose exec db psql -U app -d app_db -c "SELECT * FROM alembic_version;"
```

---

## 26. Production-рекомендации

### 1. Делай backup перед опасными миграциями

```bash
pg_dump -U app -d app_db -F c -f backup.dump
```

Или через облачный backup.

### 2. Не запускай миграции одновременно из нескольких реплик

Лучше:

- отдельный migration job;
- или запускать миграции до поднятия нескольких реплик приложения;
- или использовать advisory lock, если миграции стартуют из приложения.

### 3. Используй backward-compatible миграции

Хороший порядок для zero-downtime:

1. Добавить новую колонку/таблицу.
2. Задеплоить код, который умеет работать и со старой, и с новой схемой.
3. Заполнить данные.
4. Переключить код на новую схему.
5. Удалить старое отдельной миграцией позже.

### 4. Не удаляй данные в той же миграции, где меняешь схему

Лучше разделить:

- schema migration;
- data migration;
- cleanup migration.

### 5. Проверяй миграции на копии prod-данных

Особенно если:

- таблица большая;
- есть `NOT NULL`;
- есть `CREATE INDEX`;
- есть `UPDATE`;
- есть `ALTER TABLE`;
- есть ENUM.

---

## 27. Чек-лист перед коммитом миграции

- [ ] Файл миграции создан локально.
- [ ] Проверил `upgrade()` глазами.
- [ ] Проверил `downgrade()` глазами.
- [ ] Нет случайных `DROP TABLE` / `DROP COLUMN`.
- [ ] Модели импортированы в `env.py` или `app.models`.
- [ ] `target_metadata = Base.metadata` установлен.
- [ ] Локально выполнено:

```bash
uv run alembic upgrade head
```

- [ ] Локально выполнен откат:

```bash
uv run alembic downgrade -1
uv run alembic upgrade head
```

- [ ] Миграция закоммичена:

```bash
git add alembic/versions/
git commit -m "feat(db): ..."
```

---

## 28. Чек-лист деплоя

- [ ] `git pull`
- [ ] образ собран;
- [ ] `DATABASE_URL` содержит async-драйвер;
- [ ] база доступна из контейнера приложения;
- [ ] выполнен `upgrade head`;
- [ ] `alembic current` показывает ожидаемую ревизию;
- [ ] приложение запускается;
- [ ] критичные запросы работают.

---

## 29. Экстренный откат

Если миграция сломала прод:

```bash
docker compose exec app uv run alembic downgrade -1
```

Если нужно откатить и код:

```bash
git checkout HEAD~1
docker compose up -d --build
```

Но сначала:

1. Сделай backup.
2. Пойми, какая ревизия была рабочей:

```bash
docker compose exec app uv run alembic current
docker compose exec app uv run alembic history
```

3. Если нужно вернуть указатель без изменения схемы:

```bash
docker compose exec app uv run alembic stamp <working_revision_id>
```

---

## 30. Частые проблемы

### Миграция пустая, только pass

Причина:

- `target_metadata = None`;
- модели не импортированы;
- используется не тот `Base`.

Решение:

```python
target_metadata = Base.metadata
```

И добавь импорт моделей:

```python
import app.models  # noqa: F401
```

---

### Alembic не видит alembic.ini

Запускай из корня проекта или указывай конфиг:

```bash
uv run alembic -c /path/to/alembic.ini upgrade head
```

---

### Ошибка `Target database is not up to date`

Обычно база находится не на последней ревизии.

Варианты:

```bash
uv run alembic upgrade head
```

Если схема уже соответствует `head`, но Alembic этого не знает:

```bash
uv run alembic stamp head
```

Используй `stamp` осторожно.

---

### Ошибка `Multiple head revisions are present`

Решение:

```bash
uv run alembic merge heads -m "merge migrations"
uv run alembic upgrade head
```

---

### Alembic хочет удалить таблицу

Причины:

- модель не импортирована;
- модель действительно удалена;
- другой `Base`;
- другая схема;
- опечатка в `__tablename__`.

Сначала проверь импорты моделей.

---

### Ошибка `type "xxx" already exists`

ENUM или тип уже существует.

Решение:

- используй `checkfirst=True`;
- или вручную добавь проверку;
- или исправь миграцию.

Пример:

```python
user_status.create(op.get_bind(), checkfirst=True)
```

---

### `CREATE INDEX CONCURRENTLY cannot run inside a transaction`

Используй:

```python
with op.get_context().autocommit_block():
    op.execute(...)
```

---

### `ALTER TYPE ... ADD VALUE cannot run inside a transaction`

Используй:

```python
with op.get_context().autocommit_block():
    op.execute(...)
```

---

### Ошибка подключения к БД

Проверь:

- `DATABASE_URL`;
- хост;
- порт;
- пользователя;
- пароль;
- имя базы;
- доступ из Docker-сети;
- async-драйвер в URL.

Для Docker важно использовать имя сервиса БД как хост.

Пример:

```env
DATABASE_URL=postgresql+asyncpg://app:password@db:5432/app_db
```

А не:

```env
DATABASE_URL=postgresql+asyncpg://app:password@localhost:5432/app_db
```

если приложение работает внутри Docker.

---

### Ошибка `MissingGreenlet`

Обычно связана с async SQLAlchemy.

Проверь, что установлены:

```bash
uv add "sqlalchemy[asyncio]" greenlet
```

И что используется корректный async URL.

---

### В Docker ошибка `No such file or directory: alembic.ini`

В Dockerfile не скопированы файлы Alembic.

Добавь:

```dockerfile
COPY alembic.ini ./
COPY alembic/ ./alembic/
```

Проверь `.dockerignore`.

---

### После ручных правок БД Alembic думает, что миграции не применены

Если реальная схема соответствует ревизии, но запись в `alembic_version` потеряна:

```bash
uv run alembic stamp <revision_id>
```

Если не уверен, не делай `stamp head`.

---

## 31. Ограничения autogenerate

Autogenerate хорошо замечает:

- новые таблицы;
- новые колонки;
- удалённые колонки;
- изменение nullable;
- индексы;
- unique constraints;
- foreign keys;
- некоторые изменения типов.

Но плохо или неоднозначно обрабатывает:

- переименование таблиц;
- переименование колонок;
- сложные изменения типов;
- серверные defaults;
- кастомные типы;
- ENUM-изменения;
- данные;
- представления;
- триггеры;
- функции;
- extensions;
- partitioning;
- права доступа.

---

## 32. Полезные SQL-проверки

Текущая ревизия Alembic:

```sql
SELECT * FROM alembic_version;
```

Список таблиц:

```sql
\dt
```

или:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

Колонки таблицы:

```sql
\d users
```

или:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

Индексы:

```sql
\d users
```

или:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'users';
```

Constraints:

```sql
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'users'::regclass;
```

---

## 33. Рекомендуемая структура проекта

```text
project/
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 20260807_1234_add_users.py
├── app/
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   └── main.py
├── .env.example
├── pyproject.toml
└── docker-compose.yml
```

---

## 34. Минимальный production-процесс

### Разработка

```bash
uv run alembic revision --autogenerate -m "change"
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic upgrade head
git add alembic/versions/
git commit -m "feat(db): change"
```

### CI

```bash
uv run alembic upgrade head
uv run alembic check
```

### Deploy

```bash
git pull
docker compose build
docker compose up -d db
docker compose run --rm app uv run alembic upgrade head
docker compose up -d
```

---

## 35. Когда использовать ручную миграцию

Используй ручную миграцию, если:

- переименовываешь таблицу;
- переименовываешь колонку;
- добавляешь `CONCURRENTLY` индекс;
- меняешь ENUM;
- добавляешь extension;
- пишешь сложную data migration;
- работаешь с большой таблицей;
- нужно минимизировать блокировки;
- autogenerate предлагает опасный diff.

Создание:

```bash
uv run alembic revision -m "manual: safe index"
```

---

## 36. Безопасность

Не хранить:

- пароли;
- токены;
- production credentials;
- секреты инфраструктуры;

в файлах:

```text
alembic.ini
alembic/env.py
alembic/versions/*.py
docker-compose.yml
Dockerfile
```

Используй:

- `.env` локально;
- secrets manager на сервере;
- CI/CD variables;
- Docker secrets или environment variables.

`.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app_db
```

---

## 37. Быстрый старт для нового проекта

```bash
uv add alembic "sqlalchemy[asyncio]" asyncpg
uv run alembic init -t async alembic
```

Настроить:

```text
alembic.ini
alembic/env.py
app/db/base.py
app/models/__init__.py
```

Создать `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/app_db
```

Создать первую миграцию:

```bash
uv run alembic revision --autogenerate -m "initial"
```

Проверить файл миграции.

Применить:

```bash
uv run alembic upgrade head
```

Проверить:

```bash
uv run alembic current
```

---

## 38. Официальная документация

- Alembic: https://alembic.sqlalchemy.org/en/latest/
- Alembic tutorial: https://alembic.sqlalchemy.org/en/latest/tutorial.html
- Autogenerate: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
- Alembic cookbook: https://alembic.sqlalchemy.org/en/latest/cookbook.html
- SQLAlchemy async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- PostgreSQL ALTER TABLE: https://www.postgresql.org/docs/current/sql-altertable.html
- PostgreSQL CREATE INDEX: https://www.postgresql.org/docs/current/sql-createindex.html