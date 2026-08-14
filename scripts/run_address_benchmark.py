"""Автоматический бенчмарк адресной воронки (AddressService + AddressRepository) на реальной БД taxi-db.

Прогоняет матрицу тест-кейсов через ``AddressService.resolve_address`` (каждый вызов
идёт через реальный SQLAlchemy/asyncpg-запрос: town -> district -> street
exact/synonym/fuzzy -> house -> landmark) и печатает красивый консольный отчёт:

    * сводную таблицу (Итого пройдено / Провалено / Всего);
    * подробную таблицу по каждому тест-кейсу;
    * при наличии упавших — отдельный блок «Детали аномалий» с полными данными
      вызова и списком кандидатов, которых вернул сервис.

Скрипт ТОЛЬКО читает данные из существующей БД (taxi-db) и ничего в ней
не создаёт, не обновляет и не удаляет.

Запуск:

    python scripts/run_address_benchmark.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Позволяет импортировать app-модули при запуске как простого скрипта.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import async_session_factory  # noqa: E402
from app.repositories.address_repo import AddressRepository  # noqa: E402
from app.schemas.address import AddressInput, AddressMatchResult  # noqa: E402
from app.services.address_service import AddressService  # noqa: E402

# ---------------------------------------------------------------------------
# Матрица тест-кейсов
# ---------------------------------------------------------------------------

TEST_CASES = [

    # --- Группа 1: Уникальные улицы (Точное совпадение + Разные районы) ---
    {
        "id": 1,
        "description": "Точная улица в Центре",
        "input": {"street": "Коммунистическая"},
        "expected_status": "resolved",
        "expected_street": "Коммунистическая",
        "expected_district": "Центр",
    },
    {
        "id": 2,
        "description": "Точная улица в Южном",
        "input": {"street": "Дружбы"},
        "expected_status": "resolved",
        "expected_street": "Дружбы",
        "expected_district": "Южный",
    },
    {
        "id": 3,
        "description": "Точная улица в Восточном-1",
        "input": {"street": "Емельяна Пугачева"},
        "expected_status": "resolved",
        "expected_street": "Емельяна Пугачева",
        "expected_district": "Восточный-1",
    },
    {
        "id": 4,
        "description": "Точная улица в Восточном-2",
        "input": {"street": "Бииш Батыра"},
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 5,
        "description": "Точная улица в Северном",
        "input": {"street": "Ак Кайын"},
        "expected_status": "resolved",
        "expected_street": "Ак Кайын",
        "expected_district": "Северный",
    },
    {
        "id": 6,
        "description": "Единственная улица в Даутово",
        "input": {"street": "Мусы Гареева"},
        "expected_status": "resolved",
        "expected_street": "Мусы Гареева",
        "expected_district": "Даутово",
    },
    # --- Группа 2: Улицы-дубликаты (Ленина есть в Центре [id=364] и Восточном-1 [id=422]) ---
    {
        "id": 7,
        "description": "Улица-дубликат без района -> AMBIGUOUS",
        "input": {"street": "Ленина"},
        "expected_status": "ambiguous",
        "expected_candidates_count": 2,
    },
    {
        "id": 8,
        "description": "Улица-дубликат с указанием района 'Центр'",
        "input": {"street": "Ленина", "district": "Центр"},
        "expected_status": "resolved",
        "expected_district": "Центр",
    },
    {
        "id": 9,
        "description": "Улица-дубликат с указанием района 'Восточный-1'",
        "input": {"street": "Ленина", "district": "Восточный-1"},
        "expected_status": "resolved",
        "expected_district": "Восточный-1",
    },
    # --- Группа 3: Дома (Существующие / Несуществующие / Литеры и Дроби) ---
    {
        "id": 10,
        "description": "Улица + существующий простой дом",
        "input": {"street": "Гагарина", "house": "5"},
        "expected_status": "resolved",
        "expected_house": "5",
    },
    {
        "id": 11,
        "description": "Улица + дом с литерой (10а)",
        "input": {"street": "Ленина", "district": "Центр", "house": "10а"},
        "expected_status": "resolved",
    },
    {
        "id": 12,
        "description": "Улица + дробный номер дома (127/1)",
        "input": {"street": "Ленина", "district": "Центр", "house": "127/1"},
        "expected_status": "resolved",
    },
    {
        "id": 13,
        "description": "Ленина 13: есть в Центре, НЕТ в Восточном-1 -> Должен быть RESOLVED в Центр!",
        "input": {"street": "Ленина", "house": "13"},
        "expected_status": "resolved",
        "expected_district": "Центр",
    },
    {
        "id": 14,
        "description": "Улица с несуществующим номером дома (например, дом 999)",
        "input": {"street": "Гагарина", "house": "999"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },  # Улица должна резолвиться, но house_id=None
    # --- Группа 4: Опечатки и Fuzzy (pg_trgm) ---
    {
        "id": 15,
        "description": "Опечатка в короткой улице 'Мира' -> 'Мера'",
        "input": {"street": "Мера"},
        "expected_status": "resolved",
        "expected_street": "Мира",
    },
    {
        "id": 16,
        "description": "Опечатка в длинной национальной улице",
        "input": {"street": "Шахмуратов"},
        "expected_status": "resolved",
        "expected_street": "Шаймуратова",
    },
    {
        "id": 17,
        "description": "Опечатка с заменой и гласной и согласной",
        "input": {"street": "Гагарына"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 18,
        "description": "Пропуск дефисов и спецсимволов '70 лет октябры'",
        "input": {"street": "70 лет октябры"},
        "expected_status": "resolved",
        "expected_street": "70 лет Октября",
    },
    # --- Группа 5: Похожие названия улиц (Конфликты в одном/разных районах) ---
    {
        "id": 19,
        "description": "Почти одинаковые названия 'Шагали Шакман'",
        "input": {"street": "Шагали Шакман"},
        "expected_status": "resolved",
        "expected_street": "Шагали Шакман",
    },
    {
        "id": 20,
        "description": "Почти одинаковые названия 'Шагали Шакмана'",
        "input": {"street": "Шагали Шакмана"},
        "expected_status": "resolved",
        "expected_street": "Шагали Шакмана",
    },
    {
        "id": 21,
        "description": "Похожие цифровые улицы: '40 лет Октября' vs '70 лет Октября'",
        "input": {"street": "40 лет Октября"},
        "expected_status": "resolved",
        "expected_street": "40 лет Октября",
    },
    {
        "id": 22,
        "description": "Похожие цифровые улицы: '50 лет Победы' vs '60 лет Победы' vs '65 лет Победы'",
        "input": {"street": "60 лет Победы"},
        "expected_status": "resolved",
        "expected_street": "60 лет Победы",
    },
    # --- Группа 6: Префиксы, мусор, регистр и пробелы ---
    {
        "id": 23,
        "description": "Грязный ввод с префиксом 'ул.' и капсом",
        "input": {"street": "  УЛ. киРОВа  "},
        "expected_status": "resolved",
        "expected_street": "Кирова",
    },
    {
        "id": 24,
        "description": "Грязный ввод с префиксом 'переулок'",
        "input": {"street": "пер. Школьный"},
        "expected_status": "resolved",
    },
    {
        "id": 25,
        "description": "Улица в кавычках '\"Советская\"'",
        "input": {"street": '"Советская"'},
        "expected_status": "resolved",
        "expected_street": "Советская",
    },
    # --- Группа 7: Город по умолчанию и явные города ---
    {
        "id": 26,
        "description": "Город town=None -> подставляется Аскарово",
        "input": {"street": "Чапаева", "town": None},
        "expected_status": "resolved",
    },
    {
        "id": 27,
        "description": "Явный город 'Аскарово' в нижнем регистре",
        "input": {"street": "Чапаева", "town": "аскарово"},
        "expected_status": "resolved",
    },
    {
        "id": 28,
        "description": "Необслуживаемый город 'Уфа'",
        "input": {"town": "Уфа", "street": "Ленина"},
        "expected_status": "not_found",
        "expected_reason": "town_not_found",
    },
    # --- Группа 8: Районы с цифрами и дефисами ---
    {
        "id": 29,
        "description": "Район 'Восточный-1' не должен захватывать 'Восточный-2'",
        "input": {"street": "Сафы Истамгалина", "district": "Восточный-1"},
        "expected_status": "resolved",
        "expected_district": "Восточный-1",
    },
    {
        "id": 30,
        "description": "Несуществующий район",
        "input": {"street": "Ленина", "district": "Заречный"},
        "expected_status": "not_found",
        "expected_reason": "district_not_found",
    },
    # --- Группа 9: Несуществующие сущности ---
    {
        "id": 31,
        "description": "Абсолютно вымышленная улица",
        "input": {"street": "Тверская улица"},
        "expected_status": "not_found",
        "expected_reason": "street_not_found",
    },
    {
        "id": 32,
        "description": "Бессмысленный набор букв",
        "input": {"street": "абрвалг123"},
        "expected_status": "not_found",
    },
    # --- Группа 10: Сложные составные и национальные названия ---
    {
        "id": 33,
        "description": "Название из трех слов 'Мугалляма Мирхайдарова'",
        "input": {"street": "Мугалляма Мирхайдарова"},
        "expected_status": "resolved",
        "expected_street": "Мугалляма Мирхайдарова",
    },
    {
        "id": 34,
        "description": "Национальное имя с фамилией 'Файзрахмана Хисматуллина'",
        "input": {"street": "Файзрахмана Хисматуллина"},
        "expected_status": "resolved",
        "expected_street": "Файзрахмана Хисматуллина",
    },
    {
        "id": 35,
        "description": "Название с дефисом 'Бииш Батыра'",
        "input": {"street": "Бииш Батыра"},
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
    },
    # -----------------------------------------------------------------------
    # Группа 11: Комбинации улица + район + дом
    # -----------------------------------------------------------------------
    {
        "id": 36,
        "description": "Ленина + Центр + существующий дом",
        "input": {"street": "Ленина", "district": "Центр", "house": "13"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 37,
        "description": "Ленина + Восточный-1 + дом 13",
        "input": {"street": "Ленина", "district": "Восточный-1", "house": "13"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    {
        "id": 38,
        "description": "Ленина + Центр + несуществующий дом",
        "input": {"street": "Ленина", "district": "Центр", "house": "999"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 39,
        "description": "Ленина + Центр + дом с литерой",
        "input": {"street": "Ленина", "district": "Центр", "house": "141к1"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "141к1",
    },
    {
        "id": 40,
        "description": "Ленина + Центр + дробный дом",
        "input": {"street": "Ленина", "district": "Центр", "house": "127/1"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "127/1",
    },
    # -----------------------------------------------------------------------
    # Группа 12: Грязный голосовой ввод
    # -----------------------------------------------------------------------
    {
        "id": 41,
        "description": "Улица с лишними пробелами",
        "input": {"street": "   Гагарина   "},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 42,
        "description": "Улица полностью в верхнем регистре",
        "input": {"street": "ГАГАРИНА"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 43,
        "description": "Улица в смешанном регистре",
        "input": {"street": "гАгАрИнА"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 44,
        "description": "Улица в одинарных кавычках",
        "input": {"street": "'Гагарина'"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 45,
        "description": "Улица с префиксом 'ул' без точки",
        "input": {"street": "ул Гагарина"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 46,
        "description": "Улица с полным префиксом",
        "input": {"street": "улица Гагарина"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 47,
        "description": "Префикс + регистр + лишние пробелы",
        "input": {"street": "  УЛ.   гАгАрИнА  "},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    # -----------------------------------------------------------------------
    # Группа 13: Район в разных формах
    # -----------------------------------------------------------------------
    {
        "id": 48,
        "description": "Район в нижнем регистре",
        "input": {"street": "Ленина", "district": "центр"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 49,
        "description": "Район в верхнем регистре",
        "input": {"street": "Ленина", "district": "ЦЕНТР"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 50,
        "description": "Район с лишними пробелами",
        "input": {"street": "Ленина", "district": "  Центр  "},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 51,
        "description": "Восточный-1 в верхнем регистре",
        "input": {"street": "Ленина", "district": "ВОСТОЧНЫЙ-1"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    # -----------------------------------------------------------------------
    # Группа 14: Комбинация грязного ввода + район + дом
    # -----------------------------------------------------------------------
    {
        "id": 53,
        "description": "Грязная улица + грязный район + дом",
        "input": {
            "street": "  УЛ. лЕНИНА  ",
            "district": "  цЕНТР  ",
            "house": " 13 ",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 54,
        "description": "Грязный ввод Ленина + Восточный-1",
        "input": {
            "street": " УЛ. ЛЕНИНА ",
            "district": "ВОСТОЧНЫЙ-1",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    {
        "id": 55,
        "description": "Грязный ввод Гагарина + дом",
        "input": {
            "street": "  гАГАРИНА ",
            "house": " 5 ",
        },
        "expected_status": "resolved",
        "expected_street": "Гагарина",
        "expected_house": "5",
    },
    # -----------------------------------------------------------------------
    # Группа 15: Fuzzy + район
    # -----------------------------------------------------------------------
    {
        "id": 56,
        "description": "Опечатка Гагарина + Центр",
        "input": {"street": "Гагарына", "district": "Центр"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
        "expected_district": "Центр",
    },
    {
        "id": 57,
        "description": "Опечатка Гагарина + дом",
        "input": {"street": "Гагарына", "house": "5"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
        "expected_house": "5",
    },
    {
        "id": 58,
        "description": "Опечатка Гагарина + район + дом",
        "input": {
            "street": "Гагарына",
            "district": "Центр",
            "house": "5",
        },
        "expected_status": "resolved",
        "expected_street": "Гагарина",
        "expected_district": "Центр",
        "expected_house": "5",
    },
    {
        "id": 59,
        "description": "Опечатка Шаймуратова",
        "input": {"street": "Шахмуратов", "district": "Центр"},
        "expected_status": "resolved",
        "expected_street": "Шаймуратова",
        "expected_district": "Центр",
    },
    # -----------------------------------------------------------------------
    # Группа 16: Дубликаты + дом
    # -----------------------------------------------------------------------
    {
        "id": 60,
        "description": "Ленина без района и без дома",
        "input": {"street": "Ленина"},
        "expected_status": "ambiguous",
        "expected_candidates_count": 2,
    },
    {
        "id": 61,
        "description": "Ленина + дом 13 определяет Центр",
        "input": {"street": "Ленина", "house": "13"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 62,
        "description": "Ленина + Центр + дом 13",
        "input": {
            "street": "Ленина",
            "district": "Центр",
            "house": "13",
        },
        "expected_status": "resolved",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 63,
        "description": "Ленина + Восточный-1 + дом которого нет",
        "input": {
            "street": "Ленина",
            "district": "Восточный-1",
            "house": "999",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    # -----------------------------------------------------------------------
    # Группа 17: Полный адрес
    # -----------------------------------------------------------------------
    {
        "id": 64,
        "description": "Город + район + улица",
        "input": {
            "town": "Аскарово",
            "district": "Центр",
            "street": "Ленина",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 65,
        "description": "Город + район + улица + дом",
        "input": {
            "town": "Аскарово",
            "district": "Центр",
            "street": "Ленина",
            "house": "13",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 66,
        "description": "Полный адрес в нижнем регистре",
        "input": {
            "town": "аскарово",
            "district": "центр",
            "street": "ленина",
            "house": "13",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    {
        "id": 67,
        "description": "Полный адрес с грязным вводом",
        "input": {
            "town": "  АСКАРОВО  ",
            "district": "  ЦЕНТР  ",
            "street": "  УЛ. ЛЕНИНА  ",
            "house": " 13 ",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
        "expected_house": "13",
    },
    # -----------------------------------------------------------------------
    # Группа 18: Отсутствующие данные
    # -----------------------------------------------------------------------
    {
        "id": 68,
        "description": "Пустой AddressInput",
        "input": {},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 69,
        "description": "Только район без улицы",
        "input": {"district": "Центр"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 70,
        "description": "Только город без улицы",
        "input": {"town": "Аскарово"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 71,
        "description": "Только дом без улицы",
        "input": {"house": "13"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    # -----------------------------------------------------------------------
    # Группа 19: Негативные сценарии — защита от ложных совпадений
    # -----------------------------------------------------------------------
    {
        "id": 72,
        "description": "Полностью вымышленная длинная улица",
        "input": {"street": "Абсолютно Несуществующая Улица"},
        "expected_status": "not_found",
    },
    {
        "id": 73,
        "description": "Случайный набор букв",
        "input": {"street": "квпшрлзц"},
        "expected_status": "not_found",
    },
    {
        "id": 74,
        "description": "Случайный набор букв с цифрами",
        "input": {"street": "квпшрлзц123"},
        "expected_status": "not_found",
    },
    {
        "id": 75,
        "description": "Вымышленная улица + существующий район",
        "input": {
            "street": "Абсолютно Несуществующая",
            "district": "Центр",
        },
        "expected_status": "not_found",
    },
    {
        "id": 76,
        "description": "Вымышленная улица + дом",
        "input": {
            "street": "Абсолютно Несуществующая",
            "house": "13",
        },
        "expected_status": "not_found",
    },
    # -----------------------------------------------------------------------
    # Группа 20: Сочетание похожих названий и цифровых улиц
    # -----------------------------------------------------------------------
    {
        "id": 77,
        "description": "Точная цифровая улица с нижним регистром",
        "input": {"street": "40 лет октября"},
        "expected_status": "resolved",
        "expected_street": "40 лет Октября",
    },
    {
        "id": 78,
        "description": "Цифровая улица с лишними пробелами",
        "input": {"street": "  70 лет Октября  "},
        "expected_status": "resolved",
        "expected_street": "70 лет Октября",
    },
    {
        "id": 79,
        "description": "Цифровая улица с ошибкой в слове",
        "input": {"street": "70 лет октябры"},
        "expected_status": "resolved",
        "expected_street": "70 лет Октября",
    },
    {
        "id": 80,
        "description": "Цифровая улица + Центр",
        "input": {
            "street": "40 лет Октября",
            "district": "Центр",
        },
        "expected_status": "resolved",
        "expected_street": "40 лет Октября",
        "expected_district": "Центр",
    },
    # -----------------------------------------------------------------------
    # Группа 21: Составные национальные названия с грязным вводом
    # -----------------------------------------------------------------------
    {
        "id": 81,
        "description": "Составное название в нижнем регистре",
        "input": {"street": "мугалляма мирхайдарова"},
        "expected_status": "resolved",
        "expected_street": "Мугалляма Мирхайдарова",
    },
    {
        "id": 82,
        "description": "Составное название в верхнем регистре",
        "input": {"street": "МУГАЛЛЯМА МИРХАЙДАРОВА"},
        "expected_status": "resolved",
        "expected_street": "Мугалляма Мирхайдарова",
    },
    {
        "id": 83,
        "description": "Фамилия в нижнем регистре",
        "input": {"street": "файзрахмана хисматуллина"},
        "expected_status": "resolved",
        "expected_street": "Файзрахмана Хисматуллина",
    },
    {
        "id": 84,
        "description": "Национальное название с лишними пробелами",
        "input": {"street": "  Файзрахмана   Хисматуллина  "},
        "expected_status": "resolved",
        "expected_street": "Файзрахмана Хисматуллина",
    },
    # -----------------------------------------------------------------------
    # Группа 22: Отсутствующий город / район при существующей улице
    # -----------------------------------------------------------------------
    {
        "id": 85,
        "description": "town=None + дубликат улицы",
        "input": {
            "town": None,
            "street": "Ленина",
        },
        "expected_status": "ambiguous",
    },
    {
        "id": 86,
        "description": "town=None + район + улица",
        "input": {
            "town": None,
            "district": "Центр",
            "street": "Ленина",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 87,
        "description": "Явный город + дубликат улицы без района",
        "input": {
            "town": "Аскарово",
            "street": "Ленина",
        },
        "expected_status": "ambiguous",
    },
    {
        "id": 88,
        "description": "Явный город + район + дубликат улицы",
        "input": {
            "town": "Аскарово",
            "district": "Восточный-1",
            "street": "Ленина",
        },
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    # --- Группа 11: Реальные улица + район ---
    {
        "id": 102,
        "description": "Бииш Батыра + Восточный-2",
        "input": {"street": "Бииш Батыра", "district": "Восточный-2"},
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 103,
        "description": "Бииш Батыра + Восточный-2 в нижнем регистре",
        "input": {"street": "Бииш Батыра", "district": "восточный-2"},
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 104,
        "description": "Емельяна Пугачева + Восточный-1",
        "input": {"street": "Емельяна Пугачева", "district": "Восточный-1"},
        "expected_status": "resolved",
        "expected_street": "Емельяна Пугачева",
        "expected_district": "Восточный-1",
    },
    {
        "id": 105,
        "description": "Емельяна Пугачева + Восточный-1 в нижнем регистре",
        "input": {"street": "Емельяна Пугачева", "district": "восточный-1"},
        "expected_status": "resolved",
        "expected_street": "Емельяна Пугачева",
        "expected_district": "Восточный-1",
    },
    {
        "id": 106,
        "description": "Ак Кайын + Северный",
        "input": {"street": "Ак Кайын", "district": "Северный"},
        "expected_status": "resolved",
        "expected_street": "Ак Кайын",
        "expected_district": "Северный",
    },
    {
        "id": 107,
        "description": "Мусы Гареева + Даутово",
        "input": {"street": "Мусы Гареева", "district": "Даутово"},
        "expected_status": "resolved",
        "expected_street": "Мусы Гареева",
        "expected_district": "Даутово",
    },
    # --- Группа 12: Все формы регистра района ---
    {
        "id": 108,
        "description": "Центр в нижнем регистре",
        "input": {"street": "Коммунистическая", "district": "центр"},
        "expected_status": "resolved",
        "expected_street": "Коммунистическая",
        "expected_district": "Центр",
    },
    {
        "id": 109,
        "description": "Центр в верхнем регистре",
        "input": {"street": "Коммунистическая", "district": "ЦЕНТР"},
        "expected_status": "resolved",
        "expected_street": "Коммунистическая",
        "expected_district": "Центр",
    },
    {
        "id": 110,
        "description": "Южный в нижнем регистре",
        "input": {"street": "Дружбы", "district": "южный"},
        "expected_status": "resolved",
        "expected_street": "Дружбы",
        "expected_district": "Южный",
    },
    {
        "id": 111,
        "description": "Восточный-1 в нижнем регистре",
        "input": {"street": "Емельяна Пугачева", "district": "восточный-1"},
        "expected_status": "resolved",
        "expected_street": "Емельяна Пугачева",
        "expected_district": "Восточный-1",
    },
    {
        "id": 112,
        "description": "Восточный-2 в нижнем регистре",
        "input": {"street": "Бииш Батыра", "district": "восточный-2"},
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 113,
        "description": "Северный в нижнем регистре",
        "input": {"street": "Ак Кайын", "district": "северный"},
        "expected_status": "resolved",
        "expected_street": "Ак Кайын",
        "expected_district": "Северный",
    },
    {
        "id": 114,
        "description": "Даутово в нижнем регистре",
        "input": {"street": "Мусы Гареева", "district": "даутово"},
        "expected_status": "resolved",
        "expected_street": "Мусы Гареева",
        "expected_district": "Даутово",
    },
    # --- Группа 13: Реальные дубликаты / похожие улицы ---
    {
        "id": 49,
        "description": "60 лет Победы + Восточный-1",
        "input": {"street": "60 лет Победы", "district": "Восточный-1"},
        "expected_status": "resolved",
        "expected_street": "60 лет Победы",
        "expected_district": "Восточный-1",
    },
    {
        "id": 50,
        "description": "50 лет Победы + Восточный-2",
        "input": {"street": "50 лет Победы", "district": "Восточный-2"},
        "expected_status": "resolved",
        "expected_street": "50 лет Победы",
        "expected_district": "Восточный-2",
    },
    {
        "id": 51,
        "description": "65 лет Победы + Восточный-2",
        "input": {"street": "65 лет Победы", "district": "Восточный-2"},
        "expected_status": "resolved",
        "expected_street": "65 лет Победы",
        "expected_district": "Восточный-2",
    },
    {
        "id": 52,
        "description": "40 лет Октября + Центр",
        "input": {"street": "40 лет Октября", "district": "Центр"},
        "expected_status": "resolved",
        "expected_street": "40 лет Октября",
        "expected_district": "Центр",
    },
    {
        "id": 53,
        "description": "40 лет Победы + Южный",
        "input": {"street": "40 лет Победы", "district": "Южный"},
        "expected_status": "resolved",
        "expected_street": "40 лет Победы",
        "expected_district": "Южный",
    },
    {
        "id": 54,
        "description": "Шагали Шакман + Северный",
        "input": {"street": "Шагали Шакман", "district": "Северный"},
        "expected_status": "resolved",
        "expected_street": "Шагали Шакман",
        "expected_district": "Северный",
    },
    {
        "id": 55,
        "description": "Шагали Шакмана + Северный",
        "input": {"street": "Шагали Шакмана", "district": "Северный"},
        "expected_status": "resolved",
        "expected_street": "Шагали Шакмана",
        "expected_district": "Северный",
    },
    # --- Группа 14: Ленина — реальный duplicate-case ---
    {
        "id": 56,
        "description": "Ленина без района",
        "input": {"street": "Ленина"},
        "expected_status": "ambiguous",
        "expected_candidates_count": 2,
    },
    {
        "id": 57,
        "description": "Ленина + Центр",
        "input": {"street": "Ленина", "district": "Центр"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 58,
        "description": "Ленина + Восточный-1",
        "input": {"street": "Ленина", "district": "Восточный-1"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    {
        "id": 59,
        "description": "Ленина + Центр в нижнем регистре",
        "input": {"street": "ленина", "district": "центр"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Центр",
    },
    {
        "id": 60,
        "description": "Ленина + Восточный-1 в нижнем регистре",
        "input": {"street": "ленина", "district": "восточный-1"},
        "expected_status": "resolved",
        "expected_street": "Ленина",
        "expected_district": "Восточный-1",
    },
    # --- Группа 15: Нормализация названия улицы ---
    {
        "id": 61,
        "description": "Гагарина в нижнем регистре",
        "input": {"street": "гагарина"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 62,
        "description": "Гагарина в верхнем регистре",
        "input": {"street": "ГАГАРИНА"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 63,
        "description": "Гагарина в смешанном регистре",
        "input": {"street": "гАгАрИнА"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 64,
        "description": "Гагарина с лишними пробелами",
        "input": {"street": "   Гагарина   "},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 65,
        "description": "Кирова с префиксом ул.",
        "input": {"street": "ул. Кирова"},
        "expected_status": "resolved",
        "expected_street": "Кирова",
    },
    {
        "id": 66,
        "description": "Кирова с полным префиксом улица",
        "input": {"street": "улица Кирова"},
        "expected_status": "resolved",
        "expected_street": "Кирова",
    },
    {
        "id": 67,
        "description": "Кирова с префиксом без точки",
        "input": {"street": "ул Кирова"},
        "expected_status": "resolved",
        "expected_street": "Кирова",
    },
    {
        "id": 68,
        "description": "Гагарина в кавычках",
        "input": {"street": '"Гагарина"'},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    # --- Группа 16: Реальные fuzzy-сценарии ---
    {
        "id": 69,
        "description": "Мера -> Мира",
        "input": {"street": "Мера"},
        "expected_status": "resolved",
        "expected_street": "Мира",
    },
    {
        "id": 70,
        "description": "Гагарына -> Гагарина",
        "input": {"street": "Гагарына"},
        "expected_status": "resolved",
        "expected_street": "Гагарина",
    },
    {
        "id": 71,
        "description": "Шахмуратов -> Шаймуратова",
        "input": {"street": "Шахмуратов"},
        "expected_status": "resolved",
        "expected_street": "Шаймуратова",
    },
    {
        "id": 72,
        "description": "70 лет октябры -> 70 лет Октября",
        "input": {"street": "70 лет октябры"},
        "expected_status": "resolved",
        "expected_street": "70 лет Октября",
    },
    {
        "id": 73,
        "description": "Школьный -> Школьная",
        "input": {"street": "Школьный"},
        "expected_status": "resolved",
        "expected_street": "Школьная",
    },
    {
        "id": 74,
        "description": "пер. Школьный -> Школьная",
        "input": {"street": "пер. Школьный"},
        "expected_status": "resolved",
        "expected_street": "Школьная",
    },
    # --- Группа 17: Составные названия ---
    {
        "id": 75,
        "description": "Мугалляма Мирхайдарова в нижнем регистре",
        "input": {"street": "мугалляма мирхайдарова"},
        "expected_status": "resolved",
        "expected_street": "Мугалляма Мирхайдарова",
    },
    {
        "id": 76,
        "description": "Файзрахмана Хисматуллина в нижнем регистре",
        "input": {"street": "файзрахмана хисматуллина"},
        "expected_status": "resolved",
        "expected_street": "Файзрахмана Хисматуллина",
    },
    {
        "id": 77,
        "description": "Ахмет Заки Валиди с регистром",
        "input": {"street": "ахмет заки валиди"},
        "expected_status": "resolved",
        "expected_street": "Ахмет Заки Валиди",
    },
    {
        "id": 78,
        "description": "Мурзахана Шамсутдинова с регистром",
        "input": {"street": "МУРЗАХАНА ШАМСУТДИНОВА"},
        "expected_status": "resolved",
        "expected_street": "Мурзахана Шамсутдинова",
    },
    # --- Группа 18: Полный адрес с реальными связками ---
    {
        "id": 79,
        "description": "Аскарово + Центр + Коммунистическая",
        "input": {
            "town": "Аскарово",
            "district": "Центр",
            "street": "Коммунистическая",
        },
        "expected_status": "resolved",
        "expected_street": "Коммунистическая",
        "expected_district": "Центр",
    },
    {
        "id": 80,
        "description": "Аскарово + Южный + Дружбы",
        "input": {
            "town": "Аскарово",
            "district": "Южный",
            "street": "Дружбы",
        },
        "expected_status": "resolved",
        "expected_street": "Дружбы",
        "expected_district": "Южный",
    },
    {
        "id": 81,
        "description": "Аскарово + Восточный-2 + Бииш Батыра",
        "input": {
            "town": "Аскарово",
            "district": "Восточный-2",
            "street": "Бииш Батыра",
        },
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 82,
        "description": "Аскарово + Восточный-1 + Емельяна Пугачева",
        "input": {
            "town": "Аскарово",
            "district": "Восточный-1",
            "street": "Емельяна Пугачева",
        },
        "expected_status": "resolved",
        "expected_street": "Емельяна Пугачева",
        "expected_district": "Восточный-1",
    },
    {
        "id": 83,
        "description": "Аскарово + Северный + Ак Кайын",
        "input": {
            "town": "Аскарово",
            "district": "Северный",
            "street": "Ак Кайын",
        },
        "expected_status": "resolved",
        "expected_street": "Ак Кайын",
        "expected_district": "Северный",
    },
    {
        "id": 84,
        "description": "Аскарово + Даутово + Мусы Гареева",
        "input": {
            "town": "Аскарово",
            "district": "Даутово",
            "street": "Мусы Гареева",
        },
        "expected_status": "resolved",
        "expected_street": "Мусы Гареева",
        "expected_district": "Даутово",
    },
    # --- Группа 19: Полный адрес без явного города ---
    {
        "id": 85,
        "description": "Default town + Центр + Коммунистическая",
        "input": {
            "town": None,
            "district": "Центр",
            "street": "Коммунистическая",
        },
        "expected_status": "resolved",
        "expected_street": "Коммунистическая",
        "expected_district": "Центр",
    },
    {
        "id": 86,
        "description": "Default town + Восточный-2 + Бииш Батыра",
        "input": {
            "town": None,
            "district": "восточный-2",
            "street": "Бииш Батыра",
        },
        "expected_status": "resolved",
        "expected_street": "Бииш Батыра",
        "expected_district": "Восточный-2",
    },
    {
        "id": 87,
        "description": "Default town + Северный + Ак Кайын",
        "input": {
            "town": None,
            "district": "северный",
            "street": "Ак Кайын",
        },
        "expected_status": "resolved",
        "expected_street": "Ак Кайын",
        "expected_district": "Северный",
    },
    # --- Группа 20: Неверные комбинации улица + район ---
    {
        "id": 88,
        "description": "Бииш Батыра не существует в Центре",
        "input": {
            "street": "Бииш Батыра",
            "district": "Центр",
        },
        "expected_status": "not_found",
    },
    {
        "id": 89,
        "description": "Дружбы не существует в Восточном-1",
        "input": {
            "street": "Дружбы",
            "district": "Восточный-1",
        },
        "expected_status": "not_found",
    },
    {
        "id": 90,
        "description": "Ак Кайын не существует в Южном",
        "input": {
            "street": "Ак Кайын",
            "district": "Южный",
        },
        "expected_status": "not_found",
    },
    {
        "id": 91,
        "description": "Мусы Гареева не существует в Центре",
        "input": {
            "street": "Мусы Гареева",
            "district": "Центр",
        },
        "expected_status": "not_found",
    },
    {
        "id": 92,
        "description": "Емельяна Пугачева не существует в Восточном-2",
        "input": {
            "street": "Емельяна Пугачева",
            "district": "Восточный-2",
        },
        "expected_status": "not_found",
    },
    # --- Группа 21: Несуществующие районы ---
    {
        "id": 93,
        "description": "Несуществующий район Заречный",
        "input": {
            "street": "Коммунистическая",
            "district": "Заречный",
        },
        "expected_status": "not_found",
        "expected_reason": "district_not_found",
    },
    {
        "id": 94,
        "description": "Несуществующий район Западный",
        "input": {
            "street": "Ленина",
            "district": "Западный",
        },
        "expected_status": "not_found",
        "expected_reason": "district_not_found",
    },
    # --- Группа 22: Несуществующие улицы ---
    {
        "id": 95,
        "description": "Полностью несуществующая улица",
        "input": {"street": "Тверская"},
        "expected_status": "not_found",
        "expected_reason": "street_not_found",
    },
    {
        "id": 96,
        "description": "Случайный набор букв",
        "input": {"street": "абрвалг123"},
        "expected_status": "not_found",
    },
    {
        "id": 97,
        "description": "Несуществующая длинная улица",
        "input": {"street": "Абсолютно Несуществующая Улица"},
        "expected_status": "not_found",
    },
    # --- Группа 23: Пустые / неполные адреса ---
    {
        "id": 98,
        "description": "Полностью пустой адрес",
        "input": {},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 99,
        "description": "Только район",
        "input": {"district": "Центр"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 100,
        "description": "Только город",
        "input": {"town": "Аскарово"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
    {
        "id": 101,
        "description": "Только дом",
        "input": {"house": "13"},
        "expected_status": "not_found",
        "expected_reason": "address_and_landmark_not_found",
    },
]
# ---------------------------------------------------------------------------
# ANSI-цвета (только если вывод в терминал)
# ---------------------------------------------------------------------------

_RESET = "\033[0m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BOLD = "\033[1m"


def _use_color() -> bool:
    return sys.stdout.isatty()


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{_RESET}" if _use_color() else text


# ---------------------------------------------------------------------------
# Проверка ожиданий
# ---------------------------------------------------------------------------


def _evaluate(result: AddressMatchResult, expected: dict) -> tuple[bool, list[str]]:
    """Сверяет результат сервиса с ожиданиями. Возвращает (passed, список проблем)."""
    problems: list[str] = []
    expected_status = expected.get("expected_status")
    got_status = result.status.value

    if expected_status is not None and got_status != expected_status:
        problems.append(
            f"status: ожидалось '{expected_status}', получено '{got_status}'"
        )

    if got_status == "resolved" and result.candidates:
        top = result.candidates[0]
        for field, attr in (
            ("expected_street", "street_name"),
            ("expected_district", "district_name"),
            ("expected_house", "house_number"),
        ):
            if field in expected and getattr(top, attr) != expected[field]:
                problems.append(
                    f"{field}: ожидалось '{expected[field]}', "
                    f"получено '{getattr(top, attr)}'"
                )

    if expected_status == "ambiguous":
        expected_count = expected.get("expected_candidates_count")
        if expected_count is not None and len(result.candidates) != expected_count:
            problems.append(
                f"candidates_count: ожидалось {expected_count}, "
                f"получено {len(result.candidates)}"
            )

    if "expected_reason" in expected and result.reason != expected["expected_reason"]:
        problems.append(
            f"reason: ожидалось '{expected['expected_reason']}', "
            f"получено '{result.reason}'"
        )

    return (not problems), problems


def _top_score(result: AddressMatchResult) -> str:
    if result.candidates:
        return f"{result.candidates[0].score:.2f}"
    return "-"


# ---------------------------------------------------------------------------
# Отчёт
# ---------------------------------------------------------------------------


def _print_report(results: list[dict]) -> None:
    """Печатает сводку, подробную таблицу и блок аномалий."""
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed
    total = len(results)

    # Сводка
    print(
        _paint("\n========== БЕНЧМАРК AddressService (БД: taxi-db) ==========", _BOLD)
    )
    color = _GREEN if failed == 0 else _RED
    print(
        f"Итого пройдено: {_paint(str(passed), _GREEN)}  "
        f"провалено: {_paint(str(failed), color)}  "
        f"всего: {total}"
    )
    if total:
        print(f"Покрытие тест-кейсов: {passed / total * 100:.1f}%")
    print("=" * 75)

    # Подробная таблица
    header = (
        f"{_paint('{:<4}'.format('ID'), _BOLD)} "
        f"{_paint('{:<7}'.format('СТАТУС'), _BOLD)} "
        f"{_paint('{:<56}'.format('ОПИСАНИЕ'), _BOLD)} "
        f"{_paint('{:<28}'.format('ПОЛУЧЕНО'), _BOLD)} "
        f"{_paint('{:<24}'.format('ОЖИДАЛОСЬ'), _BOLD)}"
    )
    print(header)
    print("-" * 75)

    for r in results:
        verdict = _paint("PASSED", _GREEN) if r["passed"] else _paint("FAILED", _RED)
        got = f"status={r['got_status']} (score={r['score']})"
        exp = f"status={r['expected_status']}"
        print(f"{r['id']:<4} {verdict:<7} {r['description']:<56} {got:<28} {exp:<24}")

    # Детали аномалий
    anomalies = [r for r in results if not r["passed"]]
    if anomalies:
        print(_paint("\n=================== ДЕТАЛИ АНОМАЛИЙ ===================", _RED))
        for i, r in enumerate(anomalies, start=1):
            print(
                _paint(
                    f"\n— Аномалия {i}/{len(anomalies)}  "
                    f"[ID {r['id']}] {r['description']} —",
                    _BOLD,
                )
            )
            if r["problems"]:
                print("  Проблемы сверки:")
                for p in r["problems"]:
                    print(f"    {_paint('!', _RED)} {p}")
            print("  Входные данные вызова (AddressInput):")
            print("    " + r["input_json"].replace("\n", "\n    "))
            print("  Возвращённый сервисом AddressMatchResult:")
            print("    " + r["result_json"].replace("\n", "\n    "))
        print("=" * 75)


# ---------------------------------------------------------------------------
# Запуск
# ---------------------------------------------------------------------------


async def _main() -> int:
    async with async_session_factory() as session:
        repo = AddressRepository(session)
        service = AddressService(repo)

        results: list[dict] = []
        for case in TEST_CASES:
            case_id = case["id"]
            description = case["description"]
            raw_input = case["input"]
            expected = {
                k: v for k, v in case.items() if k not in ("id", "description", "input")
            }

            try:
                addr_input = AddressInput(**raw_input)
            except Exception as exc:  # pragma: no cover - защита от битых кейсов
                print(f"[ID {case_id}] Ошибка разбора AddressInput: {exc}")
                results.append(
                    {
                        "id": case_id,
                        "description": description,
                        "passed": False,
                        "got_status": "error",
                        "score": "-",
                        "expected_status": expected.get("expected_status", "?"),
                        "problems": [f"AddressInput parse: {exc}"],
                        "input_json": repr(raw_input),
                        "result_json": "{}",
                    }
                )
                continue

            result = await service.resolve_address(addr_input)
            passed, problems = _evaluate(result, expected)

            results.append(
                {
                    "id": case_id,
                    "description": description,
                    "passed": passed,
                    "got_status": result.status.value,
                    "score": _top_score(result),
                    "expected_status": expected.get("expected_status", "?"),
                    "problems": problems,
                    "input_json": addr_input.model_dump_json(indent=2),
                    "result_json": result.model_dump_json(indent=2),
                }
            )
            ok = _paint("OK", _GREEN) if passed else _paint("FAIL", _RED)
            print(f"→ ID {case_id:<3} {ok}  {description}")

        _print_report(results)
        return 0 if all(r["passed"] for r in results) else 1


def main() -> int:
    try:
        return asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nПрервано пользователем.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
