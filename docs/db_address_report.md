# Отчёт по БД проекта `taxi-v3` — адресные данные

> Дата снимка: **13.08.2026**
> Назначение: полная выгрузка схемы и содержимого БД, всё, что связано с **адресами**.
> Файл передаётся другому агенту/разработчику для работы со справочником адресов без доступа к СУБД.
> Машиночитаемый полный дамп всех таблиц: [`docs/db_full_dump.json`](./db_full_dump.json)
> Полный список домов (CSV): [`docs/db_houses.csv`](./db_houses.csv)

---

## 1. Общие сведения о БД

| Параметр | Значение |
|---|---|
| СУБД | PostgreSQL 15 (alpine) — docker-контейнер `taxi-db` |
| Host / Port | `localhost` / `5432` |
| Имя БД | `taxi-db` |
| Пользователь | `taxi_user` |
| DATABASE_URL | `postgresql+asyncpg://taxi_user:***@localhost:5432/taxi-db` |
| ORM | SQLAlchemy 2.0 (async, asyncpg) — см. `app/core/database.py`, `app/core/config.py` |
| Миграции | Alembic, директория `alembic/versions/` |
| Текущая ревизия | `0ac447ef3507` (add table waypoints; таблица `alembic_version`) |

`.env` (адрес/пользователь; пароль опущен):
```
POSTGRES_USER=taxi_user
POSTGRES_PASSWORD=<см. .env>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=taxi-db
```

---

## 2. Состав таблиц и количество записей (снимок на момент выгрузки)

| Таблица | Записей | Комментарий |
|---|---:|---|
| `towns` | 1 | Города (справочник) |
| `districts` | 6 | Районы (справочник) |
| `streets` | 91 | Улицы (справочник) |
| `houses` | 3363 | Дома (справочник) |
| `street_synonyms` | 0 | Синонимы улиц (справочник, пока пусто) |
| `landmarks` | 0 | Ориентиры (справочник, пока пусто) |
| `orders` | 0 | Заказы (содержат адреса подачи/назначения) |
| `waypoints` | 0 | Промежуточные остановки заказов |
| `call_sessions` | 0 | Сессии звонков/чатов |
| `messages` | 0 | Сообщения |
| `tool_call_records` | 0 | Записи вызовов инструментов LLM |
| `alembic_version` | 1 | Текущая миграция |

---
## 3. Схема БД (колонки, типы, индексы)

Ниже — актуальные определения таблиц из PostgreSQL
(`information_schema.columns` + `pg_indexes`). Модели ORM дублируют её в
`app/models/*.py` (источник истины для кода).

### 3.1 `towns`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('towns_id_seq')` |
| `name` | character varying | NO | — |
| `base_price` | integer | NO | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `towns_pkey (id)` UNIQUE; `ix_towns_id (id)`; `ix_towns_name (name)`.

### 3.2 `districts`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('districts_id_seq')` |
| `town_id` | integer | NO | — (FK → `towns.id`, CASCADE) |
| `name` | character varying | NO | — |
| `price_override` | integer | YES | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `districts_pkey (id)` UNIQUE; `ix_districts_id`; `ix_districts_name`; `ix_districts_town_id`.

### 3.3 `streets`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('streets_id_seq')` |
| `district_id` | integer | NO | — (FK → `districts.id`, CASCADE) |
| `name` | character varying | NO | — |
| `price_override` | integer | YES | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `streets_pkey (id)` UNIQUE; `ix_streets_id`; `ix_streets_name`; `ix_streets_district_id`.

### 3.4 `houses`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('houses_id_seq')` |
| `street_id` | integer | NO | — (FK → `streets.id`, CASCADE) |
| `number` | character varying(50) | NO | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `houses_pkey (id)` UNIQUE; `ix_houses_number`; `ix_houses_street_id`;
`uq_house_street_number (street_id, number)` UNIQUE — дом уникален в пределах улицы.

### 3.5 `street_synonyms`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('street_synonyms_id_seq')` |
| `street_id` | integer | NO | — (FK → `streets.id`, CASCADE) |
| `name` | character varying | NO | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `street_synonyms_pkey (id)` UNIQUE; `ix_street_synonyms_id`; `ix_street_synonyms_name`;
`ix_street_synonyms_street_id`; `uq_street_synonym_name (street_id, name)` UNIQUE.

### 3.6 `landmarks`
| Колонка | Тип | Null | Default |
|---|---|---|---|
| `id` | integer | NO | `nextval('landmarks_id_seq')` |
| `street_id` | integer | NO | — (FK → `streets.id`, CASCADE) |
| `house_id` | integer | YES | — (FK → `houses.id`, SET NULL) |
| `name` | character varying | NO | — |
| `description` | character varying | YES | — |
| `created_at` | timestamptz | NO | `now()` |
| `updated_at` | timestamptz | NO | `now()` |

Индексы: `landmarks_pkey (id)` UNIQUE; `ix_landmarks_street_id`; `ix_landmarks_house_id`; `ix_landmarks_name`.

### 3.7 `orders` (содержит адресные поля)
| Колонка | Тип | Null | Комментарий |
|---|---|---|---|
| `id` | uuid | NO | PK |
| `call_session_id` | uuid | NO | FK → `call_sessions.id` |
| `pickup_town` | varchar(250) | YES | текст адреса подачи |
| `pickup_town_id` | integer | YES | FK → `towns.id` |
| `pickup_district` | varchar(250) | YES | |
| `pickup_district_id` | integer | YES | FK → `districts.id` |
| `pickup_street` | varchar(250) | YES | |
| `pickup_street_id` | integer | YES | FK → `streets.id` (индексируется) |
| `pickup_house` | varchar(50) | YES | |
| `pickup_house_id` | integer | YES | FK → `houses.id` |
| `pickup_landmark` | varchar(250) | YES | |
| `pickup_landmark_id` | integer | YES | FK → `landmarks.id` |
| `destination_town`(+`_id`) | varchar(250)/integer | YES | адрес назначения (как у подачи) |
| `destination_district`(+`_id`) | … | YES | |
| `destination_street`(+`_id`) | … | YES | |
| `destination_house`(+`_id`) | … | YES | |
| `destination_landmark`(+`_id`) | … | YES | |
| `passenger_name` | varchar(100) | YES | |
| `comment` | varchar(200) | YES | |
| `price` | integer | YES | |
| `state` | varchar(11) | NO | enum order_state |
| `version` | integer | NO | оптимистичная блокировка |
| `idempotency_key` | varchar(64) | YES | UNIQUE |
| `driver_id`/`driver_assigned_at`/`trip_started_at`/`trip_completed_at` | … | YES | |

Индексы: `orders_pkey`, `ix_orders_call_session_id`, `ix_orders_pickup_street_id`,
`ix_orders_destination_street_id`, `ix_orders_state`, `orders_idempotency_key_key` UNIQUE.

> Соглашение (модель `Order`): «адрес валиден» = установлен `*_street_id`.
> `has_both_addresses` = `pickup_street_id` и `destination_street_id` не NULL.

### 3.8 `waypoints`
| Колонка | Тип | Null | Комментарий |
|---|---|---|---|
| `id` | uuid | NO | PK |
| `order_id` | uuid | NO | FK → `orders.id`, CASCADE |
| `sequence_number` | integer | NO | порядок |
| `waypoint_town`(+`_id`) | … | YES | адрес остановки |
| `waypoint_district`(+`_id`) | … | YES | |
| `waypoint_street`(+`_id`) | … | YES | |
| `waypoint_house`(+`_id`) | … | YES | |
| `waypoint_landmark`(+`_id`) | … | YES | |
| `created_at`/`updated_at` | timestamptz | NO | |

Индекс: `waypoints_pkey`, `ix_waypoints_waypoint_street_id`.

Прочие таблицы (`call_sessions`, `messages`, `tool_call_records`, `alembic_version`)
адресных данных не содержат — их полная структура в `docs/db_full_dump.json`.

## 4. Справочник адресов — фактическое содержимое

### 4.1 Города — `towns` (1)

| id | name | base_price |
|---|---|---|
| 4 | Аскарово | 0 |

> `base_price` = 0 (засеяно `seed_parse_askarovo.py --base-price 0`). В коде используется как
> базовая цена поездки по городу; `price_override` районов/улиц пока не заданы.

### 4.2 Районы — `districts` (6)

| id | town_id | name | price_override |
|---|---|---|---|
| 19 | 4 | Центр | null |
| 20 | 4 | Южный | null |
| 21 | 4 | Восточный-2 | null |
| 22 | 4 | Восточный-1 | null |
| 23 | 4 | Северный | null |
| 24 | 4 | Даутово | null |

### 4.3 Улицы — `streets` (91), по районам

Формат: `id: 'Название'` (price_override = null у всех).

#### Район `Центр` (district_id=19) — 24 улицы
```
332 '40 лет Октября'   345 'Гагарина'     347 'Горная'         358 'Кирова'
359 'Колхозная'        360 'Комарова'     361 'Коммунистическая' 362 'Комсомольская'
364 'Ленина'           370 'Матросова'    375 'Мира'            376 'Молодежная'
377 'Мугалляма Мирхайдарова' 381 'Партизанская'  382 'Первомайская'  393 'Салавата Юлаева'
396 'Советская'        402 'Тангатарская' 406 'Учалинская'      413 'Чапаева'
416 'Шаймуратова'      418 'Школьная'     419 'Юбилейная'       420 'Южная'
```

#### Район `Южный` (district_id=20) — 14 улиц
```
333 '40 лет Победы'    337 '70 лет Октября'  348 'Дружбы'        352 'Идяш'
354 'Искра'            365 'Лесная'          368 'Мажита Гафури' 371 'Мелиораторов'
372 'Механизаторов'    383 'Пионерская'      388 'Рауфа Давлетова' 390 'Рихарда Зорге'
399 'Строителей'       400 'Тагира Кусимова'
```

#### Район `Восточный-2` (district_id=21) — 22 улицы
```
334 '50 лет Победы'    336 '65 лет Победы'   341 'Ахмета Лутфуллина' 342 'Бииш Батыра'
353 'Иншара Султанбаева' 355 'Ишмурзы Хидиятова' 363 'Курьятмас'     366 'Луговая'
374 'Минислама Мирсаяпова' 378 'Мурзахана Шамсутдинова' 384 'Пятая'  385 'Раиса Усманова'
389 'Рафика Сальманова'  391 'Садовая'       392 'Салавата Кадырова' 394 'Сарии Миржановой'
397 'Солнечная'         401 'Тамьян'         403 'Тунгаур'         407 'Файзи Гаскарова'
411 'Хадии Давлетшиной' 412 'Целинная'
```

#### Район `Восточный-1` (district_id=22) — 22 улицы
```
335 '60 лет Победы'    338 'Абзелиловская'   343 'Вафира Тайсина'  344 'Весенняя'
346 'Гинията Ушанова'  349 'Емельяна Пугачева' 350 'Загира Исмагилова' 351 'Зайнаб Биишевой'
356 'Ишмухамета Мырзакаева' 357 'Кима Ахмедьянова' 422 'Ленина'    367 'Магнитогорская'
369 'Малика Якшимбетова' 373 'Миллята Хакимова' 379 'Мустая Карима' 386 'Рамазана Уметбаева'
387 'Расуля Кужахметова' 395 'Сафы Истамгалина' 398 'Сосновая'     409 'Фаттаха Ибрагимова'
410 'Фахиры Гумеровой'  421 'Яныбая Хамматова'
```

#### Район `Северный` (district_id=23) — 8 улиц
```
339 'Ак Кайын'      340 'Ахмет Заки Валиди'   404 'Урал Батыра'      405 'Уральская'
408 'Файзрахмана Хисматуллина'  414 'Шагали Шакман'  415 'Шагали Шакмана'  417 'Шайхзады Бабича'
```

#### Район `Даутово` (district_id=24) — 1 улица
```
380 'Мусы Гареева'
```

> ⚠️ Название «Ленина» есть в **двух** районах: `Центр` (id=364) и `Восточный-1` (id=422).
> Без указания района результат → `ambiguous`. В `Северном` также почти совпадают
> «Шагали Шакман» (414) и «Шагали Шакмана» (415).
### 4.4 Дома — `houses` (3363)

- Улиц с домами: 91 (все улицы справочника имеют дома). Уникальных номеров: 366
  (многие улицы «делят» одинаковые номера — 1, 2, 3…).
- Уникальность: `(street_id, number)` — дублей в пределах одной улицы нет.
- Номера — строки: встречаются с литерами (`33а`, `33б`, `33В`, `10а`), с корпусами
  (`10к2`, `33к1`, `14к1`) и дробные (`127/1`, `1/5`, `10/1`, `35/1`).
- Распределение по длине строки номера: 1→575, 2→2333, 3→214, 4→237, 5→4.

> ⚠️ `id` домов «прорежены» (до ~10000 при 3363 записей): seed делает `DELETE`, но не
> сбрасывает sequence `houses_id_seq`. Это не ошибка.

#### Сводка: число домов по улицам (91)
| street_id | улица | район | домов |
|---:|---|---|---:|
| 364 | Ленина | Центр | 118 |
| 337 | 70 лет Октября | Южный | 81 |
| 335 | 60 лет Победы | Восточный-1 | 76 |
| 357 | Кима Ахмедьянова | Восточный-1 | 72 |
| 416 | Шаймуратова | Центр | 70 |
| 347 | Горная | Центр | 67 |
| 411 | Хадии Давлетшиной | Восточный-2 | 67 |
| 376 | Молодежная | Центр | 66 |
| 381 | Партизанская | Центр | 66 |
| 388 | Рауфа Давлетова | Южный | 66 |
| 390 | Рихарда Зорге | Южный | 66 |
| 355 | Ишмурзы Хидиятова | Восточный-2 | 65 |
| 334 | 50 лет Победы | Восточный-2 | 63 |
| 407 | Файзи Гаскарова | Восточный-2 | 63 |
| 389 | Рафика Сальманова | Восточный-2 | 62 |
| 374 | Минислама Мирсаяпова | Восточный-2 | 61 |
| 379 | Мустая Карима | Восточный-1 | 61 |
| 408 | Файзрахмана Хисматуллина | Северный | 61 |
| 361 | Коммунистическая | Центр | 60 |
| 403 | Тунгаур | Восточный-2 | 58 |
| 394 | Сарии Миржановой | Восточный-2 | 57 |
| 412 | Целинная | Восточный-2 | 56 |
| 342 | Бииш Батыра | Восточный-2 | 55 |
| 402 | Тангатарская | Центр | 54 |
| 404 | Урал Батыра | Северный | 54 |
| 385 | Раиса Усманова | Восточный-2 | 52 |
| 391 | Садовая | Восточный-2 | 52 |
| 356 | Ишмухамета Мырзакаева | Восточный-1 | 51 |
| 359 | Колхозная | Центр | 51 |
| 336 | 65 лет Победы | Восточный-2 | 47 |
| 393 | Салавата Юлаева | Центр | 47 |
| 417 | Шайхзады Бабича | Северный | 46 |
| 333 | 40 лет Победы | Южный | 45 |
| 352 | Идяш | Южный | 45 |
| 410 | Фахиры Гумеровой | Восточный-1 | 44 |
| 375 | Мира | Центр | 43 |
| 401 | Тамьян | Восточный-2 | 43 |
| 346 | Гинията Ушанова | Восточный-1 | 41 |
| 366 | Луговая | Восточный-2 | 41 |
| 387 | Расуля Кужахметова | Восточный-1 | 41 |
| 409 | Фаттаха Ибрагимова | Восточный-1 | 41 |
| 386 | Рамазана Уметбаева | Восточный-1 | 40 |
| 363 | Курьятмас | Восточный-2 | 39 |
| 397 | Солнечная | Восточный-2 | 36 |
| 419 | Юбилейная | Центр | 36 |
| 420 | Южная | Центр | 36 |
| 348 | Дружбы | Южный | 35 |
| 350 | Загира Исмагилова | Восточный-1 | 35 |
| 373 | Миллята Хакимова | Восточный-1 | 34 |
| 341 | Ахмета Лутфуллина | Восточный-2 | 33 |
| 340 | Ахмет Заки Валиди | Северный | 32 |
| 384 | Пятая | Восточный-2 | 32 |
| 360 | Комарова | Центр | 29 |
| 395 | Сафы Истамгалина | Восточный-1 | 28 |
| 362 | Комсомольская | Центр | 27 |
| 371 | Мелиораторов | Южный | 27 |
| 399 | Строителей | Южный | 27 |
| 396 | Советская | Центр | 26 |
| 383 | Пионерская | Южный | 25 |
| 369 | Малика Якшимбетова | Восточный-1 | 24 |
| 351 | Зайнаб Биишевой | Восточный-1 | 22 |
| 354 | Искра | Южный | 22 |
| 370 | Матросова | Центр | 22 |
| 343 | Вафира Тайсина | Восточный-1 | 21 |
| 358 | Кирова | Центр | 21 |
| 367 | Магнитогорская | Восточный-1 | 21 |
| 372 | Механизаторов | Южный | 21 |
| 421 | Яныбая Хамматова | Восточный-1 | 21 |
| 365 | Лесная | Южный | 19 |
| 338 | Абзелиловская | Восточный-1 | 18 |
| 368 | Мажита Гафури | Южный | 18 |
| 400 | Тагира Кусимова | Южный | 15 |
| 406 | Учалинская | Центр | 15 |
| 377 | Мугалляма Мирхайдарова | Центр | 13 |
| 380 | Мусы Гареева | Даутово | 13 |
| 398 | Сосновая | Восточный-1 | 13 |
| 414 | Шагали Шакман | Северный | 12 |
| 345 | Гагарина | Центр | 11 |
| 349 | Емельяна Пугачева | Восточный-1 | 11 |
| 382 | Первомайская | Центр | 9 |
| 378 | Мурзахана Шамсутдинова | Восточный-2 | 8 |
| 413 | Чапаева | Центр | 7 |
| 339 | Ак Кайын | Северный | 6 |
| 418 | Школьная | Центр | 6 |
| 332 | 40 лет Октября | Центр | 5 |
| 353 | Иншара Султанбаева | Восточный-2 | 5 |
| 405 | Уральская | Северный | 5 |
| 415 | Шагали Шакмана | Северный | 3 |
| 392 | Салавата Кадырова | Восточный-2 | 2 |
| 344 | Весенняя | Восточный-1 | 1 |
| 422 | Ленина | Восточный-1 | 1 |

> Полный построчный список всех 3363 домов (id, street_id, улица, район, номер) —
> в [`docs/db_houses.csv`](./db_houses.csv).

### 4.5 Синонимы улиц — `street_synonyms` (0)
Таблица пуста.

### 4.6 Ориентиры — `landmarks` (0)
Таблица пуста.

---

## 5. Адреса в заказах (`orders`, `waypoints`)

Таблицы пусты (записей нет). Схема хранит адрес в двух видах:
- текстовое поле (`pickup_street`, `waypoint_house`, …) — как ввёл пассажир;
- FK-ссылка на справочник (`pickup_street_id` → `streets.id`, …) — заполняется только
  после успешной валидации через `AddressService`.
- `Order.has_both_addresses` = заданы `pickup_street_id` и `destination_street_id`.
## 6. Происхождение данных и воспроизведение

Справочник адресов наполняется seed-скриптами из `scripts/` (данные получены парсером
со справочного ресурса по тарифам населённого пункта Аскарово).

| Источник-файл | Что содержит |
|---|---|
| `scripts/parse_askarovo/askarovo_streets.json` | улицы + номера домов (`{улица: {номер: [url,...]}}`), 90 улиц / 3362 дома |
| `scripts/parse_askarovo/askarovo_streets_district.txt` | привязка улица→район (строки `улица<TAB>район`, `=` — префикс), 89 улиц |
| `scripts/parse_askarovo/askarovo_flat.txt` | плоский список «улица, номер» (3362 строки) |
| `docs/askarovo.yaml` | альтернативная заготовка (города/районы/улицы) для `seed_askarovo.py` |

### `python scripts/seed_parse_askarovo.py` — ОСНОВНОЙ наполнитель текущих данных
- Очищает справочник (Landmark → StreetSynonym → House → Street → District → Town),
  затем заново создаёт: 1 город, 6 районов, 90 улиц, 3362 дома.
- `--base-price` задаёт `Town.base_price` (для текущей БД использовался `0`).
- Идемпотентен: при `--no-clear` повторно не создаёт дубли (улица/дом ищутся по имени).
- Улицы без района пропускаются в списке `unmatched_streets`.

### `python scripts/seed_askarovo.py` — альтернативный
- Загружает города/районы/улицы из `docs/askarovo.yaml` (без домов).

### `python scripts/address_debug.py`
- Интерактивная отладка резолвинга: ввод улицы/района/дома/ориентира/города →
  показывает воронку EXACT/SYNONYM/FUZZY и итоговый `AddressMatchResult`.

> На текущем снимке улиц в БД **91**, а не 90: за время работы появилась вторая улица
> «Ленина» (id=422, Восточный-1, 1 дом), которой нет в `askarovo_streets.json` —
> она была добавлена в справочник вне seed-скрипта (например, автосоздание при
> заказе). Пара «Ленина/Центр (364)» и «Ленина/Восточный-1 (422)» даёт `ambiguous`.

---

## 7. Логика разрешения адреса (`AddressService`)

Код: `app/services/address_service.py`, `app/repositories/address_repo.py`,
`app/schemas/address.py`. Источник `NormalizedAddressInput` →
`AddressMatchResult {status, candidates, reason}`.

### Нормализация ввода
- lower, trim, схлопывание пробелов;
- срезаются префиксы типа улицы: `ул.`, `улица`, `пер.`, `переулок`, `пр.`, `проспект`;
- снимаются обрамляющие `"`/`'`;
- если город не указан — подставляется `default_town_name = "аскарово"`.

### Поиск (воронка) по улице
1. **EXACT** — точное совпадение `Street.name` (lower) в районах города;
2. **SYNONYM** — совпадение через `StreetSynonym.name`;
3. **FUZZY** — `similarity(Street.name, name) >= fuzzy_threshold` (порог 0.4),
   топ-`max_candidates`.

### Скоринг (`AddressConfig.weights` / добавки)
- EXACT/SYNONYM база 1.0; FUZZY база 0.65;
- дом найден +0.2, дом не найден −0.2;
- ориентир подтвердил улицу +0.1; поиск только по ориентиру: 0.9;
- сумма зажимается в `[0,1]`.

### Итоговый статус (`AddressCandidate` / `AddressMatchResult`)
- `resolved`: топ-кандидат `score >= 0.8` и либо он единственный, либо отрыв от 2-го
  `>= 0.3`;
- `ambiguous`: 2–3 близких кандидата — их обогащают полем `diff_feature`
  («район …» / «г. …») для уточняющего вопроса пользователю;
- `not_found`: ничего не найдено (с причиной: `town_not_found`, `district_not_found`,
  `street_not_found`, `landmark_not_found` и т.д.).

Параметры по умолчанию (`AddressConfig`):
```
default_town_name="аскарово"   fuzzy_threshold=0.4   max_candidates=5
min_resolve_score=0.9          max_exact_variants=3
weights: exact=1.0 synonym=0.9 fuzzy=0.6 landmark=0.7
         district_match_bonus=0.1 house_match_bonus=0.2 landmark_house_bonus=0.15
```

---

## 8. Данные, доступные в репозитории (для переноса)

| Файл | Описание |
|---|---|
| `docs/db_address_report.md` | этот отчёт |
| `docs/db_full_dump.json` | полный JSON-дамп всех таблиц БД (схемы + данные) |
| `docs/db_houses.csv` | полный список домов (3363 строки) с привязкой к улицам/районам |
| `app/models/address.py` | ORM-модели Town/District/Street/House/StreetSynonym/Landmark |
| `app/models/order.py` | ORM-модель Order с адресными полями + Waypoint |
| `app/services/address_service.py` | логика разрешения адреса |
| `app/repositories/address_repo.py` | SQL-запросы по справочнику |
| `app/schemas/address.py` | Pydantic-схемы адреса |
| `scripts/seed_parse_askarovo.py` | наполнитель справочника (основной) |
| `scripts/seed_askarovo.py` | наполнитель из `docs/askarovo.yaml` |
| `scripts/parse_askarovo/*` | исходные данные (JSON/TXT/flat) |
| `docs/askarovo.yaml` | альтернативная заготовка адресов |
| `alembic/versions/` | миграции Alembic (структура БД) |

## 9. Ограничения и примечания

1. `street_synonyms` и `landmarks` пусты — пока поиск идёт только по exact/fuzzy именам улиц.
2. Название «Ленина» присутствует в двух районах → без района ответ `ambiguous`.
3. Номера домов — строки с литерами/дробями; сравнение при резолвинге регистр/точно
   (`find_house` ищет `number == house_number`).
4. `towns.base_price = 0`; `price_override` нигде не заданы.
5. Все `created_at`/`updated_at` записей справочника одинаковые (14:58:39 UTC,
   13.08.2026) — единый seed-прогон группы.
---