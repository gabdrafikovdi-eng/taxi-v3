# Address Database Snapshot

- Generated at: 2026-08-18T14:34:19+05:00
- Database environment: localhost:5432/taxi-db
- Towns: 1
- Districts: 6
- Streets: 145
- Houses: 3366
- Landmarks: 3
- Schema revision (Alembic): `c5c0e0c33ff9`

> Снимок формируется автоматически при каждом запуске ``scripts/generate_address_snapshot.py`` и отражает РЕАЛЬНОЕ состояние БД на момент запуска. Секреты/пароли/DSN не выводятся.

## Содержимое

1. ORM Schema — структура адресных моделей (колонки и relationships).
2. Towns / Districts / Streets / Houses / Landmarks — все записи с контекстом.
3. House Number Groups — группировка домов по (улица, base).
4. Potential House Suggestion Cases — фактические suggestion-комбинации.
5. Potential Duplicates / Data Anomalies / Unparseable House Numbers.
6. Statistics — сводные счётчики.

---

# Statistics

| Entity | Count |
|---|---:|
| Towns | 1 |
| Districts | 6 |
| Streets | 145 |
| Houses | 3366 |
| Landmarks | 3 |
| Street aliases (synonyms) | 0 |
| House number groups | 2951 |

## House number type breakdown

| Type | Count |
|---|---:|
| PLAIN | 2874 |
| LETTER | 118 |
| CORPUS | 56 |
| FRACTION | 317 |
| Unparseable | 1 |

---

# ORM Schema

Фактическая структура адресных ORM-моделей проекта (интроспекция SQLAlchemy mapper, без выдуманных полей).

## Town

Таблица: `towns`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| base_price | Integer | no | no | - |
| created_at | DateTime | no | no | - |
| name | String | no | no | - |
| updated_at | DateTime | no | no | - |

### Relationships

- districts → District [list] (back: town)

## District

Таблица: `districts`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| created_at | DateTime | no | no | - |
| name | String | no | no | - |
| price_override | Integer | yes | no | - |
| town_id | Integer | no | no | towns.id |
| updated_at | DateTime | no | no | - |

### Relationships

- streets → Street [list] (back: district)
- town → Town [single] (back: districts)

## Street

Таблица: `streets`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| created_at | DateTime | no | no | - |
| district_id | Integer | no | no | districts.id |
| name | String | no | no | - |
| price_override | Integer | yes | no | - |
| updated_at | DateTime | no | no | - |

### Relationships

- district → District [single] (back: streets)
- houses → House [list] (back: street)
- landmarks → Landmark [list] (back: street)
- synonyms → StreetSynonym [list] (back: street)

## House

Таблица: `houses`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| created_at | DateTime | no | no | - |
| number | String(50) | no | no | - |
| price_override | Integer | yes | no | - |
| street_id | Integer | no | no | streets.id |
| updated_at | DateTime | no | no | - |

### Relationships

- landmarks → Landmark [list] (back: house)
- street → Street [single] (back: houses)

## StreetSynonym

Таблица: `street_synonyms`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| created_at | DateTime | no | no | - |
| name | String | no | no | - |
| street_id | Integer | no | no | streets.id |
| updated_at | DateTime | no | no | - |

### Relationships

- street → Street [single] (back: synonyms)

## Landmark

Таблица: `landmarks`

### Columns

| Column | Type | Nullable | Primary Key | Foreign Key |
|---|---|---|---|---|
| id | Integer | no | yes | - |
| created_at | DateTime | no | no | - |
| description | String | yes | no | - |
| house_id | Integer | yes | no | houses.id |
| name | String | no | no | - |
| street_id | Integer | no | no | streets.id |
| updated_at | DateTime | no | no | - |

### Relationships

- house → House [single] (back: landmarks)
- street → Street [single] (back: landmarks)

---

# Towns

## Town: Аскарово

- ID: 4
- Base price: 0
- Districts: 6
- Streets: 145
- Houses: 3366
- Landmarks: 3

---

# Districts

## District: Восточный-1

- ID: 22
- Town: Аскарово
- Town ID: 4
- Price override: 200
- Streets: 28
- Houses: 719
- Landmarks: 1

## District: Восточный-2

- ID: 21
- Town: Аскарово
- Town ID: 4
- Price override: 250
- Streets: 33
- Houses: 997
- Landmarks: 0

## District: Даутово

- ID: 24
- Town: Аскарово
- Town ID: 4
- Price override: 280
- Streets: 26
- Houses: 13
- Landmarks: 0

## District: Северный

- ID: 23
- Town: Аскарово
- Town ID: 4
- Price override: 200
- Streets: 14
- Houses: 220
- Landmarks: 0

## District: Центр

- ID: 19
- Town: Аскарово
- Town ID: 4
- Price override: 150
- Streets: 24
- Houses: 905
- Landmarks: 2

## District: Южный

- ID: 20
- Town: Аскарово
- Town ID: 4
- Price override: 170
- Streets: 20
- Houses: 512
- Landmarks: 0

---

# Streets

## Street: 60 лет Победы

- ID: 335
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 76
- Landmarks: 0
- Synonyms: —

## Street: Абзелиловская

- ID: 338
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 18
- Landmarks: 0
- Synonyms: —

## Street: Вафира Тайсина

- ID: 343
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 21
- Landmarks: 0
- Synonyms: —

## Street: Весенняя

- ID: 344
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 1
- Landmarks: 0
- Synonyms: —

## Street: Гинията Ушанова

- ID: 346
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 41
- Landmarks: 0
- Synonyms: —

## Street: Емельяна Пугачева

- ID: 349
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 11
- Landmarks: 0
- Synonyms: —

## Street: Емельяна Пугачёва

- ID: 437
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Загира Исмагилова

- ID: 350
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 35
- Landmarks: 0
- Synonyms: —

## Street: Зайнаб Биишевой

- ID: 351
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 22
- Landmarks: 0
- Synonyms: —

## Street: Ишмухамета Мырзакаева

- ID: 356
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 51
- Landmarks: 0
- Synonyms: —

## Street: Кима Ахмедьянова

- ID: 357
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 72
- Landmarks: 0
- Synonyms: —

## Street: Ленина

- ID: 422
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 2
- Landmarks: 0
- Synonyms: —

## Street: Магнитогорская

- ID: 367
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 21
- Landmarks: 0
- Synonyms: —

## Street: Малика Якшимбетова

- ID: 369
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 24
- Landmarks: 0
- Synonyms: —

## Street: Миллята Хакимова

- ID: 373
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 34
- Landmarks: 0
- Synonyms: —

## Street: Миптата Хакимова

- ID: 438
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Мустая Карима

- ID: 379
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 61
- Landmarks: 0
- Synonyms: —

## Street: Николая Гоголя

- ID: 436
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Рамазана Уметбаева

- ID: 386
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 40
- Landmarks: 0
- Synonyms: —

## Street: Расуля Кужахметова

- ID: 387
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 41
- Landmarks: 0
- Synonyms: —

## Street: Сафи Истамгалина

- ID: 439
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 1
- Landmarks: 1
- Synonyms: —

## Street: Сафы Истамгалина

- ID: 395
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 28
- Landmarks: 0
- Synonyms: —

## Street: Сосновая

- ID: 398
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 13
- Landmarks: 0
- Synonyms: —

## Street: Фаттаха Ибрагимова

- ID: 409
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 41
- Landmarks: 0
- Synonyms: —

## Street: Фахиры Гумеровой

- ID: 410
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 44
- Landmarks: 0
- Synonyms: —

## Street: Шаймуратова

- ID: 440
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Юности

- ID: 435
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Яныбая Хамматова

- ID: 421
- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Price override: —
- Houses: 21
- Landmarks: 0
- Synonyms: —

## Street: 50 лет Победы

- ID: 334
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 63
- Landmarks: 0
- Synonyms: —

## Street: 65 лет Победы

- ID: 336
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 47
- Landmarks: 0
- Synonyms: —

## Street: Ахмета Лутфуллина

- ID: 341
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 33
- Landmarks: 0
- Synonyms: —

## Street: Бииш Батыра

- ID: 342
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 55
- Landmarks: 0
- Synonyms: —

## Street: Валиахмета Сулейманова

- ID: 450
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Индиры Султанбаевой

- ID: 451
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Иншара Султанбаева

- ID: 353
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 5
- Landmarks: 0
- Synonyms: —

## Street: Ишмурзы Хидиятова

- ID: 355
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 65
- Landmarks: 0
- Synonyms: —

## Street: Курчатова

- ID: 445
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Курьятмас

- ID: 363
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 39
- Landmarks: 0
- Synonyms: —

## Street: Луговая

- ID: 366
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 41
- Landmarks: 0
- Synonyms: —

## Street: Минислама Мирсаяпова

- ID: 374
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 61
- Landmarks: 0
- Synonyms: —

## Street: Мисаля Муртасина

- ID: 452
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Мурзахана Шамсутдинова

- ID: 378
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 8
- Landmarks: 0
- Synonyms: —

## Street: Нажипа Асанбаева

- ID: 448
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Пятая

- ID: 384
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 32
- Landmarks: 0
- Synonyms: —

## Street: Раиса Усманова

- ID: 385
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 52
- Landmarks: 0
- Synonyms: —

## Street: Рамазана Уметбаева

- ID: 443
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Рами Гарипова

- ID: 449
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Рафика Сальманова

- ID: 389
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 62
- Landmarks: 0
- Synonyms: —

## Street: Сагиры Мишар

- ID: 446
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Садовая

- ID: 391
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 52
- Landmarks: 0
- Synonyms: —

## Street: Салавата Кадырова

- ID: 392
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 2
- Landmarks: 0
- Synonyms: —

## Street: Сарии Миржановой

- ID: 394
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 57
- Landmarks: 0
- Synonyms: —

## Street: Солнечная

- ID: 397
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 36
- Landmarks: 0
- Synonyms: —

## Street: Тамьян

- ID: 401
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 43
- Landmarks: 0
- Synonyms: —

## Street: Тукая

- ID: 447
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Тунгаур

- ID: 403
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 58
- Landmarks: 0
- Synonyms: —

## Street: Фазиля Искандера

- ID: 444
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Файзи Гаскарова

- ID: 407
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 63
- Landmarks: 0
- Synonyms: —

## Street: Хадии Давлетшиной

- ID: 411
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 67
- Landmarks: 0
- Synonyms: —

## Street: Целинная

- ID: 412
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 56
- Landmarks: 0
- Synonyms: —

## Street: Шаймуратова

- ID: 442
- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: 10 лет Победы

- ID: 454
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: 60 лет Победы

- ID: 455
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: 8 Марта

- ID: 453
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Абзелиловская

- ID: 456
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Александра Пушкина

- ID: 457
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Гайфуллы Сарбаева

- ID: 458
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Георгия Васева

- ID: 459
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Караташ

- ID: 460
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Кизильская

- ID: 461
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Кинзи Арсланова

- ID: 462
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Кыркты-Тау

- ID: 463
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Михаила Лермонтова

- ID: 464
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Мусы Гареева

- ID: 380
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 13
- Landmarks: 0
- Synonyms: —

## Street: Мусы Джалиля

- ID: 465
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Нургали Фахретдинова

- ID: 466
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Рауфа Давлетова

- ID: 467
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Сагиды Бердиной

- ID: 468
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Салавата Юлаева

- ID: 469
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Салимьяна Гайнуллина

- ID: 470
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Саляха Кулибая

- ID: 471
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Северная

- ID: 472
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Сергея Аксакова

- ID: 473
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Сергея Есенина

- ID: 474
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Центральная

- ID: 475
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Шакира Биккулова

- ID: 476
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Школьная

- ID: 477
- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Ак Кайын

- ID: 339
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 6
- Landmarks: 0
- Synonyms: —

## Street: Ак-Күлгин

- ID: 425
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Ахмет Заки Валиди

- ID: 340
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 32
- Landmarks: 0
- Synonyms: —

## Street: Комарова

- ID: 428
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Ленина

- ID: 423
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 1
- Landmarks: 0
- Synonyms: —

## Street: Любимая

- ID: 427
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Урал Батыра

- ID: 404
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 54
- Landmarks: 0
- Synonyms: —

## Street: Уральская

- ID: 405
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 5
- Landmarks: 0
- Synonyms: —

## Street: Файзрахмана Мустафина

- ID: 424
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Файзрахмана Хисматуллина

- ID: 408
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 61
- Landmarks: 0
- Synonyms: —

## Street: Шагали Шакман

- ID: 414
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 12
- Landmarks: 0
- Synonyms: —

## Street: Шагали Шакмана

- ID: 415
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 3
- Landmarks: 0
- Synonyms: —

## Street: Шайхзады Бабича

- ID: 417
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 46
- Landmarks: 0
- Synonyms: —

## Street: Шакимана

- ID: 426
- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: 40 лет Октября

- ID: 332
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 5
- Landmarks: 0
- Synonyms: —

## Street: Гагарина

- ID: 345
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 11
- Landmarks: 1
- Synonyms: —

## Street: Горная

- ID: 347
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 67
- Landmarks: 0
- Synonyms: —

## Street: Кирова

- ID: 358
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 21
- Landmarks: 0
- Synonyms: —

## Street: Колхозная

- ID: 359
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 51
- Landmarks: 0
- Synonyms: —

## Street: Комарова

- ID: 360
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 29
- Landmarks: 0
- Synonyms: —

## Street: Коммунистическая

- ID: 361
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 60
- Landmarks: 0
- Synonyms: —

## Street: Комсомольская

- ID: 362
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 27
- Landmarks: 0
- Synonyms: —

## Street: Ленина

- ID: 364
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 118
- Landmarks: 1
- Synonyms: —

## Street: Матросова

- ID: 370
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 22
- Landmarks: 0
- Synonyms: —

## Street: Мира

- ID: 375
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 43
- Landmarks: 0
- Synonyms: —

## Street: Молодежная

- ID: 376
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 66
- Landmarks: 0
- Synonyms: —

## Street: Мугалляма Мирхайдарова

- ID: 377
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 13
- Landmarks: 0
- Synonyms: —

## Street: Партизанская

- ID: 381
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 66
- Landmarks: 0
- Synonyms: —

## Street: Первомайская

- ID: 382
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 9
- Landmarks: 0
- Synonyms: —

## Street: Салавата Юлаева

- ID: 393
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 47
- Landmarks: 0
- Synonyms: —

## Street: Советская

- ID: 396
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 26
- Landmarks: 0
- Synonyms: —

## Street: Тангатарская

- ID: 402
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 54
- Landmarks: 0
- Synonyms: —

## Street: Учалинская

- ID: 406
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 15
- Landmarks: 0
- Synonyms: —

## Street: Чапаева

- ID: 413
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 7
- Landmarks: 0
- Synonyms: —

## Street: Шаймуратова

- ID: 416
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 70
- Landmarks: 0
- Synonyms: —

## Street: Школьная

- ID: 418
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 6
- Landmarks: 0
- Synonyms: —

## Street: Юбилейная

- ID: 419
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 36
- Landmarks: 0
- Synonyms: —

## Street: Южная

- ID: 420
- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Price override: —
- Houses: 36
- Landmarks: 0
- Synonyms: —

## Street: 40 лет Победы

- ID: 333
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 45
- Landmarks: 0
- Synonyms: —

## Street: 70 лет Октября

- ID: 337
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 81
- Landmarks: 0
- Synonyms: —

## Street: Горная

- ID: 431
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Дружбы

- ID: 348
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 35
- Landmarks: 0
- Synonyms: —

## Street: Идяш

- ID: 352
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 45
- Landmarks: 0
- Synonyms: —

## Street: Идяшево

- ID: 429
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Искра

- ID: 354
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 22
- Landmarks: 0
- Synonyms: —

## Street: Кирова

- ID: 434
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Лесная

- ID: 365
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 19
- Landmarks: 0
- Synonyms: —

## Street: Мажита Гафури

- ID: 368
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 18
- Landmarks: 0
- Synonyms: —

## Street: Мелиораторов

- ID: 371
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 27
- Landmarks: 0
- Synonyms: —

## Street: Механизаторов

- ID: 372
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 21
- Landmarks: 0
- Synonyms: —

## Street: Октябрьская

- ID: 433
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Партизанская

- ID: 432
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

## Street: Пионерская

- ID: 383
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 25
- Landmarks: 0
- Synonyms: —

## Street: Рауфа Давлетова

- ID: 388
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 66
- Landmarks: 0
- Synonyms: —

## Street: Рихарда Зорге

- ID: 390
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 66
- Landmarks: 0
- Synonyms: —

## Street: Строителей

- ID: 399
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 27
- Landmarks: 0
- Synonyms: —

## Street: Тагира Кусимова

- ID: 400
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 15
- Landmarks: 0
- Synonyms: —

## Street: Южная

- ID: 430
- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Price override: —
- Houses: 0
- Landmarks: 0
- Synonyms: —

---

# Houses

Все дома, сгруппированные по иерархии Town → District → Street. Для каждого номера показан результат существующего ``parse_house_number()``: base / type / suffix.

Всего домов: **3366**.

## Town: Аскарово (ID: 4)

### District: Восточный-1 (ID: 22)

#### Street: 60 лет Победы (ID: 335)

Кол-во домов: 76

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6842 | 1 | 1 | PLAIN | - |
| 6843 | 1/1 | 1 | FRACTION | 1 |
| 6857 | 2 | 2 | PLAIN | - |
| 6869 | 3 | 3 | PLAIN | - |
| 6889 | 5 | 5 | PLAIN | - |
| 6900 | 6 | 6 | PLAIN | - |
| 6901 | 6/1 | 6 | FRACTION | 1 |
| 6902 | 6/2 | 6 | FRACTION | 2 |
| 6909 | 7 | 7 | PLAIN | - |
| 6913 | 8 | 8 | PLAIN | - |
| 6917 | 9 | 9 | PLAIN | - |
| 6844 | 10 | 10 | PLAIN | - |
| 6845 | 11 | 11 | PLAIN | - |
| 6846 | 12 | 12 | PLAIN | - |
| 6847 | 13 | 13 | PLAIN | - |
| 6848 | 15 | 15 | PLAIN | - |
| 6849 | 15А | 15 | LETTER | а |
| 6850 | 17 | 17 | PLAIN | - |
| 6851 | 18 | 18 | PLAIN | - |
| 6854 | 18а | 18 | LETTER | а |
| 6855 | 18б | 18 | LETTER | б |
| 6852 | 18/1 | 18 | FRACTION | 1 |
| 6853 | 18/2 | 18 | FRACTION | 2 |
| 6856 | 19 | 19 | PLAIN | - |
| 6858 | 20 | 20 | PLAIN | - |
| 6859 | 20/2 | 20 | FRACTION | 2 |
| 6860 | 21 | 21 | PLAIN | - |
| 6861 | 22 | 22 | PLAIN | - |
| 6862 | 23 | 23 | PLAIN | - |
| 6863 | 24 | 24 | PLAIN | - |
| 6864 | 25 | 25 | PLAIN | - |
| 6865 | 26 | 26 | PLAIN | - |
| 6866 | 27 | 27 | PLAIN | - |
| 6867 | 28 | 28 | PLAIN | - |
| 6868 | 29 | 29 | PLAIN | - |
| 6870 | 30 | 30 | PLAIN | - |
| 6871 | 31 | 31 | PLAIN | - |
| 6872 | 32 | 32 | PLAIN | - |
| 6873 | 33 | 33 | PLAIN | - |
| 6874 | 34 | 34 | PLAIN | - |
| 6875 | 35 | 35 | PLAIN | - |
| 6876 | 36 | 36 | PLAIN | - |
| 6877 | 37 | 37 | PLAIN | - |
| 6878 | 39 | 39 | PLAIN | - |
| 6879 | 40 | 40 | PLAIN | - |
| 6880 | 41 | 41 | PLAIN | - |
| 6881 | 42 | 42 | PLAIN | - |
| 6882 | 45 | 45 | PLAIN | - |
| 6883 | 46 | 46 | PLAIN | - |
| 6885 | 46А | 46 | LETTER | а |
| 6884 | 46/1 | 46 | FRACTION | 1 |
| 6886 | 47 | 47 | PLAIN | - |
| 6887 | 48 | 48 | PLAIN | - |
| 6888 | 49 | 49 | PLAIN | - |
| 6890 | 50 | 50 | PLAIN | - |
| 6891 | 51 | 51 | PLAIN | - |
| 6892 | 51/1 | 51 | FRACTION | 1 |
| 6893 | 52 | 52 | PLAIN | - |
| 6894 | 53 | 53 | PLAIN | - |
| 6895 | 54 | 54 | PLAIN | - |
| 6896 | 56 | 56 | PLAIN | - |
| 6897 | 57 | 57 | PLAIN | - |
| 6898 | 58 | 58 | PLAIN | - |
| 6899 | 59 | 59 | PLAIN | - |
| 6903 | 60 | 60 | PLAIN | - |
| 6904 | 61 | 61 | PLAIN | - |
| 6905 | 62 | 62 | PLAIN | - |
| 6906 | 63 | 63 | PLAIN | - |
| 6907 | 64 | 64 | PLAIN | - |
| 6908 | 68 | 68 | PLAIN | - |
| 6910 | 72 | 72 | PLAIN | - |
| 6911 | 79 | 79 | PLAIN | - |
| 6912 | 79/1 | 79 | FRACTION | 1 |
| 6914 | 81 | 81 | PLAIN | - |
| 6915 | 83 | 83 | PLAIN | - |
| 6916 | 85 | 85 | PLAIN | - |

#### Street: Абзелиловская (ID: 338)

Кол-во домов: 18

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7046 | 1 | 1 | PLAIN | - |
| 7056 | 1а | 1 | LETTER | а |
| 7058 | 3 | 3 | PLAIN | - |
| 7059 | 4 | 4 | PLAIN | - |
| 7060 | 5 | 5 | PLAIN | - |
| 7061 | 6 | 6 | PLAIN | - |
| 7062 | 8 | 8 | PLAIN | - |
| 7063 | 9 | 9 | PLAIN | - |
| 7047 | 10 | 10 | PLAIN | - |
| 7048 | 11 | 11 | PLAIN | - |
| 7049 | 12 | 12 | PLAIN | - |
| 7050 | 13 | 13 | PLAIN | - |
| 7051 | 14 | 14 | PLAIN | - |
| 7052 | 15 | 15 | PLAIN | - |
| 7053 | 17 | 17 | PLAIN | - |
| 7054 | 18 | 18 | PLAIN | - |
| 7055 | 19 | 19 | PLAIN | - |
| 7057 | 23 | 23 | PLAIN | - |

#### Street: Вафира Тайсина (ID: 343)

Кол-во домов: 21

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7199 | 1А | 1 | LETTER | а |
| 7200 | 1Б | 1 | LETTER | б |
| 7201 | 2 | 2 | PLAIN | - |
| 7202 | 2/1 | 2 | FRACTION | 1 |
| 7203 | 2/2 | 2 | FRACTION | 2 |
| 7206 | 3 | 3 | PLAIN | - |
| 7207 | 4 | 4 | PLAIN | - |
| 7208 | 6 | 6 | PLAIN | - |
| 7209 | 8 | 8 | PLAIN | - |
| 7210 | 9 | 9 | PLAIN | - |
| 7190 | 10 | 10 | PLAIN | - |
| 7191 | 11 | 11 | PLAIN | - |
| 7192 | 11/1 | 11 | FRACTION | 1 |
| 7193 | 12 | 12 | PLAIN | - |
| 7194 | 14 | 14 | PLAIN | - |
| 7195 | 15 | 15 | PLAIN | - |
| 7196 | 16 | 16 | PLAIN | - |
| 7197 | 17 | 17 | PLAIN | - |
| 7198 | 19 | 19 | PLAIN | - |
| 7204 | 21 | 21 | PLAIN | - |
| 7205 | 23 | 23 | PLAIN | - |

#### Street: Весенняя (ID: 344)

Кол-во домов: 1

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7211 | 7 | 7 | PLAIN | - |

#### Street: Гинията Ушанова (ID: 346)

Кол-во домов: 41

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7223 | 1 | 1 | PLAIN | - |
| 7234 | 2 | 2 | PLAIN | - |
| 7245 | 3 | 3 | PLAIN | - |
| 7256 | 4 | 4 | PLAIN | - |
| 7258 | 5 | 5 | PLAIN | - |
| 7260 | 6 | 6 | PLAIN | - |
| 7261 | 7 | 7 | PLAIN | - |
| 7262 | 8 | 8 | PLAIN | - |
| 7263 | 9 | 9 | PLAIN | - |
| 7224 | 10 | 10 | PLAIN | - |
| 7225 | 11 | 11 | PLAIN | - |
| 7226 | 12 | 12 | PLAIN | - |
| 7227 | 13 | 13 | PLAIN | - |
| 7228 | 14 | 14 | PLAIN | - |
| 7229 | 15 | 15 | PLAIN | - |
| 7230 | 16 | 16 | PLAIN | - |
| 7231 | 17 | 17 | PLAIN | - |
| 7232 | 18 | 18 | PLAIN | - |
| 7233 | 19 | 19 | PLAIN | - |
| 7235 | 20 | 20 | PLAIN | - |
| 7236 | 21 | 21 | PLAIN | - |
| 7237 | 22 | 22 | PLAIN | - |
| 7238 | 23 | 23 | PLAIN | - |
| 7239 | 24 | 24 | PLAIN | - |
| 7240 | 25 | 25 | PLAIN | - |
| 7241 | 26 | 26 | PLAIN | - |
| 7242 | 27 | 27 | PLAIN | - |
| 7243 | 28 | 28 | PLAIN | - |
| 7244 | 29 | 29 | PLAIN | - |
| 7246 | 30 | 30 | PLAIN | - |
| 7247 | 31 | 31 | PLAIN | - |
| 7248 | 32 | 32 | PLAIN | - |
| 7249 | 33 | 33 | PLAIN | - |
| 7250 | 34 | 34 | PLAIN | - |
| 7251 | 35 | 35 | PLAIN | - |
| 7252 | 36 | 36 | PLAIN | - |
| 7253 | 37 | 37 | PLAIN | - |
| 7254 | 38 | 38 | PLAIN | - |
| 7255 | 39 | 39 | PLAIN | - |
| 7257 | 40 | 40 | PLAIN | - |
| 7259 | 56 | 56 | PLAIN | - |

#### Street: Емельяна Пугачева (ID: 349)

Кол-во домов: 11

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7371 | 4 | 4 | PLAIN | - |
| 7373 | 5 | 5 | PLAIN | - |
| 7374 | 6 | 6 | PLAIN | - |
| 7375 | 7 | 7 | PLAIN | - |
| 7376 | 9 | 9 | PLAIN | - |
| 7366 | 12 | 12 | PLAIN | - |
| 7367 | 15 | 15 | PLAIN | - |
| 7368 | 17 | 17 | PLAIN | - |
| 7369 | 25 | 25 | PLAIN | - |
| 7370 | 26 | 26 | PLAIN | - |
| 7372 | 44 | 44 | PLAIN | - |

#### Street: Емельяна Пугачёва (ID: 437)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Загира Исмагилова (ID: 350)

Кол-во домов: 35

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7377 | 1 | 1 | PLAIN | - |
| 7394 | 3 | 3 | PLAIN | - |
| 7410 | 5 | 5 | PLAIN | - |
| 7411 | 9 | 9 | PLAIN | - |
| 7378 | 10 | 10 | PLAIN | - |
| 7379 | 11 | 11 | PLAIN | - |
| 7380 | 12 | 12 | PLAIN | - |
| 7381 | 13 | 13 | PLAIN | - |
| 7382 | 14 | 14 | PLAIN | - |
| 7383 | 15/1 | 15 | FRACTION | 1 |
| 7384 | 16 | 16 | PLAIN | - |
| 7385 | 17 | 17 | PLAIN | - |
| 7386 | 18 | 18 | PLAIN | - |
| 7387 | 19 | 19 | PLAIN | - |
| 7388 | 20 | 20 | PLAIN | - |
| 7389 | 22 | 22 | PLAIN | - |
| 7390 | 23 | 23 | PLAIN | - |
| 7391 | 25 | 25 | PLAIN | - |
| 7392 | 27/1 | 27 | FRACTION | 1 |
| 7393 | 29 | 29 | PLAIN | - |
| 7395 | 31 | 31 | PLAIN | - |
| 7396 | 32/1 | 32 | FRACTION | 1 |
| 7397 | 33 | 33 | PLAIN | - |
| 7398 | 34 | 34 | PLAIN | - |
| 7399 | 35 | 35 | PLAIN | - |
| 7400 | 36 | 36 | PLAIN | - |
| 7401 | 38 | 38 | PLAIN | - |
| 7402 | 39 | 39 | PLAIN | - |
| 7403 | 40 | 40 | PLAIN | - |
| 7404 | 41 | 41 | PLAIN | - |
| 7405 | 42 | 42 | PLAIN | - |
| 7406 | 43 | 43 | PLAIN | - |
| 7407 | 44 | 44 | PLAIN | - |
| 7408 | 46 | 46 | PLAIN | - |
| 7409 | 49 | 49 | PLAIN | - |

#### Street: Зайнаб Биишевой (ID: 351)

Кол-во домов: 22

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7433 | 9/1 | 9 | FRACTION | 1 |
| 7412 | 22 | 22 | PLAIN | - |
| 7413 | 23 | 23 | PLAIN | - |
| 7414 | 24 | 24 | PLAIN | - |
| 7415 | 25 | 25 | PLAIN | - |
| 7416 | 26 | 26 | PLAIN | - |
| 7417 | 30 | 30 | PLAIN | - |
| 7418 | 32 | 32 | PLAIN | - |
| 7419 | 36 | 36 | PLAIN | - |
| 7420 | 37 | 37 | PLAIN | - |
| 7421 | 37/1 | 37 | FRACTION | 1 |
| 7422 | 39 | 39 | PLAIN | - |
| 7423 | 40 | 40 | PLAIN | - |
| 7424 | 44 | 44 | PLAIN | - |
| 7425 | 46 | 46 | PLAIN | - |
| 7426 | 48 | 48 | PLAIN | - |
| 7427 | 49 | 49 | PLAIN | - |
| 7428 | 50/1 | 50 | FRACTION | 1 |
| 7429 | 52 | 52 | PLAIN | - |
| 7430 | 54 | 54 | PLAIN | - |
| 7431 | 56 | 56 | PLAIN | - |
| 7432 | 64 | 64 | PLAIN | - |

#### Street: Ишмухамета Мырзакаева (ID: 356)

Кол-во домов: 51

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7571 | 1 | 1 | PLAIN | - |
| 7572 | 1/1 | 1 | FRACTION | 1 |
| 7584 | 2 | 2 | PLAIN | - |
| 7605 | 4 | 4 | PLAIN | - |
| 7611 | 5 | 5 | PLAIN | - |
| 7616 | 6 | 6 | PLAIN | - |
| 7619 | 7 | 7 | PLAIN | - |
| 7620 | 8 | 8 | PLAIN | - |
| 7621 | 9 | 9 | PLAIN | - |
| 7573 | 10 | 10 | PLAIN | - |
| 7574 | 11 | 11 | PLAIN | - |
| 7575 | 11к1 | 11 | CORPUS | 1 |
| 7576 | 12 | 12 | PLAIN | - |
| 7577 | 13 | 13 | PLAIN | - |
| 7578 | 13/1 | 13 | FRACTION | 1 |
| 7579 | 14 | 14 | PLAIN | - |
| 7580 | 15 | 15 | PLAIN | - |
| 7581 | 16 | 16 | PLAIN | - |
| 7582 | 18 | 18 | PLAIN | - |
| 7583 | 19 | 19 | PLAIN | - |
| 7585 | 20 | 20 | PLAIN | - |
| 7586 | 21 | 21 | PLAIN | - |
| 7587 | 22 | 22 | PLAIN | - |
| 7588 | 23 | 23 | PLAIN | - |
| 7589 | 24 | 24 | PLAIN | - |
| 7590 | 25 | 25 | PLAIN | - |
| 7591 | 25/1 | 25 | FRACTION | 1 |
| 7592 | 26 | 26 | PLAIN | - |
| 7593 | 27 | 27 | PLAIN | - |
| 7594 | 28 | 28 | PLAIN | - |
| 7595 | 29 | 29 | PLAIN | - |
| 7596 | 30 | 30 | PLAIN | - |
| 7597 | 32 | 32 | PLAIN | - |
| 7598 | 33 | 33 | PLAIN | - |
| 7599 | 34 | 34 | PLAIN | - |
| 7600 | 35 | 35 | PLAIN | - |
| 7601 | 35/2 | 35 | FRACTION | 2 |
| 7602 | 36 | 36 | PLAIN | - |
| 7603 | 37 | 37 | PLAIN | - |
| 7604 | 38 | 38 | PLAIN | - |
| 7606 | 40 | 40 | PLAIN | - |
| 7607 | 41 | 41 | PLAIN | - |
| 7608 | 42 | 42 | PLAIN | - |
| 7609 | 44 | 44 | PLAIN | - |
| 7610 | 48 | 48 | PLAIN | - |
| 7612 | 52/1 | 52 | FRACTION | 1 |
| 7613 | 54 | 54 | PLAIN | - |
| 7614 | 56 | 56 | PLAIN | - |
| 7615 | 58 | 58 | PLAIN | - |
| 7617 | 60 | 60 | PLAIN | - |
| 7618 | 66 | 66 | PLAIN | - |

#### Street: Кима Ахмедьянова (ID: 357)

Кол-во домов: 72

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7622 | 1 | 1 | PLAIN | - |
| 7632 | 1а | 1 | LETTER | а |
| 7633 | 2 | 2 | PLAIN | - |
| 7644 | 3 | 3 | PLAIN | - |
| 7656 | 4 | 4 | PLAIN | - |
| 7667 | 5 | 5 | PLAIN | - |
| 7677 | 6 | 6 | PLAIN | - |
| 7685 | 7 | 7 | PLAIN | - |
| 7692 | 8 | 8 | PLAIN | - |
| 7693 | 9 | 9 | PLAIN | - |
| 7623 | 10 | 10 | PLAIN | - |
| 7624 | 11 | 11 | PLAIN | - |
| 7625 | 12 | 12 | PLAIN | - |
| 7626 | 13 | 13 | PLAIN | - |
| 7627 | 14 | 14 | PLAIN | - |
| 7628 | 15 | 15 | PLAIN | - |
| 7629 | 16 | 16 | PLAIN | - |
| 7630 | 17 | 17 | PLAIN | - |
| 7631 | 19 | 19 | PLAIN | - |
| 7634 | 20 | 20 | PLAIN | - |
| 7635 | 21 | 21 | PLAIN | - |
| 7636 | 22 | 22 | PLAIN | - |
| 7637 | 23 | 23 | PLAIN | - |
| 7638 | 24 | 24 | PLAIN | - |
| 7639 | 25 | 25 | PLAIN | - |
| 7640 | 26 | 26 | PLAIN | - |
| 7641 | 27 | 27 | PLAIN | - |
| 7642 | 28 | 28 | PLAIN | - |
| 7643 | 29 | 29 | PLAIN | - |
| 7645 | 30 | 30 | PLAIN | - |
| 7646 | 32 | 32 | PLAIN | - |
| 7647 | 34 | 34 | PLAIN | - |
| 7648 | 35 | 35 | PLAIN | - |
| 7649 | 36 | 36 | PLAIN | - |
| 7650 | 37 | 37 | PLAIN | - |
| 7651 | 38 | 38 | PLAIN | - |
| 7652 | 38/1 | 38 | FRACTION | 1 |
| 7653 | 38/2 | 38 | FRACTION | 2 |
| 7654 | 38/3 | 38 | FRACTION | 3 |
| 7655 | 39 | 39 | PLAIN | - |
| 7657 | 40 | 40 | PLAIN | - |
| 7658 | 40/1 | 40 | FRACTION | 1 |
| 7659 | 40/3 | 40 | FRACTION | 3 |
| 7660 | 41 | 41 | PLAIN | - |
| 7661 | 42 | 42 | PLAIN | - |
| 7662 | 43 | 43 | PLAIN | - |
| 7663 | 44 | 44 | PLAIN | - |
| 7664 | 46 | 46 | PLAIN | - |
| 7665 | 48 | 48 | PLAIN | - |
| 7666 | 49 | 49 | PLAIN | - |
| 7668 | 50 | 50 | PLAIN | - |
| 7669 | 51 | 51 | PLAIN | - |
| 7670 | 52 | 52 | PLAIN | - |
| 7671 | 53 | 53 | PLAIN | - |
| 7672 | 54 | 54 | PLAIN | - |
| 7673 | 56 | 56 | PLAIN | - |
| 7674 | 57 | 57 | PLAIN | - |
| 7675 | 58 | 58 | PLAIN | - |
| 7676 | 59 | 59 | PLAIN | - |
| 7678 | 60 | 60 | PLAIN | - |
| 7679 | 62 | 62 | PLAIN | - |
| 7680 | 63 | 63 | PLAIN | - |
| 7681 | 65 | 65 | PLAIN | - |
| 7682 | 67 | 67 | PLAIN | - |
| 7683 | 68 | 68 | PLAIN | - |
| 7684 | 69 | 69 | PLAIN | - |
| 7686 | 70 | 70 | PLAIN | - |
| 7687 | 71 | 71 | PLAIN | - |
| 7688 | 72 | 72 | PLAIN | - |
| 7689 | 72/1 | 72 | FRACTION | 1 |
| 7690 | 74 | 74 | PLAIN | - |
| 7691 | 76 | 76 | PLAIN | - |

#### Street: Ленина (ID: 422)

Кол-во домов: 2

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 10092 | 33 | 33 | PLAIN | - |
| 10091 | 500 | 500 | PLAIN | - |

#### Street: Магнитогорская (ID: 367)

Кол-во домов: 21

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8099 | 1 | 1 | PLAIN | - |
| 8112 | 3 | 3 | PLAIN | - |
| 8115 | 4 | 4 | PLAIN | - |
| 8116 | 6 | 6 | PLAIN | - |
| 8117 | 7 | 7 | PLAIN | - |
| 8118 | 8 | 8 | PLAIN | - |
| 8119 | 9 | 9 | PLAIN | - |
| 8100 | 10 | 10 | PLAIN | - |
| 8101 | 13 | 13 | PLAIN | - |
| 8102 | 14 | 14 | PLAIN | - |
| 8103 | 15 | 15 | PLAIN | - |
| 8104 | 16 | 16 | PLAIN | - |
| 8105 | 17 | 17 | PLAIN | - |
| 8106 | 18 | 18 | PLAIN | - |
| 8107 | 20 | 20 | PLAIN | - |
| 8108 | 22 | 22 | PLAIN | - |
| 8109 | 24 | 24 | PLAIN | - |
| 8110 | 26 | 26 | PLAIN | - |
| 8111 | 28 | 28 | PLAIN | - |
| 8113 | 30 | 30 | PLAIN | - |
| 8114 | 30/1 | 30 | FRACTION | 1 |

#### Street: Малика Якшимбетова (ID: 369)

Кол-во домов: 24

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8145 | 2 | 2 | PLAIN | - |
| 8146 | 2/1 | 2 | FRACTION | 1 |
| 8157 | 4 | 4 | PLAIN | - |
| 8160 | 6 | 6 | PLAIN | - |
| 8161 | 8 | 8 | PLAIN | - |
| 8138 | 10 | 10 | PLAIN | - |
| 8139 | 12 | 12 | PLAIN | - |
| 8140 | 13 | 13 | PLAIN | - |
| 8141 | 14 | 14 | PLAIN | - |
| 8142 | 15 | 15 | PLAIN | - |
| 8143 | 17 | 17 | PLAIN | - |
| 8144 | 19 | 19 | PLAIN | - |
| 8147 | 20 | 20 | PLAIN | - |
| 8148 | 21 | 21 | PLAIN | - |
| 8149 | 22 | 22 | PLAIN | - |
| 8150 | 23 | 23 | PLAIN | - |
| 8151 | 24 | 24 | PLAIN | - |
| 8152 | 26 | 26 | PLAIN | - |
| 8153 | 27 | 27 | PLAIN | - |
| 8154 | 28 | 28 | PLAIN | - |
| 8155 | 30 | 30 | PLAIN | - |
| 8156 | 34 | 34 | PLAIN | - |
| 8158 | 40 | 40 | PLAIN | - |
| 8159 | 41 | 41 | PLAIN | - |

#### Street: Миллята Хакимова (ID: 373)

Кол-во домов: 34

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8232 | 1 | 1 | PLAIN | - |
| 8243 | 2 | 2 | PLAIN | - |
| 8244 | 2/1 | 2 | FRACTION | 1 |
| 8251 | 3 | 3 | PLAIN | - |
| 8255 | 4 | 4 | PLAIN | - |
| 8258 | 5 | 5 | PLAIN | - |
| 8262 | 6 | 6 | PLAIN | - |
| 8263 | 7 | 7 | PLAIN | - |
| 8264 | 8 | 8 | PLAIN | - |
| 8265 | 9 | 9 | PLAIN | - |
| 8233 | 10 | 10 | PLAIN | - |
| 8234 | 11 | 11 | PLAIN | - |
| 8235 | 12 | 12 | PLAIN | - |
| 8236 | 13 | 13 | PLAIN | - |
| 8237 | 14 | 14 | PLAIN | - |
| 8238 | 15 | 15 | PLAIN | - |
| 8239 | 16 | 16 | PLAIN | - |
| 8240 | 17 | 17 | PLAIN | - |
| 8241 | 18 | 18 | PLAIN | - |
| 8242 | 19 | 19 | PLAIN | - |
| 8245 | 20 | 20 | PLAIN | - |
| 8246 | 21 | 21 | PLAIN | - |
| 8247 | 22 | 22 | PLAIN | - |
| 8248 | 23 | 23 | PLAIN | - |
| 8249 | 25 | 25 | PLAIN | - |
| 8250 | 27 | 27 | PLAIN | - |
| 8252 | 31 | 31 | PLAIN | - |
| 8253 | 35 | 35 | PLAIN | - |
| 8254 | 39 | 39 | PLAIN | - |
| 8256 | 47 | 47 | PLAIN | - |
| 8257 | 49 | 49 | PLAIN | - |
| 8259 | 51 | 51 | PLAIN | - |
| 8260 | 55 | 55 | PLAIN | - |
| 8261 | 57 | 57 | PLAIN | - |

#### Street: Миптата Хакимова (ID: 438)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Мустая Карима (ID: 379)

Кол-во домов: 61

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8457 | 1 | 1 | PLAIN | - |
| 8468 | 2 | 2 | PLAIN | - |
| 8479 | 3 | 3 | PLAIN | - |
| 8490 | 4 | 4 | PLAIN | - |
| 8499 | 5 | 5 | PLAIN | - |
| 8507 | 6 | 6 | PLAIN | - |
| 8515 | 7 | 7 | PLAIN | - |
| 8516 | 8 | 8 | PLAIN | - |
| 8517 | 9 | 9 | PLAIN | - |
| 8458 | 10 | 10 | PLAIN | - |
| 8459 | 11 | 11 | PLAIN | - |
| 8460 | 12 | 12 | PLAIN | - |
| 8461 | 13 | 13 | PLAIN | - |
| 8462 | 14 | 14 | PLAIN | - |
| 8463 | 15 | 15 | PLAIN | - |
| 8464 | 16 | 16 | PLAIN | - |
| 8465 | 17 | 17 | PLAIN | - |
| 8466 | 18 | 18 | PLAIN | - |
| 8467 | 19 | 19 | PLAIN | - |
| 8469 | 20 | 20 | PLAIN | - |
| 8470 | 21 | 21 | PLAIN | - |
| 8471 | 22 | 22 | PLAIN | - |
| 8472 | 23 | 23 | PLAIN | - |
| 8473 | 24 | 24 | PLAIN | - |
| 8474 | 25 | 25 | PLAIN | - |
| 8475 | 26 | 26 | PLAIN | - |
| 8476 | 27 | 27 | PLAIN | - |
| 8477 | 28 | 28 | PLAIN | - |
| 8478 | 29 | 29 | PLAIN | - |
| 8480 | 30 | 30 | PLAIN | - |
| 8481 | 31 | 31 | PLAIN | - |
| 8482 | 32 | 32 | PLAIN | - |
| 8483 | 33 | 33 | PLAIN | - |
| 8484 | 34 | 34 | PLAIN | - |
| 8485 | 35 | 35 | PLAIN | - |
| 8486 | 36 | 36 | PLAIN | - |
| 8487 | 37 | 37 | PLAIN | - |
| 8488 | 38 | 38 | PLAIN | - |
| 8489 | 39 | 39 | PLAIN | - |
| 8491 | 40 | 40 | PLAIN | - |
| 8492 | 41 | 41 | PLAIN | - |
| 8493 | 42 | 42 | PLAIN | - |
| 8494 | 43 | 43 | PLAIN | - |
| 8495 | 45 | 45 | PLAIN | - |
| 8496 | 46 | 46 | PLAIN | - |
| 8497 | 48 | 48 | PLAIN | - |
| 8498 | 49 | 49 | PLAIN | - |
| 8500 | 50 | 50 | PLAIN | - |
| 8501 | 51 | 51 | PLAIN | - |
| 8502 | 53 | 53 | PLAIN | - |
| 8503 | 54 | 54 | PLAIN | - |
| 8504 | 55 | 55 | PLAIN | - |
| 8505 | 57 | 57 | PLAIN | - |
| 8506 | 59 | 59 | PLAIN | - |
| 8508 | 60 | 60 | PLAIN | - |
| 8509 | 61 | 61 | PLAIN | - |
| 8510 | 62 | 62 | PLAIN | - |
| 8511 | 63 | 63 | PLAIN | - |
| 8512 | 65 | 65 | PLAIN | - |
| 8513 | 67 | 67 | PLAIN | - |
| 8514 | 67/1 | 67 | FRACTION | 1 |

#### Street: Николая Гоголя (ID: 436)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Рамазана Уметбаева (ID: 386)

Кол-во домов: 40

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8715 | 1 | 1 | PLAIN | - |
| 8730 | 1а | 1 | LETTER | а |
| 8716 | 1/2 | 1 | FRACTION | 2 |
| 8717 | 1/3 | 1 | FRACTION | 3 |
| 8731 | 2 | 2 | PLAIN | - |
| 8749 | 4 | 4 | PLAIN | - |
| 8750 | 5 | 5 | PLAIN | - |
| 8751 | 6 | 6 | PLAIN | - |
| 8752 | 7 | 7 | PLAIN | - |
| 8753 | 8 | 8 | PLAIN | - |
| 8754 | 9 | 9 | PLAIN | - |
| 8718 | 10 | 10 | PLAIN | - |
| 8719 | 10к3 | 10 | CORPUS | 3 |
| 8720 | 11 | 11 | PLAIN | - |
| 8721 | 12 | 12 | PLAIN | - |
| 8722 | 13 | 13 | PLAIN | - |
| 8723 | 14 | 14 | PLAIN | - |
| 8724 | 15 | 15 | PLAIN | - |
| 8725 | 17 | 17 | PLAIN | - |
| 8726 | 17/1 | 17 | FRACTION | 1 |
| 8727 | 18 | 18 | PLAIN | - |
| 8728 | 19 | 19 | PLAIN | - |
| 8729 | 19/1 | 19 | FRACTION | 1 |
| 8732 | 20 | 20 | PLAIN | - |
| 8733 | 21 | 21 | PLAIN | - |
| 8734 | 23/1 | 23 | FRACTION | 1 |
| 8735 | 24 | 24 | PLAIN | - |
| 8736 | 25 | 25 | PLAIN | - |
| 8737 | 25/1 | 25 | FRACTION | 1 |
| 8738 | 27 | 27 | PLAIN | - |
| 8739 | 27/1 | 27 | FRACTION | 1 |
| 8740 | 27/2 | 27 | FRACTION | 2 |
| 8741 | 27/3 | 27 | FRACTION | 3 |
| 8742 | 28 | 28 | PLAIN | - |
| 8743 | 29 | 29 | PLAIN | - |
| 8744 | 29/1 | 29 | FRACTION | 1 |
| 8745 | 30 | 30 | PLAIN | - |
| 8746 | 31 | 31 | PLAIN | - |
| 8747 | 32 | 32 | PLAIN | - |
| 8748 | 36 | 36 | PLAIN | - |

#### Street: Расуля Кужахметова (ID: 387)

Кол-во домов: 41

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8755 | 1 | 1 | PLAIN | - |
| 8766 | 2 | 2 | PLAIN | - |
| 8779 | 3 | 3 | PLAIN | - |
| 8789 | 4 | 4 | PLAIN | - |
| 8791 | 5 | 5 | PLAIN | - |
| 8792 | 6 | 6 | PLAIN | - |
| 8793 | 7 | 7 | PLAIN | - |
| 8794 | 8 | 8 | PLAIN | - |
| 8795 | 9 | 9 | PLAIN | - |
| 8756 | 10 | 10 | PLAIN | - |
| 8757 | 11 | 11 | PLAIN | - |
| 8758 | 12 | 12 | PLAIN | - |
| 8759 | 13 | 13 | PLAIN | - |
| 8760 | 14 | 14 | PLAIN | - |
| 8761 | 15 | 15 | PLAIN | - |
| 8762 | 16 | 16 | PLAIN | - |
| 8763 | 17 | 17 | PLAIN | - |
| 8764 | 18 | 18 | PLAIN | - |
| 8765 | 19 | 19 | PLAIN | - |
| 8767 | 20 | 20 | PLAIN | - |
| 8768 | 21 | 21 | PLAIN | - |
| 8769 | 21/1 | 21 | FRACTION | 1 |
| 8770 | 22 | 22 | PLAIN | - |
| 8771 | 23 | 23 | PLAIN | - |
| 8772 | 24 | 24 | PLAIN | - |
| 8773 | 25 | 25 | PLAIN | - |
| 8774 | 26 | 26 | PLAIN | - |
| 8775 | 26А | 26 | LETTER | а |
| 8776 | 27 | 27 | PLAIN | - |
| 8777 | 28 | 28 | PLAIN | - |
| 8778 | 29 | 29 | PLAIN | - |
| 8780 | 30 | 30 | PLAIN | - |
| 8781 | 31 | 31 | PLAIN | - |
| 8782 | 32 | 32 | PLAIN | - |
| 8783 | 33 | 33 | PLAIN | - |
| 8784 | 35 | 35 | PLAIN | - |
| 8785 | 36 | 36 | PLAIN | - |
| 8786 | 37 | 37 | PLAIN | - |
| 8787 | 38 | 38 | PLAIN | - |
| 8788 | 39 | 39 | PLAIN | - |
| 8790 | 40 | 40 | PLAIN | - |

#### Street: Сафи Истамгалина (ID: 439)

Кол-во домов: 1

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 10094 | 31 | 31 | PLAIN | - |

#### Street: Сафы Истамгалина (ID: 395)

Кол-во домов: 28

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9148 | 17 | 17 | PLAIN | - |
| 9149 | 19 | 19 | PLAIN | - |
| 9150 | 21 | 21 | PLAIN | - |
| 9151 | 23 | 23 | PLAIN | - |
| 9152 | 25 | 25 | PLAIN | - |
| 9153 | 27 | 27 | PLAIN | - |
| 9154 | 29 | 29 | PLAIN | - |
| 9155 | 31 | 31 | PLAIN | - |
| 9156 | 33 | 33 | PLAIN | - |
| 9157 | 35 | 35 | PLAIN | - |
| 9158 | 37 | 37 | PLAIN | - |
| 9159 | 39 | 39 | PLAIN | - |
| 9160 | 40 | 40 | PLAIN | - |
| 9161 | 41 | 41 | PLAIN | - |
| 9162 | 42 | 42 | PLAIN | - |
| 9163 | 43 | 43 | PLAIN | - |
| 9164 | 45 | 45 | PLAIN | - |
| 9165 | 47 | 47 | PLAIN | - |
| 9166 | 48 | 48 | PLAIN | - |
| 9167 | 49 | 49 | PLAIN | - |
| 9168 | 51 | 51 | PLAIN | - |
| 9169 | 52 | 52 | PLAIN | - |
| 9170 | 53 | 53 | PLAIN | - |
| 9171 | 54 | 54 | PLAIN | - |
| 9172 | 55 | 55 | PLAIN | - |
| 9173 | 56 | 56 | PLAIN | - |
| 9174 | 58 | 58 | PLAIN | - |
| 9175 | 60 | 60 | PLAIN | - |

#### Street: Сосновая (ID: 398)

Кол-во домов: 13

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9238 | 1 | 1 | PLAIN | - |
| 9239 | 1/1 | 1 | FRACTION | 1 |
| 9247 | 3 | 3 | PLAIN | - |
| 9240 | 15 | 15 | PLAIN | - |
| 9241 | 17 | 17 | PLAIN | - |
| 9242 | 19 | 19 | PLAIN | - |
| 9243 | 21 | 21 | PLAIN | - |
| 9244 | 23 | 23 | PLAIN | - |
| 9245 | 25 | 25 | PLAIN | - |
| 9246 | 27 | 27 | PLAIN | - |
| 9248 | 33 | 33 | PLAIN | - |
| 9249 | 35 | 35 | PLAIN | - |
| 9250 | 37 | 37 | PLAIN | - |

#### Street: Фаттаха Ибрагимова (ID: 409)

Кол-во домов: 41

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9646 | 1 | 1 | PLAIN | - |
| 9654 | 1А | 1 | LETTER | а |
| 9655 | 2 | 2 | PLAIN | - |
| 9666 | 4 | 4 | PLAIN | - |
| 9672 | 5 | 5 | PLAIN | - |
| 9680 | 6 | 6 | PLAIN | - |
| 9684 | 7 | 7 | PLAIN | - |
| 9685 | 8 | 8 | PLAIN | - |
| 9686 | 9 | 9 | PLAIN | - |
| 9647 | 10 | 10 | PLAIN | - |
| 9648 | 11 | 11 | PLAIN | - |
| 9649 | 12 | 12 | PLAIN | - |
| 9650 | 13 | 13 | PLAIN | - |
| 9651 | 14 | 14 | PLAIN | - |
| 9652 | 16 | 16 | PLAIN | - |
| 9653 | 18 | 18 | PLAIN | - |
| 9656 | 20 | 20 | PLAIN | - |
| 9657 | 22 | 22 | PLAIN | - |
| 9658 | 24 | 24 | PLAIN | - |
| 9659 | 26 | 26 | PLAIN | - |
| 9660 | 28 | 28 | PLAIN | - |
| 9661 | 30 | 30 | PLAIN | - |
| 9662 | 32 | 32 | PLAIN | - |
| 9663 | 34 | 34 | PLAIN | - |
| 9664 | 36 | 36 | PLAIN | - |
| 9665 | 38 | 38 | PLAIN | - |
| 9667 | 40 | 40 | PLAIN | - |
| 9668 | 42 | 42 | PLAIN | - |
| 9669 | 44 | 44 | PLAIN | - |
| 9670 | 46 | 46 | PLAIN | - |
| 9671 | 48 | 48 | PLAIN | - |
| 9673 | 50 | 50 | PLAIN | - |
| 9674 | 51 | 51 | PLAIN | - |
| 9675 | 52 | 52 | PLAIN | - |
| 9676 | 54 | 54 | PLAIN | - |
| 9677 | 55 | 55 | PLAIN | - |
| 9678 | 56 | 56 | PLAIN | - |
| 9679 | 58 | 58 | PLAIN | - |
| 9681 | 60 | 60 | PLAIN | - |
| 9682 | 62 | 62 | PLAIN | - |
| 9683 | 64 | 64 | PLAIN | - |

#### Street: Фахиры Гумеровой (ID: 410)

Кол-во домов: 44

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9687 | 1 | 1 | PLAIN | - |
| 9694 | 2 | 2 | PLAIN | - |
| 9700 | 3 | 3 | PLAIN | - |
| 9709 | 4 | 4 | PLAIN | - |
| 9725 | 7 | 7 | PLAIN | - |
| 9728 | 8 | 8 | PLAIN | - |
| 9729 | 8А | 8 | LETTER | а |
| 9730 | 9 | 9 | PLAIN | - |
| 9688 | 10 | 10 | PLAIN | - |
| 9689 | 11 | 11 | PLAIN | - |
| 9690 | 12 | 12 | PLAIN | - |
| 9691 | 13 | 13 | PLAIN | - |
| 9692 | 14 | 14 | PLAIN | - |
| 9693 | 19 | 19 | PLAIN | - |
| 9695 | 21 | 21 | PLAIN | - |
| 9696 | 23 | 23 | PLAIN | - |
| 9697 | 25 | 25 | PLAIN | - |
| 9698 | 27 | 27 | PLAIN | - |
| 9699 | 29 | 29 | PLAIN | - |
| 9701 | 31 | 31 | PLAIN | - |
| 9702 | 33 | 33 | PLAIN | - |
| 9703 | 35 | 35 | PLAIN | - |
| 9704 | 35/1 | 35 | FRACTION | 1 |
| 9705 | 37 | 37 | PLAIN | - |
| 9706 | 38Б | 38 | LETTER | б |
| 9707 | 39 | 39 | PLAIN | - |
| 9708 | 39/1 | 39 | FRACTION | 1 |
| 9710 | 40 | 40 | PLAIN | - |
| 9711 | 41 | 41 | PLAIN | - |
| 9712 | 43 | 43 | PLAIN | - |
| 9713 | 47 | 47 | PLAIN | - |
| 9714 | 49 | 49 | PLAIN | - |
| 9715 | 51 | 51 | PLAIN | - |
| 9716 | 53 | 53 | PLAIN | - |
| 9717 | 55 | 55 | PLAIN | - |
| 9718 | 57 | 57 | PLAIN | - |
| 9719 | 59 | 59 | PLAIN | - |
| 9720 | 61 | 61 | PLAIN | - |
| 9721 | 63 | 63 | PLAIN | - |
| 9722 | 65 | 65 | PLAIN | - |
| 9723 | 67 | 67 | PLAIN | - |
| 9724 | 69 | 69 | PLAIN | - |
| 9726 | 71 | 71 | PLAIN | - |
| 9727 | 73 | 73 | PLAIN | - |

#### Street: Шаймуратова (ID: 440)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Юности (ID: 435)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Яныбая Хамматова (ID: 421)

Кол-во домов: 21

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 10070 | 1 | 1 | PLAIN | - |
| 10082 | 3 | 3 | PLAIN | - |
| 10088 | 5 | 5 | PLAIN | - |
| 10089 | 7 | 7 | PLAIN | - |
| 10090 | 9 | 9 | PLAIN | - |
| 10071 | 11 | 11 | PLAIN | - |
| 10072 | 13 | 13 | PLAIN | - |
| 10073 | 15 | 15 | PLAIN | - |
| 10074 | 17 | 17 | PLAIN | - |
| 10075 | 17к1 | 17 | CORPUS | 1 |
| 10076 | 19 | 19 | PLAIN | - |
| 10077 | 21 | 21 | PLAIN | - |
| 10078 | 23 | 23 | PLAIN | - |
| 10079 | 25 | 25 | PLAIN | - |
| 10080 | 27 | 27 | PLAIN | - |
| 10081 | 27А | 27 | LETTER | а |
| 10083 | 31 | 31 | PLAIN | - |
| 10084 | 33 | 33 | PLAIN | - |
| 10085 | 35 | 35 | PLAIN | - |
| 10086 | 37 | 37 | PLAIN | - |
| 10087 | 47 | 47 | PLAIN | - |

### District: Восточный-2 (ID: 21)

#### Street: 50 лет Победы (ID: 334)

Кол-во домов: 63

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6779 | 1/1 | 1 | FRACTION | 1 |
| 6780 | 1/4 | 1 | FRACTION | 4 |
| 6781 | 1/5 | 1 | FRACTION | 5 |
| 6782 | 1/6 | 1 | FRACTION | 6 |
| 6783 | 1/7 | 1 | FRACTION | 7 |
| 6784 | 1/8 | 1 | FRACTION | 8 |
| 6791 | 2 | 2 | PLAIN | - |
| 6792 | 2/5 | 2 | FRACTION | 5 |
| 6793 | 2/7 | 2 | FRACTION | 7 |
| 6794 | 2/9 | 2 | FRACTION | 9 |
| 6821 | 6 | 6 | PLAIN | - |
| 6826 | 7 | 7 | PLAIN | - |
| 6785 | 10 | 10 | PLAIN | - |
| 6786 | 12 | 12 | PLAIN | - |
| 6787 | 13 | 13 | PLAIN | - |
| 6788 | 16 | 16 | PLAIN | - |
| 6789 | 17 | 17 | PLAIN | - |
| 6790 | 19 | 19 | PLAIN | - |
| 6795 | 20 | 20 | PLAIN | - |
| 6796 | 21 | 21 | PLAIN | - |
| 6797 | 22 | 22 | PLAIN | - |
| 6798 | 23 | 23 | PLAIN | - |
| 6799 | 24 | 24 | PLAIN | - |
| 6800 | 25 | 25 | PLAIN | - |
| 6801 | 26 | 26 | PLAIN | - |
| 6802 | 28 | 28 | PLAIN | - |
| 6803 | 29 | 29 | PLAIN | - |
| 6804 | 31 | 31 | PLAIN | - |
| 6805 | 32 | 32 | PLAIN | - |
| 6806 | 33 | 33 | PLAIN | - |
| 6807 | 34 | 34 | PLAIN | - |
| 6808 | 35 | 35 | PLAIN | - |
| 6809 | 37 | 37 | PLAIN | - |
| 6810 | 41 | 41 | PLAIN | - |
| 6811 | 43 | 43 | PLAIN | - |
| 6812 | 46 | 46 | PLAIN | - |
| 6813 | 49 | 49 | PLAIN | - |
| 6814 | 50 | 50 | PLAIN | - |
| 6815 | 51 | 51 | PLAIN | - |
| 6816 | 53 | 53 | PLAIN | - |
| 6817 | 54 | 54 | PLAIN | - |
| 6818 | 56 | 56 | PLAIN | - |
| 6819 | 57 | 57 | PLAIN | - |
| 6820 | 58 | 58 | PLAIN | - |
| 6822 | 62 | 62 | PLAIN | - |
| 6823 | 64 | 64 | PLAIN | - |
| 6824 | 65 | 65 | PLAIN | - |
| 6825 | 67 | 67 | PLAIN | - |
| 6827 | 70 | 70 | PLAIN | - |
| 6828 | 70/1 | 70 | FRACTION | 1 |
| 6829 | 71 | 71 | PLAIN | - |
| 6830 | 73 | 73 | PLAIN | - |
| 6831 | 74 | 74 | PLAIN | - |
| 6832 | 75 | 75 | PLAIN | - |
| 6833 | 76 | 76 | PLAIN | - |
| 6834 | 78 | 78 | PLAIN | - |
| 6835 | 79 | 79 | PLAIN | - |
| 6836 | 80 | 80 | PLAIN | - |
| 6837 | 82 | 82 | PLAIN | - |
| 6838 | 84 | 84 | PLAIN | - |
| 6839 | 86 | 86 | PLAIN | - |
| 6840 | 87 | 87 | PLAIN | - |
| 6841 | 89 | 89 | PLAIN | - |

#### Street: 65 лет Победы (ID: 336)

Кол-во домов: 47

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6918 | 1 | 1 | PLAIN | - |
| 6919 | 1/2 | 1 | FRACTION | 2 |
| 6930 | 2 | 2 | PLAIN | - |
| 6931 | 2/1 | 2 | FRACTION | 1 |
| 6945 | 5 | 5 | PLAIN | - |
| 6951 | 6 | 6 | PLAIN | - |
| 6954 | 7 | 7 | PLAIN | - |
| 6960 | 8 | 8 | PLAIN | - |
| 6920 | 10 | 10 | PLAIN | - |
| 6921 | 12 | 12 | PLAIN | - |
| 6922 | 13 | 13 | PLAIN | - |
| 6923 | 14 | 14 | PLAIN | - |
| 6924 | 15 | 15 | PLAIN | - |
| 6925 | 16 | 16 | PLAIN | - |
| 6926 | 17 | 17 | PLAIN | - |
| 6927 | 18 | 18 | PLAIN | - |
| 6928 | 19 | 19 | PLAIN | - |
| 6929 | 19/1 | 19 | FRACTION | 1 |
| 6932 | 21 | 21 | PLAIN | - |
| 6933 | 25 | 25 | PLAIN | - |
| 6934 | 26 | 26 | PLAIN | - |
| 6935 | 34 | 34 | PLAIN | - |
| 6936 | 39 | 39 | PLAIN | - |
| 6937 | 40 | 40 | PLAIN | - |
| 6938 | 41 | 41 | PLAIN | - |
| 6939 | 44 | 44 | PLAIN | - |
| 6940 | 44/1 | 44 | FRACTION | 1 |
| 6941 | 45 | 45 | PLAIN | - |
| 6942 | 46 | 46 | PLAIN | - |
| 6943 | 47 | 47 | PLAIN | - |
| 6944 | 48 | 48 | PLAIN | - |
| 6946 | 50 | 50 | PLAIN | - |
| 6947 | 51 | 51 | PLAIN | - |
| 6948 | 53 | 53 | PLAIN | - |
| 6949 | 55 | 55 | PLAIN | - |
| 6950 | 57 | 57 | PLAIN | - |
| 6952 | 66 | 66 | PLAIN | - |
| 6953 | 69 | 69 | PLAIN | - |
| 6955 | 70 | 70 | PLAIN | - |
| 6956 | 70/1 | 70 | FRACTION | 1 |
| 6957 | 72 | 72 | PLAIN | - |
| 6958 | 74 | 74 | PLAIN | - |
| 6959 | 79 | 79 | PLAIN | - |
| 6961 | 81 | 81 | PLAIN | - |
| 6962 | 83 | 83 | PLAIN | - |
| 6963 | 84 | 84 | PLAIN | - |
| 6964 | 85 | 85 | PLAIN | - |

#### Street: Ахмета Лутфуллина (ID: 341)

Кол-во домов: 33

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7133 | 6 | 6 | PLAIN | - |
| 7134 | 8 | 8 | PLAIN | - |
| 7102 | 13 | 13 | PLAIN | - |
| 7103 | 13/1 | 13 | FRACTION | 1 |
| 7104 | 15 | 15 | PLAIN | - |
| 7105 | 16 | 16 | PLAIN | - |
| 7106 | 18 | 18 | PLAIN | - |
| 7107 | 19 | 19 | PLAIN | - |
| 7108 | 20 | 20 | PLAIN | - |
| 7109 | 21 | 21 | PLAIN | - |
| 7110 | 22 | 22 | PLAIN | - |
| 7111 | 23/5 | 23 | FRACTION | 5 |
| 7112 | 24 | 24 | PLAIN | - |
| 7113 | 25 | 25 | PLAIN | - |
| 7114 | 26 | 26 | PLAIN | - |
| 7115 | 27 | 27 | PLAIN | - |
| 7116 | 28 | 28 | PLAIN | - |
| 7117 | 29 | 29 | PLAIN | - |
| 7118 | 30 | 30 | PLAIN | - |
| 7119 | 30/1 | 30 | FRACTION | 1 |
| 7120 | 31 | 31 | PLAIN | - |
| 7121 | 32 | 32 | PLAIN | - |
| 7122 | 35 | 35 | PLAIN | - |
| 7123 | 36 | 36 | PLAIN | - |
| 7124 | 37 | 37 | PLAIN | - |
| 7125 | 40 | 40 | PLAIN | - |
| 7126 | 42 | 42 | PLAIN | - |
| 7127 | 43 | 43 | PLAIN | - |
| 7128 | 44 | 44 | PLAIN | - |
| 7129 | 45 | 45 | PLAIN | - |
| 7130 | 46 | 46 | PLAIN | - |
| 7131 | 48 | 48 | PLAIN | - |
| 7132 | 49 | 49 | PLAIN | - |

#### Street: Бииш Батыра (ID: 342)

Кол-во домов: 55

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7135 | 1 | 1 | PLAIN | - |
| 7136 | 1/1 | 1 | FRACTION | 1 |
| 7156 | 2 | 2 | PLAIN | - |
| 7176 | 4 | 4 | PLAIN | - |
| 7183 | 5 | 5 | PLAIN | - |
| 7186 | 6 | 6 | PLAIN | - |
| 7187 | 7 | 7 | PLAIN | - |
| 7188 | 8 | 8 | PLAIN | - |
| 7189 | 9 | 9 | PLAIN | - |
| 7137 | 10 | 10 | PLAIN | - |
| 7138 | 11 | 11 | PLAIN | - |
| 7139 | 12 | 12 | PLAIN | - |
| 7140 | 13 | 13 | PLAIN | - |
| 7141 | 14 | 14 | PLAIN | - |
| 7142 | 14/1 | 14 | FRACTION | 1 |
| 7143 | 14/2 | 14 | FRACTION | 2 |
| 7144 | 14/3 | 14 | FRACTION | 3 |
| 7145 | 15 | 15 | PLAIN | - |
| 7146 | 15/1 | 15 | FRACTION | 1 |
| 7147 | 15/3 | 15 | FRACTION | 3 |
| 7148 | 16 | 16 | PLAIN | - |
| 7151 | 16а | 16 | LETTER | а |
| 7149 | 16/1 | 16 | FRACTION | 1 |
| 7150 | 16/2 | 16 | FRACTION | 2 |
| 7152 | 17/2 | 17 | FRACTION | 2 |
| 7153 | 17/3 | 17 | FRACTION | 3 |
| 7154 | 18 | 18 | PLAIN | - |
| 7155 | 19 | 19 | PLAIN | - |
| 7157 | 20 | 20 | PLAIN | - |
| 7158 | 21 | 21 | PLAIN | - |
| 7159 | 22 | 22 | PLAIN | - |
| 7160 | 23 | 23 | PLAIN | - |
| 7161 | 25 | 25 | PLAIN | - |
| 7162 | 26 | 26 | PLAIN | - |
| 7163 | 27 | 27 | PLAIN | - |
| 7164 | 28 | 28 | PLAIN | - |
| 7165 | 29 | 29 | PLAIN | - |
| 7166 | 30 | 30 | PLAIN | - |
| 7167 | 31 | 31 | PLAIN | - |
| 7168 | 32 | 32 | PLAIN | - |
| 7169 | 33 | 33 | PLAIN | - |
| 7170 | 34 | 34 | PLAIN | - |
| 7171 | 35 | 35 | PLAIN | - |
| 7172 | 36 | 36 | PLAIN | - |
| 7173 | 37 | 37 | PLAIN | - |
| 7174 | 38 | 38 | PLAIN | - |
| 7175 | 39 | 39 | PLAIN | - |
| 7177 | 40 | 40 | PLAIN | - |
| 7178 | 41 | 41 | PLAIN | - |
| 7179 | 42 | 42 | PLAIN | - |
| 7180 | 44 | 44 | PLAIN | - |
| 7181 | 47 | 47 | PLAIN | - |
| 7182 | 48 | 48 | PLAIN | - |
| 7184 | 50 | 50 | PLAIN | - |
| 7185 | 53 | 53 | PLAIN | - |

#### Street: Валиахмета Сулейманова (ID: 450)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Индиры Султанбаевой (ID: 451)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Иншара Султанбаева (ID: 353)

Кол-во домов: 5

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7479 | 50 | 50 | PLAIN | - |
| 7480 | 51 | 51 | PLAIN | - |
| 7481 | 56 | 56 | PLAIN | - |
| 7482 | 57 | 57 | PLAIN | - |
| 7483 | 59 | 59 | PLAIN | - |

#### Street: Ишмурзы Хидиятова (ID: 355)

Кол-во домов: 65

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7506 | 1 | 1 | PLAIN | - |
| 7521 | 2 | 2 | PLAIN | - |
| 7532 | 2А | 2 | LETTER | а |
| 7533 | 3 | 3 | PLAIN | - |
| 7541 | 4 | 4 | PLAIN | - |
| 7551 | 5 | 5 | PLAIN | - |
| 7552 | 5/1 | 5 | FRACTION | 1 |
| 7553 | 5/2 | 5 | FRACTION | 2 |
| 7554 | 5/3 | 5 | FRACTION | 3 |
| 7563 | 6 | 6 | PLAIN | - |
| 7565 | 7 | 7 | PLAIN | - |
| 7567 | 7а | 7 | LETTER | а |
| 7566 | 7/2 | 7 | FRACTION | 2 |
| 7568 | 9 | 9 | PLAIN | - |
| 7569 | 9/1 | 9 | FRACTION | 1 |
| 7570 | 9/3 | 9 | FRACTION | 3 |
| 7507 | 10 | 10 | PLAIN | - |
| 7508 | 10/1 | 10 | FRACTION | 1 |
| 7509 | 11 | 11 | PLAIN | - |
| 7510 | 13 | 13 | PLAIN | - |
| 7511 | 14 | 14 | PLAIN | - |
| 7512 | 15 | 15 | PLAIN | - |
| 7513 | 15/1 | 15 | FRACTION | 1 |
| 7514 | 16 | 16 | PLAIN | - |
| 7515 | 17 | 17 | PLAIN | - |
| 7516 | 18 | 18 | PLAIN | - |
| 7517 | 18/1 | 18 | FRACTION | 1 |
| 7518 | 19 | 19 | PLAIN | - |
| 7519 | 19/1 | 19 | FRACTION | 1 |
| 7520 | 19/2 | 19 | FRACTION | 2 |
| 7522 | 20 | 20 | PLAIN | - |
| 7523 | 21 | 21 | PLAIN | - |
| 7524 | 22 | 22 | PLAIN | - |
| 7525 | 23 | 23 | PLAIN | - |
| 7526 | 23/1 | 23 | FRACTION | 1 |
| 7527 | 25/1 | 25 | FRACTION | 1 |
| 7528 | 26 | 26 | PLAIN | - |
| 7529 | 27 | 27 | PLAIN | - |
| 7530 | 28 | 28 | PLAIN | - |
| 7531 | 29 | 29 | PLAIN | - |
| 7534 | 31 | 31 | PLAIN | - |
| 7535 | 32 | 32 | PLAIN | - |
| 7536 | 33 | 33 | PLAIN | - |
| 7537 | 34 | 34 | PLAIN | - |
| 7538 | 35/1 | 35 | FRACTION | 1 |
| 7539 | 36 | 36 | PLAIN | - |
| 7540 | 38 | 38 | PLAIN | - |
| 7542 | 40 | 40 | PLAIN | - |
| 7543 | 41 | 41 | PLAIN | - |
| 7544 | 42 | 42 | PLAIN | - |
| 7545 | 43 | 43 | PLAIN | - |
| 7546 | 45 | 45 | PLAIN | - |
| 7547 | 46 | 46 | PLAIN | - |
| 7548 | 47 | 47 | PLAIN | - |
| 7549 | 48 | 48 | PLAIN | - |
| 7550 | 49 | 49 | PLAIN | - |
| 7555 | 50 | 50 | PLAIN | - |
| 7556 | 51 | 51 | PLAIN | - |
| 7557 | 52 | 52 | PLAIN | - |
| 7558 | 53 | 53 | PLAIN | - |
| 7559 | 54 | 54 | PLAIN | - |
| 7560 | 56 | 56 | PLAIN | - |
| 7561 | 58 | 58 | PLAIN | - |
| 7562 | 59 | 59 | PLAIN | - |
| 7564 | 61 | 61 | PLAIN | - |

#### Street: Курчатова (ID: 445)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Курьятмас (ID: 363)

Кол-во домов: 39

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7882 | 1 | 1 | PLAIN | - |
| 7883 | 1/1 | 1 | FRACTION | 1 |
| 7894 | 2 | 2 | PLAIN | - |
| 7895 | 2/1 | 2 | FRACTION | 1 |
| 7911 | 4 | 4 | PLAIN | - |
| 7917 | 5 | 5 | PLAIN | - |
| 7919 | 7 | 7 | PLAIN | - |
| 7920 | 9 | 9 | PLAIN | - |
| 7884 | 10 | 10 | PLAIN | - |
| 7885 | 11 | 11 | PLAIN | - |
| 7886 | 12 | 12 | PLAIN | - |
| 7887 | 13 | 13 | PLAIN | - |
| 7888 | 14 | 14 | PLAIN | - |
| 7889 | 15 | 15 | PLAIN | - |
| 7890 | 16/1 | 16 | FRACTION | 1 |
| 7891 | 17 | 17 | PLAIN | - |
| 7892 | 18 | 18 | PLAIN | - |
| 7893 | 19 | 19 | PLAIN | - |
| 7896 | 21 | 21 | PLAIN | - |
| 7897 | 22 | 22 | PLAIN | - |
| 7898 | 23 | 23 | PLAIN | - |
| 7899 | 24 | 24 | PLAIN | - |
| 7900 | 25 | 25 | PLAIN | - |
| 7901 | 26 | 26 | PLAIN | - |
| 7902 | 31 | 31 | PLAIN | - |
| 7903 | 32 | 32 | PLAIN | - |
| 7904 | 33 | 33 | PLAIN | - |
| 7905 | 34 | 34 | PLAIN | - |
| 7906 | 34/1 | 34 | FRACTION | 1 |
| 7907 | 35 | 35 | PLAIN | - |
| 7908 | 37 | 37 | PLAIN | - |
| 7909 | 38 | 38 | PLAIN | - |
| 7910 | 39 | 39 | PLAIN | - |
| 7912 | 41 | 41 | PLAIN | - |
| 7913 | 42/1 | 42 | FRACTION | 1 |
| 7914 | 43 | 43 | PLAIN | - |
| 7915 | 45 | 45 | PLAIN | - |
| 7916 | 49 | 49 | PLAIN | - |
| 7918 | 51 | 51 | PLAIN | - |

#### Street: Луговая (ID: 366)

Кол-во домов: 41

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8058 | 1 | 1 | PLAIN | - |
| 8064 | 2 | 2 | PLAIN | - |
| 8075 | 2а | 2 | LETTER | а |
| 8065 | 2/1 | 2 | FRACTION | 1 |
| 8066 | 2/2 | 2 | FRACTION | 2 |
| 8067 | 2/3 | 2 | FRACTION | 3 |
| 8076 | 3 | 3 | PLAIN | - |
| 8077 | 3/1 | 3 | FRACTION | 1 |
| 8081 | 4 | 4 | PLAIN | - |
| 8082 | 4/2 | 4 | FRACTION | 2 |
| 8087 | 5 | 5 | PLAIN | - |
| 8095 | 6 | 6 | PLAIN | - |
| 8098 | 7 | 7 | PLAIN | - |
| 8059 | 10 | 10 | PLAIN | - |
| 8060 | 12 | 12 | PLAIN | - |
| 8061 | 14 | 14 | PLAIN | - |
| 8062 | 14/1 | 14 | FRACTION | 1 |
| 8063 | 18 | 18 | PLAIN | - |
| 8068 | 20 | 20 | PLAIN | - |
| 8069 | 21 | 21 | PLAIN | - |
| 8070 | 25 | 25 | PLAIN | - |
| 8071 | 25/1 | 25 | FRACTION | 1 |
| 8072 | 26 | 26 | PLAIN | - |
| 8073 | 27 | 27 | PLAIN | - |
| 8074 | 29 | 29 | PLAIN | - |
| 8078 | 31 | 31 | PLAIN | - |
| 8079 | 34 | 34 | PLAIN | - |
| 8080 | 35 | 35 | PLAIN | - |
| 8083 | 41 | 41 | PLAIN | - |
| 8084 | 46 | 46 | PLAIN | - |
| 8085 | 49 | 49 | PLAIN | - |
| 8086 | 49а | 49 | LETTER | а |
| 8088 | 50 | 50 | PLAIN | - |
| 8089 | 52 | 52 | PLAIN | - |
| 8090 | 53 | 53 | PLAIN | - |
| 8091 | 54/2 | 54 | FRACTION | 2 |
| 8092 | 55 | 55 | PLAIN | - |
| 8093 | 57 | 57 | PLAIN | - |
| 8094 | 59 | 59 | PLAIN | - |
| 8096 | 66 | 66 | PLAIN | - |
| 8097 | 68 | 68 | PLAIN | - |

#### Street: Минислама Мирсаяпова (ID: 374)

Кол-во домов: 61

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8266 | 1 | 1 | PLAIN | - |
| 8267 | 1/2 | 1 | FRACTION | 2 |
| 8268 | 1/3 | 1 | FRACTION | 3 |
| 8269 | 1/5 | 1 | FRACTION | 5 |
| 8276 | 2/3 | 2 | FRACTION | 3 |
| 8277 | 2/7 | 2 | FRACTION | 7 |
| 8293 | 5 | 5 | PLAIN | - |
| 8301 | 6 | 6 | PLAIN | - |
| 8316 | 8 | 8 | PLAIN | - |
| 8270 | 11 | 11 | PLAIN | - |
| 8271 | 13 | 13 | PLAIN | - |
| 8272 | 14 | 14 | PLAIN | - |
| 8273 | 15 | 15 | PLAIN | - |
| 8274 | 17 | 17 | PLAIN | - |
| 8275 | 18 | 18 | PLAIN | - |
| 8278 | 20 | 20 | PLAIN | - |
| 8279 | 22 | 22 | PLAIN | - |
| 8280 | 24 | 24 | PLAIN | - |
| 8281 | 25 | 25 | PLAIN | - |
| 8282 | 28 | 28 | PLAIN | - |
| 8283 | 29 | 29 | PLAIN | - |
| 8284 | 30 | 30 | PLAIN | - |
| 8285 | 31 | 31 | PLAIN | - |
| 8286 | 31а | 31 | LETTER | а |
| 8287 | 33 | 33 | PLAIN | - |
| 8288 | 34 | 34 | PLAIN | - |
| 8289 | 42 | 42 | PLAIN | - |
| 8290 | 43 | 43 | PLAIN | - |
| 8291 | 47 | 47 | PLAIN | - |
| 8292 | 48 | 48 | PLAIN | - |
| 8294 | 50 | 50 | PLAIN | - |
| 8296 | 52 | 52 | PLAIN | - |
| 8297 | 54 | 54 | PLAIN | - |
| 8298 | 56 | 56 | PLAIN | - |
| 8299 | 58 | 58 | PLAIN | - |
| 8300 | 59 | 59 | PLAIN | - |
| 8302 | 60 | 60 | PLAIN | - |
| 8303 | 61 | 61 | PLAIN | - |
| 8304 | 62 | 62 | PLAIN | - |
| 8305 | 63 | 63 | PLAIN | - |
| 8306 | 64 | 64 | PLAIN | - |
| 8307 | 65 | 65 | PLAIN | - |
| 8308 | 69 | 69 | PLAIN | - |
| 8309 | 70 | 70 | PLAIN | - |
| 8310 | 71 | 71 | PLAIN | - |
| 8311 | 73 | 73 | PLAIN | - |
| 8312 | 74 | 74 | PLAIN | - |
| 8313 | 75 | 75 | PLAIN | - |
| 8314 | 77 | 77 | PLAIN | - |
| 8315 | 79 | 79 | PLAIN | - |
| 8317 | 80 | 80 | PLAIN | - |
| 8318 | 82 | 82 | PLAIN | - |
| 8319 | 83 | 83 | PLAIN | - |
| 8320 | 84 | 84 | PLAIN | - |
| 8321 | 85 | 85 | PLAIN | - |
| 8322 | 87 | 87 | PLAIN | - |
| 8323 | 88 | 88 | PLAIN | - |
| 8324 | 89 | 89 | PLAIN | - |
| 8325 | 94 | 94 | PLAIN | - |
| 8326 | 95 | 95 | PLAIN | - |
| 8295 | 507к4 | 507 | CORPUS | 4 |

#### Street: Мисаля Муртасина (ID: 452)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Мурзахана Шамсутдинова (ID: 378)

Кол-во домов: 8

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8449 | 34 | 34 | PLAIN | - |
| 8450 | 48 | 48 | PLAIN | - |
| 8451 | 50 | 50 | PLAIN | - |
| 8452 | 56 | 56 | PLAIN | - |
| 8453 | 58 | 58 | PLAIN | - |
| 8454 | 61 | 61 | PLAIN | - |
| 8455 | 65 | 65 | PLAIN | - |
| 8456 | 67 | 67 | PLAIN | - |

#### Street: Нажипа Асанбаева (ID: 448)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Пятая (ID: 384)

Кол-во домов: 32

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8631 | 1 | 1 | PLAIN | - |
| 8632 | 1/3 | 1 | FRACTION | 3 |
| 8633 | 1/7 | 1 | FRACTION | 7 |
| 8634 | 1/9 | 1 | FRACTION | 9 |
| 8647 | 3 | 3 | PLAIN | - |
| 8654 | 4 | 4 | PLAIN | - |
| 8658 | 5 | 5 | PLAIN | - |
| 8660 | 6 | 6 | PLAIN | - |
| 8661 | 7 | 7 | PLAIN | - |
| 8662 | 9 | 9 | PLAIN | - |
| 8635 | 10 | 10 | PLAIN | - |
| 8636 | 14 | 14 | PLAIN | - |
| 8637 | 15 | 15 | PLAIN | - |
| 8638 | 16 | 16 | PLAIN | - |
| 8639 | 17 | 17 | PLAIN | - |
| 8640 | 19 | 19 | PLAIN | - |
| 8641 | 21 | 21 | PLAIN | - |
| 8642 | 22 | 22 | PLAIN | - |
| 8643 | 23 | 23 | PLAIN | - |
| 8644 | 24 | 24 | PLAIN | - |
| 8645 | 26 | 26 | PLAIN | - |
| 8646 | 29 | 29 | PLAIN | - |
| 8648 | 34 | 34 | PLAIN | - |
| 8649 | 35 | 35 | PLAIN | - |
| 8650 | 36 | 36 | PLAIN | - |
| 8651 | 37 | 37 | PLAIN | - |
| 8652 | 38 | 38 | PLAIN | - |
| 8653 | 39 | 39 | PLAIN | - |
| 8655 | 43 | 43 | PLAIN | - |
| 8656 | 45 | 45 | PLAIN | - |
| 8657 | 47 | 47 | PLAIN | - |
| 8659 | 51 | 51 | PLAIN | - |

#### Street: Раиса Усманова (ID: 385)

Кол-во домов: 52

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8663 | 1/1 | 1 | FRACTION | 1 |
| 8664 | 1/10 | 1 | FRACTION | 10 |
| 8665 | 1/2 | 1 | FRACTION | 2 |
| 8666 | 1/3 | 1 | FRACTION | 3 |
| 8667 | 1/6 | 1 | FRACTION | 6 |
| 8668 | 1/7 | 1 | FRACTION | 7 |
| 8669 | 1/9 | 1 | FRACTION | 9 |
| 8684 | 2 | 2 | PLAIN | - |
| 8685 | 2/1 | 2 | FRACTION | 1 |
| 8686 | 2/10 | 2 | FRACTION | 10 |
| 8687 | 2/6 | 2 | FRACTION | 6 |
| 8710 | 5 | 5 | PLAIN | - |
| 8712 | 6 | 6 | PLAIN | - |
| 8713 | 8 | 8 | PLAIN | - |
| 8714 | 9 | 9 | PLAIN | - |
| 8670 | 10 | 10 | PLAIN | - |
| 8671 | 12 | 12 | PLAIN | - |
| 8672 | 13 | 13 | PLAIN | - |
| 8673 | 14 | 14 | PLAIN | - |
| 8674 | 15/2 | 15 | FRACTION | 2 |
| 8675 | 16 | 16 | PLAIN | - |
| 8676 | 16/1 | 16 | FRACTION | 1 |
| 8677 | 16/3 | 16 | FRACTION | 3 |
| 8678 | 17 | 17 | PLAIN | - |
| 8679 | 17/1 | 17 | FRACTION | 1 |
| 8680 | 17/2 | 17 | FRACTION | 2 |
| 8681 | 18 | 18 | PLAIN | - |
| 8682 | 18/2 | 18 | FRACTION | 2 |
| 8683 | 19 | 19 | PLAIN | - |
| 8688 | 20 | 20 | PLAIN | - |
| 8689 | 22 | 22 | PLAIN | - |
| 8690 | 23 | 23 | PLAIN | - |
| 8691 | 24 | 24 | PLAIN | - |
| 8692 | 25 | 25 | PLAIN | - |
| 8693 | 26 | 26 | PLAIN | - |
| 8694 | 27 | 27 | PLAIN | - |
| 8695 | 28 | 28 | PLAIN | - |
| 8696 | 29 | 29 | PLAIN | - |
| 8697 | 30 | 30 | PLAIN | - |
| 8698 | 31 | 31 | PLAIN | - |
| 8699 | 32 | 32 | PLAIN | - |
| 8700 | 37 | 37 | PLAIN | - |
| 8701 | 39 | 39 | PLAIN | - |
| 8702 | 40 | 40 | PLAIN | - |
| 8703 | 41 | 41 | PLAIN | - |
| 8704 | 42 | 42 | PLAIN | - |
| 8705 | 43 | 43 | PLAIN | - |
| 8706 | 44 | 44 | PLAIN | - |
| 8707 | 45 | 45 | PLAIN | - |
| 8708 | 47 | 47 | PLAIN | - |
| 8709 | 49 | 49 | PLAIN | - |
| 8711 | 52 | 52 | PLAIN | - |

#### Street: Рамазана Уметбаева (ID: 443)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Рами Гарипова (ID: 449)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Рафика Сальманова (ID: 389)

Кол-во домов: 62

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8862 | 1/3 | 1 | FRACTION | 3 |
| 8876 | 3 | 3 | PLAIN | - |
| 8893 | 5 | 5 | PLAIN | - |
| 8909 | 7 | 7 | PLAIN | - |
| 8915 | 8 | 8 | PLAIN | - |
| 8922 | 9 | 9 | PLAIN | - |
| 8863 | 11 | 11 | PLAIN | - |
| 8864 | 12 | 12 | PLAIN | - |
| 8865 | 13 | 13 | PLAIN | - |
| 8866 | 14 | 14 | PLAIN | - |
| 8867 | 17 | 17 | PLAIN | - |
| 8868 | 18 | 18 | PLAIN | - |
| 8869 | 19 | 19 | PLAIN | - |
| 8870 | 22 | 22 | PLAIN | - |
| 8871 | 23 | 23 | PLAIN | - |
| 8872 | 24 | 24 | PLAIN | - |
| 8873 | 26 | 26 | PLAIN | - |
| 8874 | 27 | 27 | PLAIN | - |
| 8875 | 29 | 29 | PLAIN | - |
| 8877 | 30 | 30 | PLAIN | - |
| 8878 | 31 | 31 | PLAIN | - |
| 8879 | 32 | 32 | PLAIN | - |
| 8880 | 33 | 33 | PLAIN | - |
| 8881 | 36 | 36 | PLAIN | - |
| 8882 | 37 | 37 | PLAIN | - |
| 8883 | 38 | 38 | PLAIN | - |
| 8884 | 39 | 39 | PLAIN | - |
| 8885 | 41 | 41 | PLAIN | - |
| 8886 | 42 | 42 | PLAIN | - |
| 8887 | 43 | 43 | PLAIN | - |
| 8888 | 44 | 44 | PLAIN | - |
| 8889 | 45 | 45 | PLAIN | - |
| 8890 | 47 | 47 | PLAIN | - |
| 8891 | 48 | 48 | PLAIN | - |
| 8892 | 49 | 49 | PLAIN | - |
| 8894 | 50 | 50 | PLAIN | - |
| 8895 | 51 | 51 | PLAIN | - |
| 8896 | 52 | 52 | PLAIN | - |
| 8897 | 53 | 53 | PLAIN | - |
| 8898 | 54 | 54 | PLAIN | - |
| 8899 | 55 | 55 | PLAIN | - |
| 8900 | 56 | 56 | PLAIN | - |
| 8901 | 59 | 59 | PLAIN | - |
| 8902 | 61 | 61 | PLAIN | - |
| 8903 | 62 | 62 | PLAIN | - |
| 8904 | 63 | 63 | PLAIN | - |
| 8905 | 64 | 64 | PLAIN | - |
| 8906 | 65 | 65 | PLAIN | - |
| 8907 | 66 | 66 | PLAIN | - |
| 8908 | 69 | 69 | PLAIN | - |
| 8910 | 70 | 70 | PLAIN | - |
| 8911 | 72 | 72 | PLAIN | - |
| 8912 | 75 | 75 | PLAIN | - |
| 8913 | 76 | 76 | PLAIN | - |
| 8914 | 77 | 77 | PLAIN | - |
| 8916 | 80 | 80 | PLAIN | - |
| 8917 | 81/1 | 81 | FRACTION | 1 |
| 8918 | 83 | 83 | PLAIN | - |
| 8919 | 84 | 84 | PLAIN | - |
| 8920 | 86 | 86 | PLAIN | - |
| 8921 | 87 | 87 | PLAIN | - |
| 8923 | 90 | 90 | PLAIN | - |

#### Street: Сагиры Мишар (ID: 446)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Садовая (ID: 391)

Кол-во домов: 52

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8990 | 1 | 1 | PLAIN | - |
| 9006 | 1а | 1 | LETTER | а |
| 8991 | 1/1 | 1 | FRACTION | 1 |
| 9007 | 2 | 2 | PLAIN | - |
| 9019 | 3 | 3 | PLAIN | - |
| 9038 | 6 | 6 | PLAIN | - |
| 9039 | 7/1 | 7 | FRACTION | 1 |
| 9040 | 8 | 8 | PLAIN | - |
| 9041 | 9 | 9 | PLAIN | - |
| 8992 | 10 | 10 | PLAIN | - |
| 8993 | 11 | 11 | PLAIN | - |
| 8994 | 12 | 12 | PLAIN | - |
| 8995 | 13 | 13 | PLAIN | - |
| 8996 | 14 | 14 | PLAIN | - |
| 8997 | 14/1 | 14 | FRACTION | 1 |
| 8998 | 15 | 15 | PLAIN | - |
| 8999 | 16 | 16 | PLAIN | - |
| 9000 | 16/1 | 16 | FRACTION | 1 |
| 9001 | 17 | 17 | PLAIN | - |
| 9002 | 19 | 19 | PLAIN | - |
| 9003 | 19/1 | 19 | FRACTION | 1 |
| 9004 | 19/2 | 19 | FRACTION | 2 |
| 9005 | 19/4 | 19 | FRACTION | 4 |
| 9008 | 20 | 20 | PLAIN | - |
| 9009 | 21 | 21 | PLAIN | - |
| 9010 | 21/2 | 21 | FRACTION | 2 |
| 9011 | 22 | 22 | PLAIN | - |
| 9012 | 23 | 23 | PLAIN | - |
| 9013 | 24 | 24 | PLAIN | - |
| 9014 | 25 | 25 | PLAIN | - |
| 9015 | 26 | 26 | PLAIN | - |
| 9016 | 27 | 27 | PLAIN | - |
| 9017 | 28 | 28 | PLAIN | - |
| 9018 | 29 | 29 | PLAIN | - |
| 9020 | 30 | 30 | PLAIN | - |
| 9021 | 31 | 31 | PLAIN | - |
| 9022 | 32 | 32 | PLAIN | - |
| 9023 | 33 | 33 | PLAIN | - |
| 9024 | 34 | 34 | PLAIN | - |
| 9025 | 35 | 35 | PLAIN | - |
| 9026 | 36 | 36 | PLAIN | - |
| 9027 | 37 | 37 | PLAIN | - |
| 9028 | 40 | 40 | PLAIN | - |
| 9029 | 42 | 42 | PLAIN | - |
| 9030 | 43 | 43 | PLAIN | - |
| 9031 | 45 | 45 | PLAIN | - |
| 9032 | 46 | 46 | PLAIN | - |
| 9033 | 47 | 47 | PLAIN | - |
| 9034 | 48 | 48 | PLAIN | - |
| 9035 | 49 | 49 | PLAIN | - |
| 9036 | 52 | 52 | PLAIN | - |
| 9037 | 53 | 53 | PLAIN | - |

#### Street: Салавата Кадырова (ID: 392)

Кол-во домов: 2

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9042 | 17 | 17 | PLAIN | - |
| 9043 | 38 | 38 | PLAIN | - |

#### Street: Сарии Миржановой (ID: 394)

Кол-во домов: 57

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9091 | 1 | 1 | PLAIN | - |
| 9108 | 1а | 1 | LETTER | а |
| 9109 | 1б | 1 | LETTER | б |
| 9092 | 1/2 | 1 | FRACTION | 2 |
| 9110 | 2 | 2 | PLAIN | - |
| 9123 | 2а | 2 | LETTER | а |
| 9111 | 2/1 | 2 | FRACTION | 1 |
| 9124 | 3/1 | 3 | FRACTION | 1 |
| 9140 | 5 | 5 | PLAIN | - |
| 9145 | 6 | 6 | PLAIN | - |
| 9146 | 7 | 7 | PLAIN | - |
| 9147 | 9 | 9 | PLAIN | - |
| 9093 | 11 | 11 | PLAIN | - |
| 9094 | 12 | 12 | PLAIN | - |
| 9095 | 13 | 13 | PLAIN | - |
| 9096 | 14 | 14 | PLAIN | - |
| 9097 | 15/1 | 15 | FRACTION | 1 |
| 9098 | 16 | 16 | PLAIN | - |
| 9099 | 16/1 | 16 | FRACTION | 1 |
| 9100 | 16/2 | 16 | FRACTION | 2 |
| 9101 | 16/3 | 16 | FRACTION | 3 |
| 9102 | 17 | 17 | PLAIN | - |
| 9103 | 17/2 | 17 | FRACTION | 2 |
| 9104 | 17/3 | 17 | FRACTION | 3 |
| 9105 | 18/1 | 18 | FRACTION | 1 |
| 9106 | 18/2 | 18 | FRACTION | 2 |
| 9107 | 19 | 19 | PLAIN | - |
| 9113 | 20 | 20 | PLAIN | - |
| 9114 | 21 | 21 | PLAIN | - |
| 9115 | 22 | 22 | PLAIN | - |
| 9116 | 23 | 23 | PLAIN | - |
| 9117 | 24 | 24 | PLAIN | - |
| 9118 | 25 | 25 | PLAIN | - |
| 9119 | 26 | 26 | PLAIN | - |
| 9120 | 27 | 27 | PLAIN | - |
| 9121 | 28 | 28 | PLAIN | - |
| 9122 | 29 | 29 | PLAIN | - |
| 9125 | 30 | 30 | PLAIN | - |
| 9126 | 31 | 31 | PLAIN | - |
| 9127 | 32 | 32 | PLAIN | - |
| 9128 | 33 | 33 | PLAIN | - |
| 9129 | 34 | 34 | PLAIN | - |
| 9130 | 36 | 36 | PLAIN | - |
| 9131 | 38 | 38 | PLAIN | - |
| 9132 | 39 | 39 | PLAIN | - |
| 9133 | 40 | 40 | PLAIN | - |
| 9134 | 41 | 41 | PLAIN | - |
| 9135 | 44 | 44 | PLAIN | - |
| 9136 | 45 | 45 | PLAIN | - |
| 9137 | 46 | 46 | PLAIN | - |
| 9138 | 47 | 47 | PLAIN | - |
| 9139 | 48 | 48 | PLAIN | - |
| 9141 | 50 | 50 | PLAIN | - |
| 9142 | 50/1 | 50 | FRACTION | 1 |
| 9143 | 51 | 51 | PLAIN | - |
| 9144 | 52 | 52 | PLAIN | - |
| 9112 | 2/1а | — | UNPARSEABLE | - |

#### Street: Солнечная (ID: 397)

Кол-во домов: 36

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9202 | 1 | 1 | PLAIN | - |
| 9208 | 2 | 2 | PLAIN | - |
| 9215 | 3 | 3 | PLAIN | - |
| 9225 | 5 | 5 | PLAIN | - |
| 9231 | 7/1 | 7 | FRACTION | 1 |
| 9236 | 8 | 8 | PLAIN | - |
| 9237 | 9 | 9 | PLAIN | - |
| 9203 | 10 | 10 | PLAIN | - |
| 9204 | 16 | 16 | PLAIN | - |
| 9205 | 17/1 | 17 | FRACTION | 1 |
| 9206 | 18 | 18 | PLAIN | - |
| 9207 | 19 | 19 | PLAIN | - |
| 9209 | 20 | 20 | PLAIN | - |
| 9210 | 21 | 21 | PLAIN | - |
| 9211 | 25 | 25 | PLAIN | - |
| 9212 | 26 | 26 | PLAIN | - |
| 9213 | 28 | 28 | PLAIN | - |
| 9214 | 29 | 29 | PLAIN | - |
| 9216 | 31 | 31 | PLAIN | - |
| 9217 | 32 | 32 | PLAIN | - |
| 9218 | 33 | 33 | PLAIN | - |
| 9219 | 35 | 35 | PLAIN | - |
| 9220 | 38 | 38 | PLAIN | - |
| 9221 | 39 | 39 | PLAIN | - |
| 9222 | 40 | 40 | PLAIN | - |
| 9223 | 41 | 41 | PLAIN | - |
| 9224 | 49 | 49 | PLAIN | - |
| 9226 | 50 | 50 | PLAIN | - |
| 9227 | 50/1 | 50 | FRACTION | 1 |
| 9228 | 53 | 53 | PLAIN | - |
| 9229 | 57 | 57 | PLAIN | - |
| 9230 | 59 | 59 | PLAIN | - |
| 9232 | 73 | 73 | PLAIN | - |
| 9233 | 77 | 77 | PLAIN | - |
| 9234 | 78 | 78 | PLAIN | - |
| 9235 | 79 | 79 | PLAIN | - |

#### Street: Тамьян (ID: 401)

Кол-во домов: 43

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9293 | 1/1 | 1 | FRACTION | 1 |
| 9307 | 2/1 | 2 | FRACTION | 1 |
| 9308 | 2/2 | 2 | FRACTION | 2 |
| 9316 | 3 | 3 | PLAIN | - |
| 9325 | 4 | 4 | PLAIN | - |
| 9333 | 6 | 6 | PLAIN | - |
| 9334 | 7 | 7 | PLAIN | - |
| 9335 | 9 | 9 | PLAIN | - |
| 9294 | 10 | 10 | PLAIN | - |
| 9295 | 13 | 13 | PLAIN | - |
| 9296 | 14 | 14 | PLAIN | - |
| 9297 | 15 | 15 | PLAIN | - |
| 9298 | 16/1 | 16 | FRACTION | 1 |
| 9299 | 16/2 | 16 | FRACTION | 2 |
| 9300 | 17 | 17 | PLAIN | - |
| 9301 | 17/1 | 17 | FRACTION | 1 |
| 9302 | 18 | 18 | PLAIN | - |
| 9303 | 18/1 | 18 | FRACTION | 1 |
| 9304 | 18/2 | 18 | FRACTION | 2 |
| 9305 | 18/3 | 18 | FRACTION | 3 |
| 9306 | 19 | 19 | PLAIN | - |
| 9309 | 20 | 20 | PLAIN | - |
| 9310 | 20/1 | 20 | FRACTION | 1 |
| 9311 | 21 | 21 | PLAIN | - |
| 9312 | 22 | 22 | PLAIN | - |
| 9313 | 23 | 23 | PLAIN | - |
| 9314 | 25 | 25 | PLAIN | - |
| 9315 | 27 | 27 | PLAIN | - |
| 9317 | 30 | 30 | PLAIN | - |
| 9318 | 31 | 31 | PLAIN | - |
| 9319 | 33 | 33 | PLAIN | - |
| 9320 | 34 | 34 | PLAIN | - |
| 9321 | 35 | 35 | PLAIN | - |
| 9322 | 36 | 36 | PLAIN | - |
| 9323 | 37 | 37 | PLAIN | - |
| 9324 | 38 | 38 | PLAIN | - |
| 9326 | 40 | 40 | PLAIN | - |
| 9327 | 41 | 41 | PLAIN | - |
| 9328 | 42 | 42 | PLAIN | - |
| 9329 | 43 | 43 | PLAIN | - |
| 9330 | 46 | 46 | PLAIN | - |
| 9331 | 53 | 53 | PLAIN | - |
| 9332 | 54 | 54 | PLAIN | - |

#### Street: Тукая (ID: 447)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Тунгаур (ID: 403)

Кол-во домов: 58

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9390 | 1 | 1 | PLAIN | - |
| 9391 | 1/1 | 1 | FRACTION | 1 |
| 9392 | 1/2 | 1 | FRACTION | 2 |
| 9393 | 1/3 | 1 | FRACTION | 3 |
| 9412 | 2/1 | 2 | FRACTION | 1 |
| 9413 | 2/11 | 2 | FRACTION | 11 |
| 9414 | 2/3 | 2 | FRACTION | 3 |
| 9415 | 2/4 | 2 | FRACTION | 4 |
| 9416 | 2/5 | 2 | FRACTION | 5 |
| 9417 | 2/7 | 2 | FRACTION | 7 |
| 9426 | 3 | 3 | PLAIN | - |
| 9441 | 5 | 5 | PLAIN | - |
| 9444 | 6 | 6 | PLAIN | - |
| 9445 | 7 | 7 | PLAIN | - |
| 9446 | 8 | 8 | PLAIN | - |
| 9447 | 9 | 9 | PLAIN | - |
| 9394 | 10 | 10 | PLAIN | - |
| 9395 | 11 | 11 | PLAIN | - |
| 9396 | 12 | 12 | PLAIN | - |
| 9397 | 13 | 13 | PLAIN | - |
| 9398 | 14 | 14 | PLAIN | - |
| 9399 | 14/1 | 14 | FRACTION | 1 |
| 9400 | 15 | 15 | PLAIN | - |
| 9401 | 15/1 | 15 | FRACTION | 1 |
| 9402 | 15/2 | 15 | FRACTION | 2 |
| 9403 | 15/3 | 15 | FRACTION | 3 |
| 9404 | 16/1 | 16 | FRACTION | 1 |
| 9405 | 16/3 | 16 | FRACTION | 3 |
| 9406 | 17 | 17 | PLAIN | - |
| 9407 | 17/1 | 17 | FRACTION | 1 |
| 9408 | 17/2 | 17 | FRACTION | 2 |
| 9409 | 18/1 | 18 | FRACTION | 1 |
| 9410 | 18/2 | 18 | FRACTION | 2 |
| 9411 | 19 | 19 | PLAIN | - |
| 9418 | 21 | 21 | PLAIN | - |
| 9419 | 22 | 22 | PLAIN | - |
| 9420 | 23 | 23 | PLAIN | - |
| 9421 | 23/1 | 23 | FRACTION | 1 |
| 9422 | 25 | 25 | PLAIN | - |
| 9423 | 26 | 26 | PLAIN | - |
| 9424 | 27 | 27 | PLAIN | - |
| 9425 | 28 | 28 | PLAIN | - |
| 9427 | 30 | 30 | PLAIN | - |
| 9428 | 31 | 31 | PLAIN | - |
| 9429 | 32 | 32 | PLAIN | - |
| 9430 | 33 | 33 | PLAIN | - |
| 9431 | 34 | 34 | PLAIN | - |
| 9432 | 35 | 35 | PLAIN | - |
| 9433 | 35/1 | 35 | FRACTION | 1 |
| 9434 | 38 | 38 | PLAIN | - |
| 9435 | 40 | 40 | PLAIN | - |
| 9436 | 41 | 41 | PLAIN | - |
| 9437 | 42 | 42 | PLAIN | - |
| 9438 | 43 | 43 | PLAIN | - |
| 9439 | 44 | 44 | PLAIN | - |
| 9440 | 46 | 46 | PLAIN | - |
| 9442 | 52 | 52 | PLAIN | - |
| 9443 | 53 | 53 | PLAIN | - |

#### Street: Фазиля Искандера (ID: 444)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Файзи Гаскарова (ID: 407)

Кол-во домов: 63

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9522 | 1 | 1 | PLAIN | - |
| 9537 | 1А | 1 | LETTER | а |
| 9523 | 1/1 | 1 | FRACTION | 1 |
| 9524 | 1/2 | 1 | FRACTION | 2 |
| 9538 | 2 | 2 | PLAIN | - |
| 9551 | 3 | 3 | PLAIN | - |
| 9562 | 4 | 4 | PLAIN | - |
| 9573 | 5 | 5 | PLAIN | - |
| 9581 | 6 | 6 | PLAIN | - |
| 9582 | 7 | 7 | PLAIN | - |
| 9583 | 8 | 8 | PLAIN | - |
| 9584 | 9 | 9 | PLAIN | - |
| 9525 | 10 | 10 | PLAIN | - |
| 9526 | 11 | 11 | PLAIN | - |
| 9527 | 12 | 12 | PLAIN | - |
| 9528 | 13 | 13 | PLAIN | - |
| 9529 | 15 | 15 | PLAIN | - |
| 9530 | 15/1 | 15 | FRACTION | 1 |
| 9531 | 16 | 16 | PLAIN | - |
| 9532 | 17/1 | 17 | FRACTION | 1 |
| 9533 | 18 | 18 | PLAIN | - |
| 9534 | 18/1 | 18 | FRACTION | 1 |
| 9535 | 19 | 19 | PLAIN | - |
| 9536 | 19/2 | 19 | FRACTION | 2 |
| 9539 | 20 | 20 | PLAIN | - |
| 9540 | 20/3 | 20 | FRACTION | 3 |
| 9541 | 21 | 21 | PLAIN | - |
| 9542 | 21/1 | 21 | FRACTION | 1 |
| 9543 | 22 | 22 | PLAIN | - |
| 9544 | 23 | 23 | PLAIN | - |
| 9545 | 24 | 24 | PLAIN | - |
| 9546 | 25 | 25 | PLAIN | - |
| 9547 | 26 | 26 | PLAIN | - |
| 9548 | 27 | 27 | PLAIN | - |
| 9549 | 28 | 28 | PLAIN | - |
| 9550 | 29 | 29 | PLAIN | - |
| 9552 | 30 | 30 | PLAIN | - |
| 9553 | 31 | 31 | PLAIN | - |
| 9554 | 32 | 32 | PLAIN | - |
| 9555 | 33 | 33 | PLAIN | - |
| 9556 | 34 | 34 | PLAIN | - |
| 9557 | 35 | 35 | PLAIN | - |
| 9558 | 36 | 36 | PLAIN | - |
| 9559 | 37 | 37 | PLAIN | - |
| 9560 | 38 | 38 | PLAIN | - |
| 9561 | 39 | 39 | PLAIN | - |
| 9563 | 40 | 40 | PLAIN | - |
| 9564 | 41 | 41 | PLAIN | - |
| 9565 | 42 | 42 | PLAIN | - |
| 9566 | 43 | 43 | PLAIN | - |
| 9567 | 44 | 44 | PLAIN | - |
| 9568 | 45 | 45 | PLAIN | - |
| 9569 | 46 | 46 | PLAIN | - |
| 9570 | 47 | 47 | PLAIN | - |
| 9571 | 48 | 48 | PLAIN | - |
| 9572 | 49 | 49 | PLAIN | - |
| 9574 | 50 | 50 | PLAIN | - |
| 9575 | 51 | 51 | PLAIN | - |
| 9576 | 53 | 53 | PLAIN | - |
| 9577 | 55 | 55 | PLAIN | - |
| 9578 | 57 | 57 | PLAIN | - |
| 9579 | 57/1 | 57 | FRACTION | 1 |
| 9580 | 57/4 | 57 | FRACTION | 4 |

#### Street: Хадии Давлетшиной (ID: 411)

Кол-во домов: 67

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9731 | 1 | 1 | PLAIN | - |
| 9751 | 3 | 3 | PLAIN | - |
| 9779 | 6 | 6 | PLAIN | - |
| 9786 | 7 | 7 | PLAIN | - |
| 9792 | 8 | 8 | PLAIN | - |
| 9796 | 9 | 9 | PLAIN | - |
| 9732 | 10 | 10 | PLAIN | - |
| 9733 | 11 | 11 | PLAIN | - |
| 9734 | 12 | 12 | PLAIN | - |
| 9735 | 13 | 13 | PLAIN | - |
| 9736 | 14 | 14 | PLAIN | - |
| 9737 | 15 | 15 | PLAIN | - |
| 9738 | 17 | 17 | PLAIN | - |
| 9739 | 18 | 18 | PLAIN | - |
| 9740 | 19 | 19 | PLAIN | - |
| 9741 | 20 | 20 | PLAIN | - |
| 9742 | 21 | 21 | PLAIN | - |
| 9743 | 22 | 22 | PLAIN | - |
| 9744 | 24 | 24 | PLAIN | - |
| 9745 | 25 | 25 | PLAIN | - |
| 9746 | 26 | 26 | PLAIN | - |
| 9747 | 27 | 27 | PLAIN | - |
| 9748 | 27/2 | 27 | FRACTION | 2 |
| 9749 | 28 | 28 | PLAIN | - |
| 9750 | 29 | 29 | PLAIN | - |
| 9752 | 30 | 30 | PLAIN | - |
| 9753 | 31 | 31 | PLAIN | - |
| 9754 | 33 | 33 | PLAIN | - |
| 9755 | 34 | 34 | PLAIN | - |
| 9756 | 35 | 35 | PLAIN | - |
| 9757 | 36 | 36 | PLAIN | - |
| 9758 | 37 | 37 | PLAIN | - |
| 9759 | 38 | 38 | PLAIN | - |
| 9760 | 40 | 40 | PLAIN | - |
| 9761 | 41 | 41 | PLAIN | - |
| 9762 | 42 | 42 | PLAIN | - |
| 9763 | 43 | 43 | PLAIN | - |
| 9764 | 44 | 44 | PLAIN | - |
| 9765 | 45 | 45 | PLAIN | - |
| 9766 | 46 | 46 | PLAIN | - |
| 9767 | 46/1 | 46 | FRACTION | 1 |
| 9768 | 47 | 47 | PLAIN | - |
| 9769 | 48 | 48 | PLAIN | - |
| 9770 | 49 | 49 | PLAIN | - |
| 9771 | 50 | 50 | PLAIN | - |
| 9772 | 51 | 51 | PLAIN | - |
| 9773 | 52 | 52 | PLAIN | - |
| 9774 | 53 | 53 | PLAIN | - |
| 9775 | 54 | 54 | PLAIN | - |
| 9776 | 56 | 56 | PLAIN | - |
| 9777 | 57 | 57 | PLAIN | - |
| 9778 | 59 | 59 | PLAIN | - |
| 9780 | 61 | 61 | PLAIN | - |
| 9781 | 62 | 62 | PLAIN | - |
| 9782 | 63 | 63 | PLAIN | - |
| 9783 | 64 | 64 | PLAIN | - |
| 9784 | 65 | 65 | PLAIN | - |
| 9785 | 68 | 68 | PLAIN | - |
| 9787 | 72 | 72 | PLAIN | - |
| 9788 | 75 | 75 | PLAIN | - |
| 9789 | 77 | 77 | PLAIN | - |
| 9790 | 78 | 78 | PLAIN | - |
| 9791 | 79 | 79 | PLAIN | - |
| 9793 | 83 | 83 | PLAIN | - |
| 9794 | 86 | 86 | PLAIN | - |
| 9795 | 87 | 87 | PLAIN | - |
| 9797 | 90 | 90 | PLAIN | - |

#### Street: Целинная (ID: 412)

Кол-во домов: 56

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9808 | 1а | 1 | LETTER | а |
| 9798 | 1/4 | 1 | FRACTION | 4 |
| 9799 | 1/6 | 1 | FRACTION | 6 |
| 9800 | 1/7 | 1 | FRACTION | 7 |
| 9801 | 1/8 | 1 | FRACTION | 8 |
| 9802 | 1/9 | 1 | FRACTION | 9 |
| 9809 | 2 | 2 | PLAIN | - |
| 9810 | 2/4 | 2 | FRACTION | 4 |
| 9811 | 2/5 | 2 | FRACTION | 5 |
| 9812 | 2/7 | 2 | FRACTION | 7 |
| 9813 | 2/8 | 2 | FRACTION | 8 |
| 9828 | 4 | 4 | PLAIN | - |
| 9835 | 5 | 5 | PLAIN | - |
| 9846 | 7 | 7 | PLAIN | - |
| 9853 | 8 | 8 | PLAIN | - |
| 9803 | 11 | 11 | PLAIN | - |
| 9804 | 12 | 12 | PLAIN | - |
| 9805 | 14 | 14 | PLAIN | - |
| 9806 | 15 | 15 | PLAIN | - |
| 9807 | 17 | 17 | PLAIN | - |
| 9814 | 20/1 | 20 | FRACTION | 1 |
| 9815 | 21 | 21 | PLAIN | - |
| 9816 | 21А | 21 | LETTER | а |
| 9817 | 22 | 22 | PLAIN | - |
| 9818 | 27 | 27 | PLAIN | - |
| 9819 | 28 | 28 | PLAIN | - |
| 9820 | 29 | 29 | PLAIN | - |
| 9821 | 30 | 30 | PLAIN | - |
| 9822 | 31 | 31 | PLAIN | - |
| 9823 | 33 | 33 | PLAIN | - |
| 9824 | 34 | 34 | PLAIN | - |
| 9825 | 35 | 35 | PLAIN | - |
| 9826 | 36 | 36 | PLAIN | - |
| 9827 | 38 | 38 | PLAIN | - |
| 9829 | 42 | 42 | PLAIN | - |
| 9830 | 44 | 44 | PLAIN | - |
| 9831 | 46 | 46 | PLAIN | - |
| 9832 | 47 | 47 | PLAIN | - |
| 9833 | 48 | 48 | PLAIN | - |
| 9834 | 49 | 49 | PLAIN | - |
| 9836 | 53 | 53 | PLAIN | - |
| 9837 | 56 | 56 | PLAIN | - |
| 9838 | 57 | 57 | PLAIN | - |
| 9839 | 58 | 58 | PLAIN | - |
| 9840 | 59 | 59 | PLAIN | - |
| 9841 | 60 | 60 | PLAIN | - |
| 9842 | 62 | 62 | PLAIN | - |
| 9843 | 66 | 66 | PLAIN | - |
| 9844 | 68 | 68 | PLAIN | - |
| 9845 | 69 | 69 | PLAIN | - |
| 9847 | 70 | 70 | PLAIN | - |
| 9848 | 71 | 71 | PLAIN | - |
| 9849 | 72 | 72 | PLAIN | - |
| 9850 | 73 | 73 | PLAIN | - |
| 9851 | 74 | 74 | PLAIN | - |
| 9852 | 76 | 76 | PLAIN | - |

#### Street: Шаймуратова (ID: 442)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

### District: Даутово (ID: 24)

#### Street: 10 лет Победы (ID: 454)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: 60 лет Победы (ID: 455)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: 8 Марта (ID: 453)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Абзелиловская (ID: 456)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Александра Пушкина (ID: 457)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Гайфуллы Сарбаева (ID: 458)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Георгия Васева (ID: 459)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Караташ (ID: 460)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Кизильская (ID: 461)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Кинзи Арсланова (ID: 462)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Кыркты-Тау (ID: 463)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Михаила Лермонтова (ID: 464)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Мусы Гареева (ID: 380)

Кол-во домов: 13

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8518 | 1 | 1 | PLAIN | - |
| 8523 | 2 | 2 | PLAIN | - |
| 8524 | 3 | 3 | PLAIN | - |
| 8525 | 4 | 4 | PLAIN | - |
| 8526 | 5 | 5 | PLAIN | - |
| 8527 | 6 | 6 | PLAIN | - |
| 8528 | 7 | 7 | PLAIN | - |
| 8529 | 8 | 8 | PLAIN | - |
| 8530 | 9 | 9 | PLAIN | - |
| 8519 | 10 | 10 | PLAIN | - |
| 8520 | 11 | 11 | PLAIN | - |
| 8521 | 12 | 12 | PLAIN | - |
| 8522 | 13 | 13 | PLAIN | - |

#### Street: Мусы Джалиля (ID: 465)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Нургали Фахретдинова (ID: 466)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Рауфа Давлетова (ID: 467)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Сагиды Бердиной (ID: 468)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Салавата Юлаева (ID: 469)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Салимьяна Гайнуллина (ID: 470)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Саляха Кулибая (ID: 471)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Северная (ID: 472)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Сергея Аксакова (ID: 473)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Сергея Есенина (ID: 474)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Центральная (ID: 475)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Шакира Биккулова (ID: 476)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Школьная (ID: 477)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

### District: Северный (ID: 23)

#### Street: Ак Кайын (ID: 339)

Кол-во домов: 6

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7064 | 2 | 2 | PLAIN | - |
| 7065 | 3 | 3 | PLAIN | - |
| 7066 | 4 | 4 | PLAIN | - |
| 7067 | 5 | 5 | PLAIN | - |
| 7068 | 6 | 6 | PLAIN | - |
| 7069 | 8 | 8 | PLAIN | - |

#### Street: Ак-Күлгин (ID: 425)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Ахмет Заки Валиди (ID: 340)

Кол-во домов: 32

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7070 | 1 | 1 | PLAIN | - |
| 7081 | 2 | 2 | PLAIN | - |
| 7091 | 3 | 3 | PLAIN | - |
| 7097 | 4 | 4 | PLAIN | - |
| 7098 | 5 | 5 | PLAIN | - |
| 7099 | 6 | 6 | PLAIN | - |
| 7100 | 7 | 7 | PLAIN | - |
| 7101 | 9 | 9 | PLAIN | - |
| 7071 | 10 | 10 | PLAIN | - |
| 7072 | 11 | 11 | PLAIN | - |
| 7073 | 12 | 12 | PLAIN | - |
| 7074 | 13 | 13 | PLAIN | - |
| 7075 | 14 | 14 | PLAIN | - |
| 7076 | 15 | 15 | PLAIN | - |
| 7077 | 16 | 16 | PLAIN | - |
| 7078 | 17 | 17 | PLAIN | - |
| 7079 | 19 | 19 | PLAIN | - |
| 7080 | 19/3 | 19 | FRACTION | 3 |
| 7082 | 21 | 21 | PLAIN | - |
| 7083 | 22 | 22 | PLAIN | - |
| 7084 | 23 | 23 | PLAIN | - |
| 7085 | 24 | 24 | PLAIN | - |
| 7086 | 25 | 25 | PLAIN | - |
| 7087 | 26 | 26 | PLAIN | - |
| 7088 | 27 | 27 | PLAIN | - |
| 7089 | 28 | 28 | PLAIN | - |
| 7090 | 29 | 29 | PLAIN | - |
| 7092 | 30 | 30 | PLAIN | - |
| 7093 | 31 | 31 | PLAIN | - |
| 7094 | 32 | 32 | PLAIN | - |
| 7095 | 33 | 33 | PLAIN | - |
| 7096 | 35 | 35 | PLAIN | - |

#### Street: Комарова (ID: 428)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Ленина (ID: 423)

Кол-во домов: 1

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 10093 | 12 | 12 | PLAIN | - |

#### Street: Любимая (ID: 427)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Урал Батыра (ID: 404)

Кол-во домов: 54

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9448 | 1 | 1 | PLAIN | - |
| 9459 | 2 | 2 | PLAIN | - |
| 9460 | 2/1 | 2 | FRACTION | 1 |
| 9477 | 3 | 3 | PLAIN | - |
| 9489 | 4 | 4 | PLAIN | - |
| 9496 | 5 | 5 | PLAIN | - |
| 9498 | 6 | 6 | PLAIN | - |
| 9499 | 7 | 7 | PLAIN | - |
| 9500 | 8 | 8 | PLAIN | - |
| 9501 | 9 | 9 | PLAIN | - |
| 9449 | 10 | 10 | PLAIN | - |
| 9450 | 11 | 11 | PLAIN | - |
| 9451 | 12 | 12 | PLAIN | - |
| 9452 | 13 | 13 | PLAIN | - |
| 9453 | 14 | 14 | PLAIN | - |
| 9454 | 15 | 15 | PLAIN | - |
| 9455 | 16 | 16 | PLAIN | - |
| 9456 | 17 | 17 | PLAIN | - |
| 9457 | 18 | 18 | PLAIN | - |
| 9458 | 19 | 19 | PLAIN | - |
| 9461 | 20/1 | 20 | FRACTION | 1 |
| 9462 | 21 | 21 | PLAIN | - |
| 9465 | 21к4 | 21 | CORPUS | 4 |
| 9466 | 21к5 | 21 | CORPUS | 5 |
| 9463 | 21/1 | 21 | FRACTION | 1 |
| 9464 | 21/2 | 21 | FRACTION | 2 |
| 9467 | 22 | 22 | PLAIN | - |
| 9468 | 23 | 23 | PLAIN | - |
| 9469 | 23к1 | 23 | CORPUS | 1 |
| 9470 | 24 | 24 | PLAIN | - |
| 9471 | 25 | 25 | PLAIN | - |
| 9472 | 26 | 26 | PLAIN | - |
| 9473 | 27 | 27 | PLAIN | - |
| 9474 | 28 | 28 | PLAIN | - |
| 9475 | 28к1 | 28 | CORPUS | 1 |
| 9476 | 29 | 29 | PLAIN | - |
| 9478 | 30 | 30 | PLAIN | - |
| 9479 | 30к1 | 30 | CORPUS | 1 |
| 9480 | 31 | 31 | PLAIN | - |
| 9481 | 32 | 32 | PLAIN | - |
| 9482 | 33 | 33 | PLAIN | - |
| 9483 | 34 | 34 | PLAIN | - |
| 9484 | 35 | 35 | PLAIN | - |
| 9485 | 36 | 36 | PLAIN | - |
| 9486 | 38 | 38 | PLAIN | - |
| 9487 | 39 | 39 | PLAIN | - |
| 9488 | 39А | 39 | LETTER | а |
| 9490 | 40 | 40 | PLAIN | - |
| 9491 | 41 | 41 | PLAIN | - |
| 9492 | 42 | 42 | PLAIN | - |
| 9493 | 44 | 44 | PLAIN | - |
| 9494 | 46 | 46 | PLAIN | - |
| 9495 | 48 | 48 | PLAIN | - |
| 9497 | 50 | 50 | PLAIN | - |

#### Street: Уральская (ID: 405)

Кол-во домов: 5

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9502 | 16 | 16 | PLAIN | - |
| 9503 | 20 | 20 | PLAIN | - |
| 9504 | 30 | 30 | PLAIN | - |
| 9505 | 32 | 32 | PLAIN | - |
| 9506 | 39 | 39 | PLAIN | - |

#### Street: Файзрахмана Мустафина (ID: 424)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Файзрахмана Хисматуллина (ID: 408)

Кол-во домов: 61

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9585 | 1 | 1 | PLAIN | - |
| 9596 | 2 | 2 | PLAIN | - |
| 9607 | 3 | 3 | PLAIN | - |
| 9618 | 4 | 4 | PLAIN | - |
| 9629 | 5 | 5 | PLAIN | - |
| 9643 | 7 | 7 | PLAIN | - |
| 9644 | 8 | 8 | PLAIN | - |
| 9645 | 9 | 9 | PLAIN | - |
| 9586 | 10 | 10 | PLAIN | - |
| 9587 | 11 | 11 | PLAIN | - |
| 9588 | 12 | 12 | PLAIN | - |
| 9589 | 13 | 13 | PLAIN | - |
| 9590 | 14 | 14 | PLAIN | - |
| 9591 | 15 | 15 | PLAIN | - |
| 9592 | 16 | 16 | PLAIN | - |
| 9593 | 17 | 17 | PLAIN | - |
| 9594 | 18 | 18 | PLAIN | - |
| 9595 | 19 | 19 | PLAIN | - |
| 9597 | 20 | 20 | PLAIN | - |
| 9598 | 21 | 21 | PLAIN | - |
| 9599 | 22 | 22 | PLAIN | - |
| 9600 | 23 | 23 | PLAIN | - |
| 9601 | 24 | 24 | PLAIN | - |
| 9602 | 25 | 25 | PLAIN | - |
| 9603 | 26 | 26 | PLAIN | - |
| 9604 | 27 | 27 | PLAIN | - |
| 9605 | 28 | 28 | PLAIN | - |
| 9606 | 29 | 29 | PLAIN | - |
| 9608 | 30 | 30 | PLAIN | - |
| 9609 | 31 | 31 | PLAIN | - |
| 9610 | 32 | 32 | PLAIN | - |
| 9611 | 33 | 33 | PLAIN | - |
| 9612 | 34 | 34 | PLAIN | - |
| 9613 | 35 | 35 | PLAIN | - |
| 9614 | 36 | 36 | PLAIN | - |
| 9615 | 37 | 37 | PLAIN | - |
| 9616 | 38 | 38 | PLAIN | - |
| 9617 | 39 | 39 | PLAIN | - |
| 9619 | 40 | 40 | PLAIN | - |
| 9620 | 41 | 41 | PLAIN | - |
| 9621 | 42 | 42 | PLAIN | - |
| 9622 | 43 | 43 | PLAIN | - |
| 9623 | 44 | 44 | PLAIN | - |
| 9624 | 45 | 45 | PLAIN | - |
| 9625 | 46 | 46 | PLAIN | - |
| 9626 | 47 | 47 | PLAIN | - |
| 9627 | 48 | 48 | PLAIN | - |
| 9628 | 49 | 49 | PLAIN | - |
| 9630 | 50 | 50 | PLAIN | - |
| 9631 | 51 | 51 | PLAIN | - |
| 9632 | 52 | 52 | PLAIN | - |
| 9633 | 53 | 53 | PLAIN | - |
| 9634 | 54 | 54 | PLAIN | - |
| 9635 | 55 | 55 | PLAIN | - |
| 9636 | 56 | 56 | PLAIN | - |
| 9637 | 57 | 57 | PLAIN | - |
| 9638 | 58 | 58 | PLAIN | - |
| 9639 | 59 | 59 | PLAIN | - |
| 9640 | 60 | 60 | PLAIN | - |
| 9641 | 62 | 62 | PLAIN | - |
| 9642 | 62к2 | 62 | CORPUS | 2 |

#### Street: Шагали Шакман (ID: 414)

Кол-во домов: 12

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9861 | 1 | 1 | PLAIN | - |
| 9867 | 2 | 2 | PLAIN | - |
| 9868 | 3 | 3 | PLAIN | - |
| 9869 | 4 | 4 | PLAIN | - |
| 9870 | 5 | 5 | PLAIN | - |
| 9871 | 6 | 6 | PLAIN | - |
| 9872 | 8 | 8 | PLAIN | - |
| 9862 | 10 | 10 | PLAIN | - |
| 9863 | 12 | 12 | PLAIN | - |
| 9864 | 14 | 14 | PLAIN | - |
| 9865 | 16 | 16 | PLAIN | - |
| 9866 | 18 | 18 | PLAIN | - |

#### Street: Шагали Шакмана (ID: 415)

Кол-во домов: 3

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9873 | 1/1 | 1 | FRACTION | 1 |
| 9875 | 9 | 9 | PLAIN | - |
| 9874 | 16/1 | 16 | FRACTION | 1 |

#### Street: Шайхзады Бабича (ID: 417)

Кол-во домов: 46

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9946 | 1 | 1 | PLAIN | - |
| 9957 | 2 | 2 | PLAIN | - |
| 9969 | 3 | 3 | PLAIN | - |
| 9977 | 4 | 4 | PLAIN | - |
| 9984 | 5 | 5 | PLAIN | - |
| 9988 | 6 | 6 | PLAIN | - |
| 9989 | 7 | 7 | PLAIN | - |
| 9990 | 8 | 8 | PLAIN | - |
| 9991 | 9 | 9 | PLAIN | - |
| 9947 | 10 | 10 | PLAIN | - |
| 9948 | 11 | 11 | PLAIN | - |
| 9949 | 12 | 12 | PLAIN | - |
| 9950 | 13 | 13 | PLAIN | - |
| 9951 | 14 | 14 | PLAIN | - |
| 9952 | 15 | 15 | PLAIN | - |
| 9953 | 16 | 16 | PLAIN | - |
| 9954 | 17 | 17 | PLAIN | - |
| 9955 | 18 | 18 | PLAIN | - |
| 9956 | 19 | 19 | PLAIN | - |
| 9958 | 20 | 20 | PLAIN | - |
| 9959 | 21 | 21 | PLAIN | - |
| 9960 | 22 | 22 | PLAIN | - |
| 9961 | 23 | 23 | PLAIN | - |
| 9962 | 24 | 24 | PLAIN | - |
| 9963 | 25 | 25 | PLAIN | - |
| 9964 | 26 | 26 | PLAIN | - |
| 9965 | 27 | 27 | PLAIN | - |
| 9966 | 28 | 28 | PLAIN | - |
| 9967 | 28/1 | 28 | FRACTION | 1 |
| 9968 | 29 | 29 | PLAIN | - |
| 9970 | 30 | 30 | PLAIN | - |
| 9971 | 31 | 31 | PLAIN | - |
| 9972 | 32 | 32 | PLAIN | - |
| 9973 | 33 | 33 | PLAIN | - |
| 9974 | 35 | 35 | PLAIN | - |
| 9975 | 37 | 37 | PLAIN | - |
| 9976 | 39 | 39 | PLAIN | - |
| 9978 | 41 | 41 | PLAIN | - |
| 9979 | 43 | 43 | PLAIN | - |
| 9980 | 43/1 | 43 | FRACTION | 1 |
| 9981 | 45 | 45 | PLAIN | - |
| 9982 | 47 | 47 | PLAIN | - |
| 9983 | 49 | 49 | PLAIN | - |
| 9985 | 51 | 51 | PLAIN | - |
| 9986 | 53 | 53 | PLAIN | - |
| 9987 | 55 | 55 | PLAIN | - |

#### Street: Шакимана (ID: 426)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

### District: Центр (ID: 19)

#### Street: 40 лет Октября (ID: 332)

Кол-во домов: 5

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6732 | 2 | 2 | PLAIN | - |
| 6733 | 4 | 4 | PLAIN | - |
| 6729 | 10 | 10 | PLAIN | - |
| 6730 | 11 | 11 | PLAIN | - |
| 6731 | 15 | 15 | PLAIN | - |

#### Street: Гагарина (ID: 345)

Кол-во домов: 11

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7212 | 1 | 1 | PLAIN | - |
| 7214 | 1а | 1 | LETTER | а |
| 7215 | 2а | 2 | LETTER | а |
| 7216 | 3 | 3 | PLAIN | - |
| 7217 | 4 | 4 | PLAIN | - |
| 7218 | 5 | 5 | PLAIN | - |
| 7219 | 6 | 6 | PLAIN | - |
| 7220 | 7 | 7 | PLAIN | - |
| 7221 | 8 | 8 | PLAIN | - |
| 7222 | 9 | 9 | PLAIN | - |
| 7213 | 11 | 11 | PLAIN | - |

#### Street: Горная (ID: 347)

Кол-во домов: 67

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7264 | 1 | 1 | PLAIN | - |
| 7276 | 1а | 1 | LETTER | а |
| 7277 | 1б | 1 | LETTER | б |
| 7278 | 2 | 2 | PLAIN | - |
| 7292 | 2а | 2 | LETTER | а |
| 7293 | 2б | 2 | LETTER | б |
| 7291 | 2В | 2 | LETTER | в |
| 7279 | 2/1 | 2 | FRACTION | 1 |
| 7294 | 3 | 3 | PLAIN | - |
| 7305 | 3А | 3 | LETTER | а |
| 7306 | 4 | 4 | PLAIN | - |
| 7318 | 5 | 5 | PLAIN | - |
| 7326 | 6 | 6 | PLAIN | - |
| 7327 | 7 | 7 | PLAIN | - |
| 7328 | 8 | 8 | PLAIN | - |
| 7329 | 8а | 8 | LETTER | а |
| 7330 | 9 | 9 | PLAIN | - |
| 7265 | 10 | 10 | PLAIN | - |
| 7266 | 11 | 11 | PLAIN | - |
| 7267 | 12 | 12 | PLAIN | - |
| 7268 | 13 | 13 | PLAIN | - |
| 7269 | 13А | 13 | LETTER | а |
| 7270 | 14 | 14 | PLAIN | - |
| 7271 | 15 | 15 | PLAIN | - |
| 7272 | 16 | 16 | PLAIN | - |
| 7273 | 17 | 17 | PLAIN | - |
| 7274 | 18 | 18 | PLAIN | - |
| 7275 | 19 | 19 | PLAIN | - |
| 7280 | 20 | 20 | PLAIN | - |
| 7281 | 21 | 21 | PLAIN | - |
| 7282 | 21А | 21 | LETTER | а |
| 7283 | 21Б | 21 | LETTER | б |
| 7284 | 23 | 23 | PLAIN | - |
| 7285 | 24 | 24 | PLAIN | - |
| 7286 | 25 | 25 | PLAIN | - |
| 7287 | 26 | 26 | PLAIN | - |
| 7288 | 27 | 27 | PLAIN | - |
| 7289 | 28 | 28 | PLAIN | - |
| 7290 | 29 | 29 | PLAIN | - |
| 7295 | 30 | 30 | PLAIN | - |
| 7296 | 31 | 31 | PLAIN | - |
| 7297 | 32 | 32 | PLAIN | - |
| 7298 | 33 | 33 | PLAIN | - |
| 7299 | 34 | 34 | PLAIN | - |
| 7300 | 35 | 35 | PLAIN | - |
| 7301 | 36 | 36 | PLAIN | - |
| 7302 | 37 | 37 | PLAIN | - |
| 7303 | 38 | 38 | PLAIN | - |
| 7304 | 39 | 39 | PLAIN | - |
| 7307 | 40 | 40 | PLAIN | - |
| 7308 | 41 | 41 | PLAIN | - |
| 7309 | 42 | 42 | PLAIN | - |
| 7310 | 43 | 43 | PLAIN | - |
| 7311 | 43а | 43 | LETTER | а |
| 7312 | 44 | 44 | PLAIN | - |
| 7313 | 45 | 45 | PLAIN | - |
| 7314 | 46 | 46 | PLAIN | - |
| 7315 | 47а | 47 | LETTER | а |
| 7316 | 48 | 48 | PLAIN | - |
| 7317 | 49 | 49 | PLAIN | - |
| 7319 | 50 | 50 | PLAIN | - |
| 7320 | 50а | 50 | LETTER | а |
| 7321 | 50б | 50 | LETTER | б |
| 7322 | 51 | 51 | PLAIN | - |
| 7323 | 53 | 53 | PLAIN | - |
| 7324 | 55 | 55 | PLAIN | - |
| 7325 | 57 | 57 | PLAIN | - |

#### Street: Кирова (ID: 358)

Кол-во домов: 21

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7694 | 1 | 1 | PLAIN | - |
| 7701 | 2 | 2 | PLAIN | - |
| 7707 | 3 | 3 | PLAIN | - |
| 7708 | 4 | 4 | PLAIN | - |
| 7709 | 5 | 5 | PLAIN | - |
| 7710 | 5а | 5 | LETTER | а |
| 7711 | 6 | 6 | PLAIN | - |
| 7712 | 7 | 7 | PLAIN | - |
| 7713 | 8 | 8 | PLAIN | - |
| 7714 | 9 | 9 | PLAIN | - |
| 7695 | 10 | 10 | PLAIN | - |
| 7696 | 11 | 11 | PLAIN | - |
| 7697 | 12 | 12 | PLAIN | - |
| 7698 | 14 | 14 | PLAIN | - |
| 7699 | 16 | 16 | PLAIN | - |
| 7700 | 18 | 18 | PLAIN | - |
| 7702 | 20 | 20 | PLAIN | - |
| 7703 | 22 | 22 | PLAIN | - |
| 7704 | 24 | 24 | PLAIN | - |
| 7705 | 26 | 26 | PLAIN | - |
| 7706 | 28 | 28 | PLAIN | - |

#### Street: Колхозная (ID: 359)

Кол-во домов: 51

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7715 | 1 | 1 | PLAIN | - |
| 7725 | 2 | 2 | PLAIN | - |
| 7735 | 2а | 2 | LETTER | а |
| 7736 | 2б | 2 | LETTER | б |
| 7737 | 3 | 3 | PLAIN | - |
| 7747 | 4 | 4 | PLAIN | - |
| 7755 | 5 | 5 | PLAIN | - |
| 7761 | 6 | 6 | PLAIN | - |
| 7763 | 7 | 7 | PLAIN | - |
| 7764 | 8 | 8 | PLAIN | - |
| 7765 | 9 | 9 | PLAIN | - |
| 7716 | 10 | 10 | PLAIN | - |
| 7717 | 11 | 11 | PLAIN | - |
| 7718 | 12 | 12 | PLAIN | - |
| 7719 | 13 | 13 | PLAIN | - |
| 7720 | 14 | 14 | PLAIN | - |
| 7721 | 16 | 16 | PLAIN | - |
| 7722 | 17 | 17 | PLAIN | - |
| 7723 | 18 | 18 | PLAIN | - |
| 7724 | 19 | 19 | PLAIN | - |
| 7726 | 20 | 20 | PLAIN | - |
| 7727 | 21 | 21 | PLAIN | - |
| 7728 | 22 | 22 | PLAIN | - |
| 7729 | 23 | 23 | PLAIN | - |
| 7730 | 25 | 25 | PLAIN | - |
| 7731 | 26 | 26 | PLAIN | - |
| 7732 | 27 | 27 | PLAIN | - |
| 7733 | 28 | 28 | PLAIN | - |
| 7734 | 29 | 29 | PLAIN | - |
| 7738 | 30 | 30 | PLAIN | - |
| 7739 | 31 | 31 | PLAIN | - |
| 7740 | 32 | 32 | PLAIN | - |
| 7741 | 33 | 33 | PLAIN | - |
| 7742 | 34 | 34 | PLAIN | - |
| 7743 | 35 | 35 | PLAIN | - |
| 7744 | 36 | 36 | PLAIN | - |
| 7745 | 37 | 37 | PLAIN | - |
| 7746 | 38 | 38 | PLAIN | - |
| 7748 | 40 | 40 | PLAIN | - |
| 7749 | 41 | 41 | PLAIN | - |
| 7750 | 42 | 42 | PLAIN | - |
| 7751 | 43 | 43 | PLAIN | - |
| 7752 | 44 | 44 | PLAIN | - |
| 7753 | 46 | 46 | PLAIN | - |
| 7754 | 48 | 48 | PLAIN | - |
| 7756 | 50 | 50 | PLAIN | - |
| 7757 | 52 | 52 | PLAIN | - |
| 7758 | 54 | 54 | PLAIN | - |
| 7759 | 56 | 56 | PLAIN | - |
| 7760 | 58 | 58 | PLAIN | - |
| 7762 | 60 | 60 | PLAIN | - |

#### Street: Комарова (ID: 360)

Кол-во домов: 29

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7766 | 1 | 1 | PLAIN | - |
| 7777 | 1к1 | 1 | CORPUS | 1 |
| 7778 | 2 | 2 | PLAIN | - |
| 7783 | 2к1 | 2 | CORPUS | 1 |
| 7784 | 3 | 3 | PLAIN | - |
| 7785 | 4 | 4 | PLAIN | - |
| 7786 | 5 | 5 | PLAIN | - |
| 7787 | 5к1 | 5 | CORPUS | 1 |
| 7788 | 6 | 6 | PLAIN | - |
| 7789 | 6а | 6 | LETTER | а |
| 7790 | 6к1 | 6 | CORPUS | 1 |
| 7791 | 7 | 7 | PLAIN | - |
| 7792 | 7А | 7 | LETTER | а |
| 7793 | 8 | 8 | PLAIN | - |
| 7794 | 9 | 9 | PLAIN | - |
| 7767 | 10 | 10 | PLAIN | - |
| 7768 | 11 | 11 | PLAIN | - |
| 7769 | 12 | 12 | PLAIN | - |
| 7770 | 13 | 13 | PLAIN | - |
| 7771 | 14 | 14 | PLAIN | - |
| 7772 | 15 | 15 | PLAIN | - |
| 7773 | 16 | 16 | PLAIN | - |
| 7774 | 17 | 17 | PLAIN | - |
| 7775 | 18 | 18 | PLAIN | - |
| 7776 | 19 | 19 | PLAIN | - |
| 7779 | 20 | 20 | PLAIN | - |
| 7780 | 21 | 21 | PLAIN | - |
| 7781 | 22 | 22 | PLAIN | - |
| 7782 | 23 | 23 | PLAIN | - |

#### Street: Коммунистическая (ID: 361)

Кол-во домов: 60

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7795 | 1 | 1 | PLAIN | - |
| 7802 | 1а | 1 | LETTER | а |
| 7801 | 1Б | 1 | LETTER | б |
| 7803 | 1к1 | 1 | CORPUS | 1 |
| 7804 | 1к2 | 1 | CORPUS | 2 |
| 7805 | 1к3 | 1 | CORPUS | 3 |
| 7806 | 1к4 | 1 | CORPUS | 4 |
| 7807 | 1к5 | 1 | CORPUS | 5 |
| 7808 | 1к6 | 1 | CORPUS | 6 |
| 7809 | 2 | 2 | PLAIN | - |
| 7828 | 2а | 2 | LETTER | а |
| 7829 | 2б | 2 | LETTER | б |
| 7830 | 2к1 | 2 | CORPUS | 1 |
| 7831 | 2к2 | 2 | CORPUS | 2 |
| 7832 | 2к3 | 2 | CORPUS | 3 |
| 7833 | 2к5 | 2 | CORPUS | 5 |
| 7810 | 2/4 | 2 | FRACTION | 4 |
| 7834 | 3 | 3 | PLAIN | - |
| 7850 | 5 | 5 | PLAIN | - |
| 7851 | 7 | 7 | PLAIN | - |
| 7852 | 8 | 8 | PLAIN | - |
| 7853 | 8а | 8 | LETTER | а |
| 7854 | 9 | 9 | PLAIN | - |
| 7796 | 10 | 10 | PLAIN | - |
| 7797 | 11 | 11 | PLAIN | - |
| 7798 | 11/1 | 11 | FRACTION | 1 |
| 7799 | 16 | 16 | PLAIN | - |
| 7800 | 19 | 19 | PLAIN | - |
| 7811 | 21 | 21 | PLAIN | - |
| 7814 | 21б | 21 | LETTER | б |
| 7815 | 21в | 21 | LETTER | в |
| 7816 | 21к4 | 21 | CORPUS | 4 |
| 7812 | 21/2 | 21 | FRACTION | 2 |
| 7813 | 21/3 | 21 | FRACTION | 3 |
| 7817 | 22 | 22 | PLAIN | - |
| 7818 | 22/1 | 22 | FRACTION | 1 |
| 7819 | 23 | 23 | PLAIN | - |
| 7820 | 24 | 24 | PLAIN | - |
| 7821 | 25 | 25 | PLAIN | - |
| 7822 | 25А | 25 | LETTER | а |
| 7823 | 26 | 26 | PLAIN | - |
| 7824 | 27 | 27 | PLAIN | - |
| 7825 | 28/1 | 28 | FRACTION | 1 |
| 7826 | 28/3 | 28 | FRACTION | 3 |
| 7827 | 29 | 29 | PLAIN | - |
| 7835 | 30 | 30 | PLAIN | - |
| 7836 | 31 | 31 | PLAIN | - |
| 7837 | 32 | 32 | PLAIN | - |
| 7838 | 32/1 | 32 | FRACTION | 1 |
| 7839 | 33 | 33 | PLAIN | - |
| 7840 | 34 | 34 | PLAIN | - |
| 7841 | 35 | 35 | PLAIN | - |
| 7842 | 36 | 36 | PLAIN | - |
| 7843 | 37 | 37 | PLAIN | - |
| 7844 | 38 | 38 | PLAIN | - |
| 7845 | 38/1 | 38 | FRACTION | 1 |
| 7846 | 39 | 39 | PLAIN | - |
| 7847 | 41 | 41 | PLAIN | - |
| 7848 | 43 | 43 | PLAIN | - |
| 7849 | 45 | 45 | PLAIN | - |

#### Street: Комсомольская (ID: 362)

Кол-во домов: 27

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7855 | 1 | 1 | PLAIN | - |
| 7864 | 2 | 2 | PLAIN | - |
| 7871 | 3 | 3 | PLAIN | - |
| 7875 | 4 | 4 | PLAIN | - |
| 7876 | 4А | 4 | LETTER | а |
| 7877 | 5 | 5 | PLAIN | - |
| 7878 | 6 | 6 | PLAIN | - |
| 7879 | 7 | 7 | PLAIN | - |
| 7880 | 8 | 8 | PLAIN | - |
| 7881 | 9 | 9 | PLAIN | - |
| 7856 | 10 | 10 | PLAIN | - |
| 7857 | 12 | 12 | PLAIN | - |
| 7858 | 14 | 14 | PLAIN | - |
| 7859 | 15 | 15 | PLAIN | - |
| 7860 | 16 | 16 | PLAIN | - |
| 7861 | 17 | 17 | PLAIN | - |
| 7862 | 18 | 18 | PLAIN | - |
| 7863 | 19 | 19 | PLAIN | - |
| 7865 | 20 | 20 | PLAIN | - |
| 7866 | 21 | 21 | PLAIN | - |
| 7867 | 22 | 22 | PLAIN | - |
| 7868 | 24 | 24 | PLAIN | - |
| 7869 | 26 | 26 | PLAIN | - |
| 7870 | 28 | 28 | PLAIN | - |
| 7872 | 30 | 30 | PLAIN | - |
| 7873 | 32 | 32 | PLAIN | - |
| 7874 | 34 | 34 | PLAIN | - |

#### Street: Ленина (ID: 364)

Кол-во домов: 118

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7921 | 1 | 1 | PLAIN | - |
| 7961 | 2 | 2 | PLAIN | - |
| 7971 | 2а | 2 | LETTER | а |
| 7972 | 2б | 2 | LETTER | б |
| 7973 | 2в | 2 | LETTER | в |
| 7962 | 2/1 | 2 | FRACTION | 1 |
| 7974 | 3 | 3 | PLAIN | - |
| 7986 | 4 | 4 | PLAIN | - |
| 7995 | 4а | 4 | LETTER | а |
| 7996 | 5 | 5 | PLAIN | - |
| 8008 | 6 | 6 | PLAIN | - |
| 8018 | 7 | 7 | PLAIN | - |
| 8028 | 8 | 8 | PLAIN | - |
| 8034 | 9 | 9 | PLAIN | - |
| 7922 | 10 | 10 | PLAIN | - |
| 7928 | 11 | 11 | PLAIN | - |
| 7933 | 12 | 12 | PLAIN | - |
| 7939 | 13 | 13 | PLAIN | - |
| 7945 | 14 | 14 | PLAIN | - |
| 7951 | 14к1 | 14 | CORPUS | 1 |
| 7952 | 15 | 15 | PLAIN | - |
| 7957 | 16/1 | 16 | FRACTION | 1 |
| 7958 | 17 | 17 | PLAIN | - |
| 7959 | 18 | 18 | PLAIN | - |
| 7960 | 19 | 19 | PLAIN | - |
| 7963 | 22 | 22 | PLAIN | - |
| 7964 | 23 | 23 | PLAIN | - |
| 7965 | 24 | 24 | PLAIN | - |
| 7966 | 25 | 25 | PLAIN | - |
| 7967 | 26 | 26 | PLAIN | - |
| 7968 | 27 | 27 | PLAIN | - |
| 7969 | 28 | 28 | PLAIN | - |
| 7970 | 29/1 | 29 | FRACTION | 1 |
| 7975 | 30 | 30 | PLAIN | - |
| 7976 | 31 | 31 | PLAIN | - |
| 7977 | 32 | 32 | PLAIN | - |
| 7978 | 33 | 33 | PLAIN | - |
| 7979 | 34 | 34 | PLAIN | - |
| 7980 | 35 | 35 | PLAIN | - |
| 7981 | 36 | 36 | PLAIN | - |
| 7982 | 37 | 37 | PLAIN | - |
| 7983 | 38 | 38 | PLAIN | - |
| 7984 | 38/1 | 38 | FRACTION | 1 |
| 7985 | 39 | 39 | PLAIN | - |
| 7987 | 40 | 40 | PLAIN | - |
| 7988 | 41 | 41 | PLAIN | - |
| 7989 | 42 | 42 | PLAIN | - |
| 7990 | 43 | 43 | PLAIN | - |
| 7991 | 44 | 44 | PLAIN | - |
| 7992 | 46 | 46 | PLAIN | - |
| 7993 | 48 | 48 | PLAIN | - |
| 7994 | 49 | 49 | PLAIN | - |
| 7997 | 50 | 50 | PLAIN | - |
| 7998 | 51 | 51 | PLAIN | - |
| 7999 | 51А | 51 | LETTER | а |
| 8000 | 52 | 52 | PLAIN | - |
| 8001 | 52к1 | 52 | CORPUS | 1 |
| 8002 | 53 | 53 | PLAIN | - |
| 8003 | 54 | 54 | PLAIN | - |
| 8004 | 55 | 55 | PLAIN | - |
| 8005 | 56 | 56 | PLAIN | - |
| 8006 | 57 | 57 | PLAIN | - |
| 8007 | 58 | 58 | PLAIN | - |
| 8009 | 60 | 60 | PLAIN | - |
| 8010 | 61 | 61 | PLAIN | - |
| 8011 | 62 | 62 | PLAIN | - |
| 8012 | 63 | 63 | PLAIN | - |
| 8013 | 64 | 64 | PLAIN | - |
| 8014 | 65 | 65 | PLAIN | - |
| 8015 | 66 | 66 | PLAIN | - |
| 8016 | 68 | 68 | PLAIN | - |
| 8017 | 69 | 69 | PLAIN | - |
| 8019 | 71 | 71 | PLAIN | - |
| 8020 | 72 | 72 | PLAIN | - |
| 8021 | 73 | 73 | PLAIN | - |
| 8022 | 74 | 74 | PLAIN | - |
| 8023 | 75 | 75 | PLAIN | - |
| 8024 | 76 | 76 | PLAIN | - |
| 8025 | 77 | 77 | PLAIN | - |
| 8026 | 78 | 78 | PLAIN | - |
| 8027 | 79 | 79 | PLAIN | - |
| 8029 | 80 | 80 | PLAIN | - |
| 8030 | 81 | 81 | PLAIN | - |
| 8031 | 85 | 85 | PLAIN | - |
| 8032 | 87 | 87 | PLAIN | - |
| 8033 | 89 | 89 | PLAIN | - |
| 8035 | 91 | 91 | PLAIN | - |
| 8036 | 95 | 95 | PLAIN | - |
| 8037 | 97 | 97 | PLAIN | - |
| 8038 | 99 | 99 | PLAIN | - |
| 7923 | 100 | 100 | PLAIN | - |
| 7924 | 101 | 101 | PLAIN | - |
| 7925 | 105 | 105 | PLAIN | - |
| 7926 | 107 | 107 | PLAIN | - |
| 7927 | 109 | 109 | PLAIN | - |
| 7929 | 111 | 111 | PLAIN | - |
| 7930 | 113 | 113 | PLAIN | - |
| 7931 | 115 | 115 | PLAIN | - |
| 7932 | 119 | 119 | PLAIN | - |
| 7934 | 121 | 121 | PLAIN | - |
| 7935 | 123 | 123 | PLAIN | - |
| 7936 | 125 | 125 | PLAIN | - |
| 7937 | 127 | 127 | PLAIN | - |
| 7938 | 127/1 | 127 | FRACTION | 1 |
| 7940 | 131 | 131 | PLAIN | - |
| 7941 | 133 | 133 | PLAIN | - |
| 7942 | 135 | 135 | PLAIN | - |
| 7943 | 137 | 137 | PLAIN | - |
| 7944 | 139 | 139 | PLAIN | - |
| 7946 | 141к1 | 141 | CORPUS | 1 |
| 7947 | 143 | 143 | PLAIN | - |
| 7948 | 145 | 145 | PLAIN | - |
| 7949 | 147 | 147 | PLAIN | - |
| 7950 | 149 | 149 | PLAIN | - |
| 7953 | 151 | 151 | PLAIN | - |
| 7954 | 155/1 | 155 | FRACTION | 1 |
| 7955 | 155/2 | 155 | FRACTION | 2 |
| 7956 | 157 | 157 | PLAIN | - |

#### Street: Матросова (ID: 370)

Кол-во домов: 22

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8162 | 1 | 1 | PLAIN | - |
| 8171 | 2 | 2 | PLAIN | - |
| 8173 | 3 | 3 | PLAIN | - |
| 8174 | 3а | 3 | LETTER | а |
| 8175 | 4 | 4 | PLAIN | - |
| 8176 | 5 | 5 | PLAIN | - |
| 8177 | 5а | 5 | LETTER | а |
| 8178 | 6 | 6 | PLAIN | - |
| 8179 | 7 | 7 | PLAIN | - |
| 8180 | 7/1 | 7 | FRACTION | 1 |
| 8181 | 8 | 8 | PLAIN | - |
| 8183 | 9а | 9 | LETTER | а |
| 8182 | 9Б | 9 | LETTER | б |
| 8163 | 10/1 | 10 | FRACTION | 1 |
| 8164 | 10/2 | 10 | FRACTION | 2 |
| 8165 | 11 | 11 | PLAIN | - |
| 8166 | 12 | 12 | PLAIN | - |
| 8167 | 14 | 14 | PLAIN | - |
| 8168 | 14/1 | 14 | FRACTION | 1 |
| 8169 | 16 | 16 | PLAIN | - |
| 8170 | 18 | 18 | PLAIN | - |
| 8172 | 20 | 20 | PLAIN | - |

#### Street: Мира (ID: 375)

Кол-во домов: 43

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8327 | 1 | 1 | PLAIN | - |
| 8341 | 1а | 1 | LETTER | а |
| 8351 | 2а | 2 | LETTER | а |
| 8352 | 3 | 3 | PLAIN | - |
| 8353 | 3/1 | 3 | FRACTION | 1 |
| 8360 | 4/1 | 4 | FRACTION | 1 |
| 8364 | 5 | 5 | PLAIN | - |
| 8365 | 6/1 | 6 | FRACTION | 1 |
| 8366 | 6/2 | 6 | FRACTION | 2 |
| 8367 | 7 | 7 | PLAIN | - |
| 8368 | 8 | 8 | PLAIN | - |
| 8369 | 9 | 9 | PLAIN | - |
| 8328 | 10/1 | 10 | FRACTION | 1 |
| 8329 | 10/2 | 10 | FRACTION | 2 |
| 8330 | 11 | 11 | PLAIN | - |
| 8331 | 11а | 11 | LETTER | а |
| 8332 | 12/2 | 12 | FRACTION | 2 |
| 8333 | 13 | 13 | PLAIN | - |
| 8334 | 14 | 14 | PLAIN | - |
| 8335 | 15 | 15 | PLAIN | - |
| 8336 | 15/1 | 15 | FRACTION | 1 |
| 8337 | 16 | 16 | PLAIN | - |
| 8338 | 17 | 17 | PLAIN | - |
| 8339 | 18 | 18 | PLAIN | - |
| 8340 | 19 | 19 | PLAIN | - |
| 8342 | 20 | 20 | PLAIN | - |
| 8343 | 22 | 22 | PLAIN | - |
| 8344 | 23 | 23 | PLAIN | - |
| 8345 | 25 | 25 | PLAIN | - |
| 8346 | 27 | 27 | PLAIN | - |
| 8347 | 27/1 | 27 | FRACTION | 1 |
| 8348 | 27/2 | 27 | FRACTION | 2 |
| 8349 | 29 | 29 | PLAIN | - |
| 8350 | 29/1 | 29 | FRACTION | 1 |
| 8354 | 31 | 31 | PLAIN | - |
| 8355 | 31/1 | 31 | FRACTION | 1 |
| 8356 | 33 | 33 | PLAIN | - |
| 8357 | 35 | 35 | PLAIN | - |
| 8358 | 37 | 37 | PLAIN | - |
| 8359 | 39 | 39 | PLAIN | - |
| 8361 | 41 | 41 | PLAIN | - |
| 8362 | 43 | 43 | PLAIN | - |
| 8363 | 45 | 45 | PLAIN | - |

#### Street: Молодежная (ID: 376)

Кол-во домов: 66

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8370 | 1 | 1 | PLAIN | - |
| 8386 | 2 | 2 | PLAIN | - |
| 8402 | 3 | 3 | PLAIN | - |
| 8416 | 4 | 4 | PLAIN | - |
| 8424 | 5 | 5 | PLAIN | - |
| 8431 | 6 | 6 | PLAIN | - |
| 8432 | 7 | 7 | PLAIN | - |
| 8433 | 7а | 7 | LETTER | а |
| 8434 | 8 | 8 | PLAIN | - |
| 8435 | 9 | 9 | PLAIN | - |
| 8371 | 10 | 10 | PLAIN | - |
| 8373 | 10а | 10 | LETTER | а |
| 8374 | 10б | 10 | LETTER | б |
| 8372 | 10/1 | 10 | FRACTION | 1 |
| 8375 | 11 | 11 | PLAIN | - |
| 8376 | 12 | 12 | PLAIN | - |
| 8377 | 12а | 12 | LETTER | а |
| 8378 | 13 | 13 | PLAIN | - |
| 8379 | 13/3 | 13 | FRACTION | 3 |
| 8380 | 14 | 14 | PLAIN | - |
| 8381 | 15 | 15 | PLAIN | - |
| 8382 | 16 | 16 | PLAIN | - |
| 8383 | 17 | 17 | PLAIN | - |
| 8384 | 18 | 18 | PLAIN | - |
| 8385 | 19 | 19 | PLAIN | - |
| 8387 | 20 | 20 | PLAIN | - |
| 8388 | 20б | 20 | LETTER | б |
| 8389 | 21 | 21 | PLAIN | - |
| 8390 | 22 | 22 | PLAIN | - |
| 8391 | 23 | 23 | PLAIN | - |
| 8392 | 24 | 24 | PLAIN | - |
| 8393 | 24а | 24 | LETTER | а |
| 8394 | 25 | 25 | PLAIN | - |
| 8395 | 25а | 25 | LETTER | а |
| 8396 | 25к1 | 25 | CORPUS | 1 |
| 8397 | 26 | 26 | PLAIN | - |
| 8398 | 27 | 27 | PLAIN | - |
| 8399 | 28 | 28 | PLAIN | - |
| 8400 | 28к3 | 28 | CORPUS | 3 |
| 8401 | 29 | 29 | PLAIN | - |
| 8403 | 30 | 30 | PLAIN | - |
| 8404 | 30/1 | 30 | FRACTION | 1 |
| 8405 | 31 | 31 | PLAIN | - |
| 8406 | 32 | 32 | PLAIN | - |
| 8407 | 33 | 33 | PLAIN | - |
| 8408 | 35 | 35 | PLAIN | - |
| 8409 | 36 | 36 | PLAIN | - |
| 8410 | 36/2 | 36 | FRACTION | 2 |
| 8411 | 36/3 | 36 | FRACTION | 3 |
| 8412 | 37 | 37 | PLAIN | - |
| 8413 | 38 | 38 | PLAIN | - |
| 8414 | 39 | 39 | PLAIN | - |
| 8415 | 39А | 39 | LETTER | а |
| 8417 | 41 | 41 | PLAIN | - |
| 8418 | 41а | 41 | LETTER | а |
| 8419 | 43 | 43 | PLAIN | - |
| 8420 | 44 | 44 | PLAIN | - |
| 8421 | 45 | 45 | PLAIN | - |
| 8422 | 47 | 47 | PLAIN | - |
| 8423 | 49 | 49 | PLAIN | - |
| 8425 | 51 | 51 | PLAIN | - |
| 8426 | 53 | 53 | PLAIN | - |
| 8427 | 55 | 55 | PLAIN | - |
| 8428 | 57 | 57 | PLAIN | - |
| 8429 | 57а | 57 | LETTER | а |
| 8430 | 59 | 59 | PLAIN | - |

#### Street: Мугалляма Мирхайдарова (ID: 377)

Кол-во домов: 13

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8436 | 1 | 1 | PLAIN | - |
| 8442 | 2 | 2 | PLAIN | - |
| 8443 | 4 | 4 | PLAIN | - |
| 8444 | 5 | 5 | PLAIN | - |
| 8445 | 6 | 6 | PLAIN | - |
| 8446 | 7 | 7 | PLAIN | - |
| 8447 | 8 | 8 | PLAIN | - |
| 8448 | 9 | 9 | PLAIN | - |
| 8437 | 10 | 10 | PLAIN | - |
| 8438 | 11 | 11 | PLAIN | - |
| 8439 | 12 | 12 | PLAIN | - |
| 8440 | 14 | 14 | PLAIN | - |
| 8441 | 16 | 16 | PLAIN | - |

#### Street: Партизанская (ID: 381)

Кол-во домов: 66

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8531 | 1 | 1 | PLAIN | - |
| 8552 | 3 | 3 | PLAIN | - |
| 8563 | 4 | 4 | PLAIN | - |
| 8574 | 5 | 5 | PLAIN | - |
| 8586 | 6 | 6 | PLAIN | - |
| 8593 | 6А | 6 | LETTER | а |
| 8594 | 7 | 7 | PLAIN | - |
| 8595 | 8 | 8 | PLAIN | - |
| 8596 | 9 | 9 | PLAIN | - |
| 8532 | 11 | 11 | PLAIN | - |
| 8533 | 12 | 12 | PLAIN | - |
| 8534 | 13 | 13 | PLAIN | - |
| 8535 | 14 | 14 | PLAIN | - |
| 8536 | 14а | 14 | LETTER | а |
| 8537 | 15 | 15 | PLAIN | - |
| 8538 | 16 | 16 | PLAIN | - |
| 8539 | 17 | 17 | PLAIN | - |
| 8540 | 18 | 18 | PLAIN | - |
| 8541 | 19 | 19 | PLAIN | - |
| 8542 | 20 | 20 | PLAIN | - |
| 8543 | 21 | 21 | PLAIN | - |
| 8544 | 23 | 23 | PLAIN | - |
| 8545 | 24 | 24 | PLAIN | - |
| 8546 | 24/2 | 24 | FRACTION | 2 |
| 8547 | 25 | 25 | PLAIN | - |
| 8548 | 26 | 26 | PLAIN | - |
| 8549 | 27 | 27 | PLAIN | - |
| 8550 | 28 | 28 | PLAIN | - |
| 8551 | 29 | 29 | PLAIN | - |
| 8553 | 30 | 30 | PLAIN | - |
| 8554 | 31 | 31 | PLAIN | - |
| 8555 | 32 | 32 | PLAIN | - |
| 8556 | 33 | 33 | PLAIN | - |
| 8557 | 34 | 34 | PLAIN | - |
| 8558 | 35 | 35 | PLAIN | - |
| 8559 | 36 | 36 | PLAIN | - |
| 8560 | 37 | 37 | PLAIN | - |
| 8561 | 38 | 38 | PLAIN | - |
| 8562 | 39 | 39 | PLAIN | - |
| 8564 | 40 | 40 | PLAIN | - |
| 8565 | 41 | 41 | PLAIN | - |
| 8566 | 42 | 42 | PLAIN | - |
| 8567 | 43 | 43 | PLAIN | - |
| 8568 | 44 | 44 | PLAIN | - |
| 8569 | 45 | 45 | PLAIN | - |
| 8570 | 46 | 46 | PLAIN | - |
| 8571 | 47 | 47 | PLAIN | - |
| 8572 | 48 | 48 | PLAIN | - |
| 8573 | 49 | 49 | PLAIN | - |
| 8575 | 50 | 50 | PLAIN | - |
| 8576 | 51 | 51 | PLAIN | - |
| 8577 | 52 | 52 | PLAIN | - |
| 8578 | 53 | 53 | PLAIN | - |
| 8579 | 54 | 54 | PLAIN | - |
| 8580 | 55 | 55 | PLAIN | - |
| 8581 | 56 | 56 | PLAIN | - |
| 8582 | 57 | 57 | PLAIN | - |
| 8583 | 57а | 57 | LETTER | а |
| 8584 | 58 | 58 | PLAIN | - |
| 8585 | 59Б | 59 | LETTER | б |
| 8587 | 60 | 60 | PLAIN | - |
| 8588 | 61 | 61 | PLAIN | - |
| 8589 | 62 | 62 | PLAIN | - |
| 8590 | 63 | 63 | PLAIN | - |
| 8591 | 64 | 64 | PLAIN | - |
| 8592 | 65 | 65 | PLAIN | - |

#### Street: Первомайская (ID: 382)

Кол-во домов: 9

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8597 | 1 | 1 | PLAIN | - |
| 8599 | 2 | 2 | PLAIN | - |
| 8600 | 3 | 3 | PLAIN | - |
| 8601 | 4 | 4 | PLAIN | - |
| 8602 | 5 | 5 | PLAIN | - |
| 8603 | 6 | 6 | PLAIN | - |
| 8604 | 7 | 7 | PLAIN | - |
| 8605 | 8 | 8 | PLAIN | - |
| 8598 | 10 | 10 | PLAIN | - |

#### Street: Салавата Юлаева (ID: 393)

Кол-во домов: 47

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9044 | 1 | 1 | PLAIN | - |
| 9053 | 2 | 2 | PLAIN | - |
| 9064 | 2а | 2 | LETTER | а |
| 9065 | 3 | 3 | PLAIN | - |
| 9076 | 4 | 4 | PLAIN | - |
| 9083 | 5 | 5 | PLAIN | - |
| 9084 | 6 | 6 | PLAIN | - |
| 9087 | 7 | 7 | PLAIN | - |
| 9088 | 8 | 8 | PLAIN | - |
| 9089 | 8/1 | 8 | FRACTION | 1 |
| 9090 | 9 | 9 | PLAIN | - |
| 9045 | 11 | 11 | PLAIN | - |
| 9046 | 12 | 12 | PLAIN | - |
| 9047 | 12а | 12 | LETTER | а |
| 9048 | 13 | 13 | PLAIN | - |
| 9049 | 14 | 14 | PLAIN | - |
| 9050 | 16 | 16 | PLAIN | - |
| 9051 | 18 | 18 | PLAIN | - |
| 9052 | 19 | 19 | PLAIN | - |
| 9054 | 20 | 20 | PLAIN | - |
| 9055 | 21 | 21 | PLAIN | - |
| 9056 | 22 | 22 | PLAIN | - |
| 9057 | 23 | 23 | PLAIN | - |
| 9058 | 24 | 24 | PLAIN | - |
| 9059 | 25 | 25 | PLAIN | - |
| 9060 | 26 | 26 | PLAIN | - |
| 9061 | 27 | 27 | PLAIN | - |
| 9062 | 28 | 28 | PLAIN | - |
| 9063 | 29 | 29 | PLAIN | - |
| 9066 | 30 | 30 | PLAIN | - |
| 9067 | 31 | 31 | PLAIN | - |
| 9068 | 33 | 33 | PLAIN | - |
| 9069 | 33а | 33 | LETTER | а |
| 9070 | 34 | 34 | PLAIN | - |
| 9071 | 35 | 35 | PLAIN | - |
| 9072 | 36 | 36 | PLAIN | - |
| 9073 | 37 | 37 | PLAIN | - |
| 9074 | 38 | 38 | PLAIN | - |
| 9075 | 38А | 38 | LETTER | а |
| 9077 | 40 | 40 | PLAIN | - |
| 9078 | 42 | 42 | PLAIN | - |
| 9079 | 44 | 44 | PLAIN | - |
| 9080 | 46 | 46 | PLAIN | - |
| 9081 | 46/1 | 46 | FRACTION | 1 |
| 9082 | 48 | 48 | PLAIN | - |
| 9086 | 65а | 65 | LETTER | а |
| 9085 | 65/1 | 65 | FRACTION | 1 |

#### Street: Советская (ID: 396)

Кол-во домов: 26

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9176 | 1 | 1 | PLAIN | - |
| 9185 | 2 | 2 | PLAIN | - |
| 9193 | 3 | 3 | PLAIN | - |
| 9195 | 4А | 4 | LETTER | а |
| 9196 | 4Б | 4 | LETTER | б |
| 9197 | 5 | 5 | PLAIN | - |
| 9198 | 6 | 6 | PLAIN | - |
| 9199 | 7 | 7 | PLAIN | - |
| 9200 | 8 | 8 | PLAIN | - |
| 9201 | 9 | 9 | PLAIN | - |
| 9177 | 10 | 10 | PLAIN | - |
| 9178 | 11 | 11 | PLAIN | - |
| 9179 | 13 | 13 | PLAIN | - |
| 9180 | 14 | 14 | PLAIN | - |
| 9181 | 15 | 15 | PLAIN | - |
| 9182 | 16 | 16 | PLAIN | - |
| 9183 | 17 | 17 | PLAIN | - |
| 9184 | 19 | 19 | PLAIN | - |
| 9186 | 20 | 20 | PLAIN | - |
| 9187 | 21 | 21 | PLAIN | - |
| 9188 | 22 | 22 | PLAIN | - |
| 9189 | 23 | 23 | PLAIN | - |
| 9190 | 24 | 24 | PLAIN | - |
| 9191 | 26 | 26 | PLAIN | - |
| 9192 | 27 | 27 | PLAIN | - |
| 9194 | 36 | 36 | PLAIN | - |

#### Street: Тангатарская (ID: 402)

Кол-во домов: 54

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9344 | 2 | 2 | PLAIN | - |
| 9353 | 3 | 3 | PLAIN | - |
| 9365 | 4 | 4 | PLAIN | - |
| 9376 | 5 | 5 | PLAIN | - |
| 9382 | 5а | 5 | LETTER | а |
| 9383 | 6 | 6 | PLAIN | - |
| 9388 | 8к1 | 8 | CORPUS | 1 |
| 9389 | 9 | 9 | PLAIN | - |
| 9336 | 10 | 10 | PLAIN | - |
| 9337 | 10к2 | 10 | CORPUS | 2 |
| 9338 | 12/1 | 12 | FRACTION | 1 |
| 9339 | 12/2 | 12 | FRACTION | 2 |
| 9340 | 14 | 14 | PLAIN | - |
| 9341 | 15 | 15 | PLAIN | - |
| 9342 | 17 | 17 | PLAIN | - |
| 9343 | 19 | 19 | PLAIN | - |
| 9345 | 21 | 21 | PLAIN | - |
| 9346 | 23 | 23 | PLAIN | - |
| 9347 | 24 | 24 | PLAIN | - |
| 9348 | 25 | 25 | PLAIN | - |
| 9349 | 26 | 26 | PLAIN | - |
| 9350 | 27 | 27 | PLAIN | - |
| 9351 | 28 | 28 | PLAIN | - |
| 9352 | 29 | 29 | PLAIN | - |
| 9354 | 30 | 30 | PLAIN | - |
| 9355 | 31 | 31 | PLAIN | - |
| 9356 | 32 | 32 | PLAIN | - |
| 9357 | 33 | 33 | PLAIN | - |
| 9358 | 34 | 34 | PLAIN | - |
| 9359 | 34А | 34 | LETTER | а |
| 9360 | 35 | 35 | PLAIN | - |
| 9361 | 36 | 36 | PLAIN | - |
| 9362 | 37 | 37 | PLAIN | - |
| 9363 | 39 | 39 | PLAIN | - |
| 9364 | 39/1 | 39 | FRACTION | 1 |
| 9366 | 40 | 40 | PLAIN | - |
| 9367 | 41 | 41 | PLAIN | - |
| 9368 | 42 | 42 | PLAIN | - |
| 9369 | 43 | 43 | PLAIN | - |
| 9370 | 44 | 44 | PLAIN | - |
| 9371 | 45 | 45 | PLAIN | - |
| 9372 | 46 | 46 | PLAIN | - |
| 9373 | 47 | 47 | PLAIN | - |
| 9374 | 48 | 48 | PLAIN | - |
| 9375 | 49/1 | 49 | FRACTION | 1 |
| 9377 | 50 | 50 | PLAIN | - |
| 9378 | 52 | 52 | PLAIN | - |
| 9379 | 54 | 54 | PLAIN | - |
| 9380 | 56 | 56 | PLAIN | - |
| 9381 | 58 | 58 | PLAIN | - |
| 9384 | 60 | 60 | PLAIN | - |
| 9385 | 62 | 62 | PLAIN | - |
| 9386 | 64 | 64 | PLAIN | - |
| 9387 | 66 | 66 | PLAIN | - |

#### Street: Учалинская (ID: 406)

Кол-во домов: 15

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9507 | 1 | 1 | PLAIN | - |
| 9517 | 3 | 3 | PLAIN | - |
| 9518 | 3/1 | 3 | FRACTION | 1 |
| 9519 | 5 | 5 | PLAIN | - |
| 9520 | 8 | 8 | PLAIN | - |
| 9521 | 9 | 9 | PLAIN | - |
| 9508 | 10 | 10 | PLAIN | - |
| 9509 | 11 | 11 | PLAIN | - |
| 9510 | 12 | 12 | PLAIN | - |
| 9511 | 14 | 14 | PLAIN | - |
| 9512 | 16 | 16 | PLAIN | - |
| 9514 | 16к1 | 16 | CORPUS | 1 |
| 9513 | 16/2 | 16 | FRACTION | 2 |
| 9515 | 18 | 18 | PLAIN | - |
| 9516 | 18а | 18 | LETTER | а |

#### Street: Чапаева (ID: 413)

Кол-во домов: 7

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9854 | 1 | 1 | PLAIN | - |
| 9855 | 18 | 18 | PLAIN | - |
| 9856 | 19 | 19 | PLAIN | - |
| 9857 | 21 | 21 | PLAIN | - |
| 9858 | 23 | 23 | PLAIN | - |
| 9859 | 25 | 25 | PLAIN | - |
| 9860 | 27 | 27 | PLAIN | - |

#### Street: Шаймуратова (ID: 416)

Кол-во домов: 70

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9876 | 1 | 1 | PLAIN | - |
| 9900 | 3 | 3 | PLAIN | - |
| 9911 | 4 | 4 | PLAIN | - |
| 9912 | 4/1 | 4 | FRACTION | 1 |
| 9921 | 5 | 5 | PLAIN | - |
| 9930 | 6/1 | 6 | FRACTION | 1 |
| 9945 | 9 | 9 | PLAIN | - |
| 9877 | 11 | 11 | PLAIN | - |
| 9878 | 12 | 12 | PLAIN | - |
| 9879 | 12а | 12 | LETTER | а |
| 9880 | 13 | 13 | PLAIN | - |
| 9881 | 14 | 14 | PLAIN | - |
| 9882 | 14/1 | 14 | FRACTION | 1 |
| 9883 | 14/2 | 14 | FRACTION | 2 |
| 9884 | 15 | 15 | PLAIN | - |
| 9885 | 16 | 16 | PLAIN | - |
| 9886 | 16/1 | 16 | FRACTION | 1 |
| 9887 | 17 | 17 | PLAIN | - |
| 9888 | 18 | 18 | PLAIN | - |
| 9889 | 19 | 19 | PLAIN | - |
| 9890 | 20 | 20 | PLAIN | - |
| 9891 | 21 | 21 | PLAIN | - |
| 9892 | 22 | 22 | PLAIN | - |
| 9893 | 23 | 23 | PLAIN | - |
| 9894 | 24 | 24 | PLAIN | - |
| 9895 | 25 | 25 | PLAIN | - |
| 9896 | 26 | 26 | PLAIN | - |
| 9897 | 27 | 27 | PLAIN | - |
| 9898 | 28 | 28 | PLAIN | - |
| 9899 | 29 | 29 | PLAIN | - |
| 9901 | 30 | 30 | PLAIN | - |
| 9902 | 31 | 31 | PLAIN | - |
| 9903 | 32 | 32 | PLAIN | - |
| 9904 | 33 | 33 | PLAIN | - |
| 9905 | 34 | 34 | PLAIN | - |
| 9906 | 36 | 36 | PLAIN | - |
| 9907 | 37 | 37 | PLAIN | - |
| 9908 | 38 | 38 | PLAIN | - |
| 9910 | 39а | 39 | LETTER | а |
| 9909 | 39Б | 39 | LETTER | б |
| 9913 | 40 | 40 | PLAIN | - |
| 9914 | 41 | 41 | PLAIN | - |
| 9915 | 42 | 42 | PLAIN | - |
| 9916 | 43 | 43 | PLAIN | - |
| 9917 | 44 | 44 | PLAIN | - |
| 9918 | 45 | 45 | PLAIN | - |
| 9919 | 47 | 47 | PLAIN | - |
| 9920 | 49 | 49 | PLAIN | - |
| 9922 | 50 | 50 | PLAIN | - |
| 9923 | 51 | 51 | PLAIN | - |
| 9924 | 53 | 53 | PLAIN | - |
| 9925 | 53к1 | 53 | CORPUS | 1 |
| 9926 | 54 | 54 | PLAIN | - |
| 9927 | 55 | 55 | PLAIN | - |
| 9928 | 55/1 | 55 | FRACTION | 1 |
| 9929 | 57 | 57 | PLAIN | - |
| 9931 | 61 | 61 | PLAIN | - |
| 9932 | 63 | 63 | PLAIN | - |
| 9933 | 65 | 65 | PLAIN | - |
| 9934 | 67 | 67 | PLAIN | - |
| 9935 | 68 | 68 | PLAIN | - |
| 9936 | 71 | 71 | PLAIN | - |
| 9937 | 76 | 76 | PLAIN | - |
| 9938 | 77 | 77 | PLAIN | - |
| 9939 | 78 | 78 | PLAIN | - |
| 9940 | 80 | 80 | PLAIN | - |
| 9941 | 81 | 81 | PLAIN | - |
| 9942 | 84 | 84 | PLAIN | - |
| 9943 | 86 | 86 | PLAIN | - |
| 9944 | 86/1 | 86 | FRACTION | 1 |

#### Street: Школьная (ID: 418)

Кол-во домов: 6

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9992 | 1 | 1 | PLAIN | - |
| 9994 | 4 | 4 | PLAIN | - |
| 9995 | 5 | 5 | PLAIN | - |
| 9996 | 6 | 6 | PLAIN | - |
| 9997 | 7 | 7 | PLAIN | - |
| 9993 | 26 | 26 | PLAIN | - |

#### Street: Юбилейная (ID: 419)

Кол-во домов: 36

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9998 | 1 | 1 | PLAIN | - |
| 10005 | 1а | 1 | LETTER | а |
| 10012 | 3 | 3 | PLAIN | - |
| 10028 | 3а | 3 | LETTER | а |
| 10031 | 5 | 5 | PLAIN | - |
| 10032 | 7 | 7 | PLAIN | - |
| 10033 | 9 | 9 | PLAIN | - |
| 9999 | 12/1 | 12 | FRACTION | 1 |
| 10000 | 13 | 13 | PLAIN | - |
| 10001 | 14 | 14 | PLAIN | - |
| 10002 | 15 | 15 | PLAIN | - |
| 10003 | 17 | 17 | PLAIN | - |
| 10004 | 19 | 19 | PLAIN | - |
| 10006 | 21 | 21 | PLAIN | - |
| 10007 | 23 | 23 | PLAIN | - |
| 10008 | 23/1 | 23 | FRACTION | 1 |
| 10009 | 25 | 25 | PLAIN | - |
| 10010 | 27 | 27 | PLAIN | - |
| 10011 | 29 | 29 | PLAIN | - |
| 10013 | 31 | 31 | PLAIN | - |
| 10014 | 33 | 33 | PLAIN | - |
| 10016 | 33а | 33 | LETTER | а |
| 10017 | 33б | 33 | LETTER | б |
| 10015 | 33В | 33 | LETTER | в |
| 10018 | 33к1 | 33 | CORPUS | 1 |
| 10019 | 33к2 | 33 | CORPUS | 2 |
| 10020 | 33к4 | 33 | CORPUS | 4 |
| 10021 | 35 | 35 | PLAIN | - |
| 10022 | 35/1 | 35 | FRACTION | 1 |
| 10023 | 35/2 | 35 | FRACTION | 2 |
| 10024 | 35/3 | 35 | FRACTION | 3 |
| 10025 | 35/4 | 35 | FRACTION | 4 |
| 10026 | 37 | 37 | PLAIN | - |
| 10027 | 39 | 39 | PLAIN | - |
| 10029 | 41/2 | 41 | FRACTION | 2 |
| 10030 | 43/1 | 43 | FRACTION | 1 |

#### Street: Южная (ID: 420)

Кол-во домов: 36

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 10034 | 1 | 1 | PLAIN | - |
| 10045 | 2 | 2 | PLAIN | - |
| 10056 | 2а | 2 | LETTER | а |
| 10057 | 2б | 2 | LETTER | б |
| 10058 | 3 | 3 | PLAIN | - |
| 10064 | 4 | 4 | PLAIN | - |
| 10066 | 5 | 5 | PLAIN | - |
| 10067 | 7 | 7 | PLAIN | - |
| 10068 | 8 | 8 | PLAIN | - |
| 10069 | 9 | 9 | PLAIN | - |
| 10035 | 10 | 10 | PLAIN | - |
| 10036 | 11А | 11 | LETTER | а |
| 10037 | 12 | 12 | PLAIN | - |
| 10038 | 13 | 13 | PLAIN | - |
| 10039 | 14 | 14 | PLAIN | - |
| 10040 | 15 | 15 | PLAIN | - |
| 10041 | 16 | 16 | PLAIN | - |
| 10042 | 17 | 17 | PLAIN | - |
| 10043 | 18 | 18 | PLAIN | - |
| 10044 | 19 | 19 | PLAIN | - |
| 10046 | 20 | 20 | PLAIN | - |
| 10047 | 21 | 21 | PLAIN | - |
| 10048 | 22 | 22 | PLAIN | - |
| 10049 | 23 | 23 | PLAIN | - |
| 10050 | 24 | 24 | PLAIN | - |
| 10051 | 25 | 25 | PLAIN | - |
| 10052 | 26 | 26 | PLAIN | - |
| 10053 | 27 | 27 | PLAIN | - |
| 10054 | 28 | 28 | PLAIN | - |
| 10055 | 29 | 29 | PLAIN | - |
| 10059 | 30 | 30 | PLAIN | - |
| 10060 | 32 | 32 | PLAIN | - |
| 10061 | 34 | 34 | PLAIN | - |
| 10062 | 36 | 36 | PLAIN | - |
| 10063 | 38 | 38 | PLAIN | - |
| 10065 | 40 | 40 | PLAIN | - |

### District: Южный (ID: 20)

#### Street: 40 лет Победы (ID: 333)

Кол-во домов: 45

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6734 | 1 | 1 | PLAIN | - |
| 6746 | 2 | 2 | PLAIN | - |
| 6757 | 3 | 3 | PLAIN | - |
| 6766 | 4 | 4 | PLAIN | - |
| 6773 | 5 | 5 | PLAIN | - |
| 6775 | 6 | 6 | PLAIN | - |
| 6776 | 7 | 7 | PLAIN | - |
| 6777 | 8 | 8 | PLAIN | - |
| 6778 | 9 | 9 | PLAIN | - |
| 6735 | 10 | 10 | PLAIN | - |
| 6736 | 11 | 11 | PLAIN | - |
| 6737 | 12 | 12 | PLAIN | - |
| 6738 | 13 | 13 | PLAIN | - |
| 6739 | 14 | 14 | PLAIN | - |
| 6740 | 15 | 15 | PLAIN | - |
| 6741 | 16 | 16 | PLAIN | - |
| 6742 | 16/1 | 16 | FRACTION | 1 |
| 6743 | 17 | 17 | PLAIN | - |
| 6744 | 18 | 18 | PLAIN | - |
| 6745 | 19 | 19 | PLAIN | - |
| 6747 | 20 | 20 | PLAIN | - |
| 6748 | 21 | 21 | PLAIN | - |
| 6749 | 22 | 22 | PLAIN | - |
| 6750 | 23 | 23 | PLAIN | - |
| 6751 | 24 | 24 | PLAIN | - |
| 6752 | 25 | 25 | PLAIN | - |
| 6753 | 26 | 26 | PLAIN | - |
| 6754 | 27 | 27 | PLAIN | - |
| 6755 | 28 | 28 | PLAIN | - |
| 6756 | 29 | 29 | PLAIN | - |
| 6758 | 30 | 30 | PLAIN | - |
| 6759 | 31 | 31 | PLAIN | - |
| 6760 | 32 | 32 | PLAIN | - |
| 6761 | 34 | 34 | PLAIN | - |
| 6762 | 35 | 35 | PLAIN | - |
| 6763 | 36 | 36 | PLAIN | - |
| 6764 | 37 | 37 | PLAIN | - |
| 6765 | 39 | 39 | PLAIN | - |
| 6767 | 41 | 41 | PLAIN | - |
| 6768 | 43 | 43 | PLAIN | - |
| 6769 | 45 | 45 | PLAIN | - |
| 6770 | 47 | 47 | PLAIN | - |
| 6771 | 49 | 49 | PLAIN | - |
| 6772 | 49/2 | 49 | FRACTION | 2 |
| 6774 | 51 | 51 | PLAIN | - |

#### Street: 70 лет Октября (ID: 337)

Кол-во домов: 81

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 6965 | 1 | 1 | PLAIN | - |
| 6983 | 2 | 2 | PLAIN | - |
| 6994 | 3 | 3 | PLAIN | - |
| 7002 | 4 | 4 | PLAIN | - |
| 7009 | 5 | 5 | PLAIN | - |
| 7028 | 6 | 6 | PLAIN | - |
| 7039 | 8 | 8 | PLAIN | - |
| 7045 | 9 | 9 | PLAIN | - |
| 6966 | 10 | 10 | PLAIN | - |
| 6967 | 11 | 11 | PLAIN | - |
| 6968 | 12 | 12 | PLAIN | - |
| 6969 | 14 | 14 | PLAIN | - |
| 6970 | 15 | 15 | PLAIN | - |
| 6971 | 15/1 | 15 | FRACTION | 1 |
| 6972 | 16 | 16 | PLAIN | - |
| 6973 | 17 | 17 | PLAIN | - |
| 6974 | 17к1 | 17 | CORPUS | 1 |
| 6975 | 17к2 | 17 | CORPUS | 2 |
| 6976 | 17к3 | 17 | CORPUS | 3 |
| 6977 | 17к4 | 17 | CORPUS | 4 |
| 6978 | 18 | 18 | PLAIN | - |
| 6979 | 19 | 19 | PLAIN | - |
| 6980 | 19к1 | 19 | CORPUS | 1 |
| 6981 | 19к2 | 19 | CORPUS | 2 |
| 6982 | 19к3 | 19 | CORPUS | 3 |
| 6984 | 21 | 21 | PLAIN | - |
| 6985 | 22 | 22 | PLAIN | - |
| 6986 | 22/1 | 22 | FRACTION | 1 |
| 6987 | 22/2 | 22 | FRACTION | 2 |
| 6988 | 23 | 23 | PLAIN | - |
| 6989 | 25 | 25 | PLAIN | - |
| 6990 | 26 | 26 | PLAIN | - |
| 6991 | 27 | 27 | PLAIN | - |
| 6992 | 28 | 28 | PLAIN | - |
| 6993 | 29 | 29 | PLAIN | - |
| 6995 | 32 | 32 | PLAIN | - |
| 6996 | 33 | 33 | PLAIN | - |
| 6997 | 34 | 34 | PLAIN | - |
| 6998 | 35 | 35 | PLAIN | - |
| 6999 | 36 | 36 | PLAIN | - |
| 7000 | 37 | 37 | PLAIN | - |
| 7001 | 38 | 38 | PLAIN | - |
| 7003 | 41 | 41 | PLAIN | - |
| 7004 | 43 | 43 | PLAIN | - |
| 7005 | 46 | 46 | PLAIN | - |
| 7006 | 47 | 47 | PLAIN | - |
| 7007 | 48 | 48 | PLAIN | - |
| 7008 | 49 | 49 | PLAIN | - |
| 7010 | 50 | 50 | PLAIN | - |
| 7011 | 51 | 51 | PLAIN | - |
| 7013 | 51к2 | 51 | CORPUS | 2 |
| 7014 | 51к3 | 51 | CORPUS | 3 |
| 7015 | 51к4 | 51 | CORPUS | 4 |
| 7016 | 51к5 | 51 | CORPUS | 5 |
| 7012 | 51/1 | 51 | FRACTION | 1 |
| 7017 | 52 | 52 | PLAIN | - |
| 7018 | 53 | 53 | PLAIN | - |
| 7019 | 53к1 | 53 | CORPUS | 1 |
| 7020 | 53к2 | 53 | CORPUS | 2 |
| 7021 | 53к3 | 53 | CORPUS | 3 |
| 7022 | 54 | 54 | PLAIN | - |
| 7023 | 55 | 55 | PLAIN | - |
| 7024 | 56 | 56 | PLAIN | - |
| 7025 | 57 | 57 | PLAIN | - |
| 7026 | 58 | 58 | PLAIN | - |
| 7027 | 59 | 59 | PLAIN | - |
| 7029 | 60 | 60 | PLAIN | - |
| 7030 | 63 | 63 | PLAIN | - |
| 7031 | 65 | 65 | PLAIN | - |
| 7032 | 67 | 67 | PLAIN | - |
| 7033 | 69 | 69 | PLAIN | - |
| 7034 | 71 | 71 | PLAIN | - |
| 7035 | 73 | 73 | PLAIN | - |
| 7036 | 75 | 75 | PLAIN | - |
| 7037 | 77 | 77 | PLAIN | - |
| 7038 | 79 | 79 | PLAIN | - |
| 7040 | 81 | 81 | PLAIN | - |
| 7041 | 83 | 83 | PLAIN | - |
| 7042 | 85 | 85 | PLAIN | - |
| 7043 | 87 | 87 | PLAIN | - |
| 7044 | 89 | 89 | PLAIN | - |

#### Street: Горная (ID: 431)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Дружбы (ID: 348)

Кол-во домов: 35

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7331 | 1 | 1 | PLAIN | - |
| 7343 | 2 | 2 | PLAIN | - |
| 7354 | 3 | 3 | PLAIN | - |
| 7360 | 4 | 4 | PLAIN | - |
| 7361 | 5 | 5 | PLAIN | - |
| 7362 | 6 | 6 | PLAIN | - |
| 7363 | 7 | 7 | PLAIN | - |
| 7364 | 8 | 8 | PLAIN | - |
| 7365 | 9 | 9 | PLAIN | - |
| 7332 | 10 | 10 | PLAIN | - |
| 7333 | 11 | 11 | PLAIN | - |
| 7334 | 11к1 | 11 | CORPUS | 1 |
| 7335 | 12 | 12 | PLAIN | - |
| 7336 | 13 | 13 | PLAIN | - |
| 7337 | 14 | 14 | PLAIN | - |
| 7338 | 15 | 15 | PLAIN | - |
| 7339 | 16 | 16 | PLAIN | - |
| 7340 | 17 | 17 | PLAIN | - |
| 7341 | 18 | 18 | PLAIN | - |
| 7342 | 19 | 19 | PLAIN | - |
| 7344 | 20 | 20 | PLAIN | - |
| 7345 | 21 | 21 | PLAIN | - |
| 7346 | 22 | 22 | PLAIN | - |
| 7347 | 23 | 23 | PLAIN | - |
| 7348 | 23А | 23 | LETTER | а |
| 7349 | 24 | 24 | PLAIN | - |
| 7350 | 25 | 25 | PLAIN | - |
| 7351 | 26 | 26 | PLAIN | - |
| 7352 | 27 | 27 | PLAIN | - |
| 7353 | 28 | 28 | PLAIN | - |
| 7355 | 30 | 30 | PLAIN | - |
| 7356 | 31 | 31 | PLAIN | - |
| 7357 | 32 | 32 | PLAIN | - |
| 7358 | 33 | 33 | PLAIN | - |
| 7359 | 35/1 | 35 | FRACTION | 1 |

#### Street: Идяш (ID: 352)

Кол-во домов: 45

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7434 | 1 | 1 | PLAIN | - |
| 7440 | 2 | 2 | PLAIN | - |
| 7446 | 3 | 3 | PLAIN | - |
| 7452 | 4 | 4 | PLAIN | - |
| 7464 | 5 | 5 | PLAIN | - |
| 7471 | 6 | 6 | PLAIN | - |
| 7472 | 7 | 7 | PLAIN | - |
| 7473 | 8 | 8 | PLAIN | - |
| 7476 | 9 | 9 | PLAIN | - |
| 7435 | 10 | 10 | PLAIN | - |
| 7436 | 12 | 12 | PLAIN | - |
| 7437 | 14 | 14 | PLAIN | - |
| 7438 | 16 | 16 | PLAIN | - |
| 7439 | 18 | 18 | PLAIN | - |
| 7441 | 20 | 20 | PLAIN | - |
| 7442 | 22 | 22 | PLAIN | - |
| 7443 | 24 | 24 | PLAIN | - |
| 7444 | 26 | 26 | PLAIN | - |
| 7445 | 28 | 28 | PLAIN | - |
| 7447 | 30 | 30 | PLAIN | - |
| 7448 | 32 | 32 | PLAIN | - |
| 7449 | 34 | 34 | PLAIN | - |
| 7450 | 36 | 36 | PLAIN | - |
| 7451 | 38 | 38 | PLAIN | - |
| 7453 | 40 | 40 | PLAIN | - |
| 7454 | 41 | 41 | PLAIN | - |
| 7455 | 42 | 42 | PLAIN | - |
| 7456 | 43 | 43 | PLAIN | - |
| 7457 | 44 | 44 | PLAIN | - |
| 7458 | 45 | 45 | PLAIN | - |
| 7459 | 45/1 | 45 | FRACTION | 1 |
| 7460 | 46 | 46 | PLAIN | - |
| 7461 | 47 | 47 | PLAIN | - |
| 7462 | 48 | 48 | PLAIN | - |
| 7463 | 49 | 49 | PLAIN | - |
| 7465 | 50 | 50 | PLAIN | - |
| 7466 | 51 | 51 | PLAIN | - |
| 7467 | 52 | 52 | PLAIN | - |
| 7468 | 53 | 53 | PLAIN | - |
| 7469 | 56 | 56 | PLAIN | - |
| 7470 | 57 | 57 | PLAIN | - |
| 7474 | 86А | 86 | LETTER | а |
| 7475 | 87 | 87 | PLAIN | - |
| 7477 | 91 | 91 | PLAIN | - |
| 7478 | 93 | 93 | PLAIN | - |

#### Street: Идяшево (ID: 429)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Искра (ID: 354)

Кол-во домов: 22

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 7484 | 1 | 1 | PLAIN | - |
| 7494 | 2 | 2 | PLAIN | - |
| 7500 | 3 | 3 | PLAIN | - |
| 7501 | 4 | 4 | PLAIN | - |
| 7502 | 6 | 6 | PLAIN | - |
| 7503 | 7 | 7 | PLAIN | - |
| 7504 | 8 | 8 | PLAIN | - |
| 7505 | 9 | 9 | PLAIN | - |
| 7485 | 10 | 10 | PLAIN | - |
| 7486 | 11 | 11 | PLAIN | - |
| 7487 | 12 | 12 | PLAIN | - |
| 7488 | 13 | 13 | PLAIN | - |
| 7489 | 14 | 14 | PLAIN | - |
| 7490 | 15 | 15 | PLAIN | - |
| 7491 | 16 | 16 | PLAIN | - |
| 7492 | 17 | 17 | PLAIN | - |
| 7493 | 19 | 19 | PLAIN | - |
| 7495 | 21 | 21 | PLAIN | - |
| 7496 | 23 | 23 | PLAIN | - |
| 7497 | 25 | 25 | PLAIN | - |
| 7498 | 26 | 26 | PLAIN | - |
| 7499 | 27 | 27 | PLAIN | - |

#### Street: Кирова (ID: 434)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Лесная (ID: 365)

Кол-во домов: 19

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8039 | 1 | 1 | PLAIN | - |
| 8046 | 2 | 2 | PLAIN | - |
| 8051 | 3 | 3 | PLAIN | - |
| 8052 | 4 | 4 | PLAIN | - |
| 8053 | 5 | 5 | PLAIN | - |
| 8054 | 6 | 6 | PLAIN | - |
| 8055 | 7 | 7 | PLAIN | - |
| 8056 | 8 | 8 | PLAIN | - |
| 8057 | 9 | 9 | PLAIN | - |
| 8040 | 11 | 11 | PLAIN | - |
| 8041 | 13 | 13 | PLAIN | - |
| 8042 | 14 | 14 | PLAIN | - |
| 8043 | 15 | 15 | PLAIN | - |
| 8044 | 16 | 16 | PLAIN | - |
| 8045 | 18 | 18 | PLAIN | - |
| 8047 | 20 | 20 | PLAIN | - |
| 8048 | 22 | 22 | PLAIN | - |
| 8049 | 24 | 24 | PLAIN | - |
| 8050 | 26 | 26 | PLAIN | - |

#### Street: Мажита Гафури (ID: 368)

Кол-во домов: 18

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8120 | 1 | 1 | PLAIN | - |
| 8121 | 1/1 | 1 | FRACTION | 1 |
| 8130 | 2 | 2 | PLAIN | - |
| 8137 | 4 | 4 | PLAIN | - |
| 8122 | 10 | 10 | PLAIN | - |
| 8123 | 13 | 13 | PLAIN | - |
| 8124 | 14 | 14 | PLAIN | - |
| 8125 | 15 | 15 | PLAIN | - |
| 8126 | 16 | 16 | PLAIN | - |
| 8127 | 17 | 17 | PLAIN | - |
| 8128 | 18 | 18 | PLAIN | - |
| 8129 | 19 | 19 | PLAIN | - |
| 8131 | 20 | 20 | PLAIN | - |
| 8132 | 21 | 21 | PLAIN | - |
| 8133 | 22 | 22 | PLAIN | - |
| 8134 | 23 | 23 | PLAIN | - |
| 8135 | 25 | 25 | PLAIN | - |
| 8136 | 27 | 27 | PLAIN | - |

#### Street: Мелиораторов (ID: 371)

Кол-во домов: 27

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8184 | 1 | 1 | PLAIN | - |
| 8194 | 2 | 2 | PLAIN | - |
| 8201 | 3 | 3 | PLAIN | - |
| 8202 | 4 | 4 | PLAIN | - |
| 8203 | 5 | 5 | PLAIN | - |
| 8204 | 6 | 6 | PLAIN | - |
| 8205 | 6к1 | 6 | CORPUS | 1 |
| 8206 | 7 | 7 | PLAIN | - |
| 8207 | 7а | 7 | LETTER | а |
| 8208 | 8 | 8 | PLAIN | - |
| 8209 | 8к1 | 8 | CORPUS | 1 |
| 8210 | 9 | 9 | PLAIN | - |
| 8185 | 10 | 10 | PLAIN | - |
| 8186 | 11 | 11 | PLAIN | - |
| 8187 | 12 | 12 | PLAIN | - |
| 8188 | 13 | 13 | PLAIN | - |
| 8189 | 14 | 14 | PLAIN | - |
| 8190 | 15 | 15 | PLAIN | - |
| 8191 | 16 | 16 | PLAIN | - |
| 8192 | 17 | 17 | PLAIN | - |
| 8193 | 19 | 19 | PLAIN | - |
| 8195 | 20 | 20 | PLAIN | - |
| 8196 | 21 | 21 | PLAIN | - |
| 8197 | 22 | 22 | PLAIN | - |
| 8198 | 23 | 23 | PLAIN | - |
| 8199 | 24 | 24 | PLAIN | - |
| 8200 | 26 | 26 | PLAIN | - |

#### Street: Механизаторов (ID: 372)

Кол-во домов: 21

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8211 | 1 | 1 | PLAIN | - |
| 8222 | 2 | 2 | PLAIN | - |
| 8225 | 3 | 3 | PLAIN | - |
| 8226 | 4 | 4 | PLAIN | - |
| 8227 | 5 | 5 | PLAIN | - |
| 8228 | 6 | 6 | PLAIN | - |
| 8229 | 7 | 7 | PLAIN | - |
| 8230 | 8 | 8 | PLAIN | - |
| 8231 | 9 | 9 | PLAIN | - |
| 8212 | 10 | 10 | PLAIN | - |
| 8213 | 11 | 11 | PLAIN | - |
| 8214 | 12 | 12 | PLAIN | - |
| 8215 | 13 | 13 | PLAIN | - |
| 8216 | 14 | 14 | PLAIN | - |
| 8217 | 15 | 15 | PLAIN | - |
| 8218 | 16 | 16 | PLAIN | - |
| 8219 | 17 | 17 | PLAIN | - |
| 8220 | 18 | 18 | PLAIN | - |
| 8221 | 19 | 19 | PLAIN | - |
| 8223 | 20 | 20 | PLAIN | - |
| 8224 | 22 | 22 | PLAIN | - |

#### Street: Октябрьская (ID: 433)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Партизанская (ID: 432)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

#### Street: Пионерская (ID: 383)

Кол-во домов: 25

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8606 | 1 | 1 | PLAIN | - |
| 8614 | 2 | 2 | PLAIN | - |
| 8623 | 2А | 2 | LETTER | а |
| 8615 | 2/1 | 2 | FRACTION | 1 |
| 8616 | 2/3 | 2 | FRACTION | 3 |
| 8624 | 3 | 3 | PLAIN | - |
| 8627 | 4/1 | 4 | FRACTION | 1 |
| 8628 | 5 | 5 | PLAIN | - |
| 8629 | 7 | 7 | PLAIN | - |
| 8630 | 9 | 9 | PLAIN | - |
| 8607 | 11 | 11 | PLAIN | - |
| 8608 | 13 | 13 | PLAIN | - |
| 8609 | 15 | 15 | PLAIN | - |
| 8610 | 17 | 17 | PLAIN | - |
| 8611 | 18/1 | 18 | FRACTION | 1 |
| 8612 | 18/2 | 18 | FRACTION | 2 |
| 8613 | 19 | 19 | PLAIN | - |
| 8617 | 20 | 20 | PLAIN | - |
| 8618 | 21 | 21 | PLAIN | - |
| 8619 | 23 | 23 | PLAIN | - |
| 8620 | 25 | 25 | PLAIN | - |
| 8621 | 27 | 27 | PLAIN | - |
| 8622 | 29 | 29 | PLAIN | - |
| 8625 | 31 | 31 | PLAIN | - |
| 8626 | 33 | 33 | PLAIN | - |

#### Street: Рауфа Давлетова (ID: 388)

Кол-во домов: 66

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8796 | 1 | 1 | PLAIN | - |
| 8813 | 1к3 | 1 | CORPUS | 3 |
| 8814 | 1к4 | 1 | CORPUS | 4 |
| 8797 | 1/2 | 1 | FRACTION | 2 |
| 8798 | 1/7 | 1 | FRACTION | 7 |
| 8815 | 2 | 2 | PLAIN | - |
| 8827 | 2а | 2 | LETTER | а |
| 8828 | 2б | 2 | LETTER | б |
| 8816 | 2/1 | 2 | FRACTION | 1 |
| 8829 | 3 | 3 | PLAIN | - |
| 8837 | 4 | 4 | PLAIN | - |
| 8838 | 4/1 | 4 | FRACTION | 1 |
| 8844 | 5 | 5 | PLAIN | - |
| 8851 | 6 | 6 | PLAIN | - |
| 8852 | 6/2 | 6 | FRACTION | 2 |
| 8853 | 6/3 | 6 | FRACTION | 3 |
| 8858 | 7 | 7 | PLAIN | - |
| 8860 | 8/4 | 8 | FRACTION | 4 |
| 8861 | 9 | 9 | PLAIN | - |
| 8799 | 10/1 | 10 | FRACTION | 1 |
| 8800 | 10/3 | 10 | FRACTION | 3 |
| 8801 | 10/4 | 10 | FRACTION | 4 |
| 8802 | 11 | 11 | PLAIN | - |
| 8803 | 12 | 12 | PLAIN | - |
| 8804 | 13 | 13 | PLAIN | - |
| 8805 | 14/1 | 14 | FRACTION | 1 |
| 8806 | 15 | 15 | PLAIN | - |
| 8807 | 15/1 | 15 | FRACTION | 1 |
| 8808 | 15/2 | 15 | FRACTION | 2 |
| 8809 | 16/3 | 16 | FRACTION | 3 |
| 8810 | 17 | 17 | PLAIN | - |
| 8811 | 18 | 18 | PLAIN | - |
| 8812 | 19 | 19 | PLAIN | - |
| 8817 | 20 | 20 | PLAIN | - |
| 8818 | 21 | 21 | PLAIN | - |
| 8819 | 22 | 22 | PLAIN | - |
| 8820 | 23 | 23 | PLAIN | - |
| 8821 | 24 | 24 | PLAIN | - |
| 8822 | 25 | 25 | PLAIN | - |
| 8823 | 26 | 26 | PLAIN | - |
| 8824 | 27 | 27 | PLAIN | - |
| 8825 | 28 | 28 | PLAIN | - |
| 8826 | 29 | 29 | PLAIN | - |
| 8830 | 30 | 30 | PLAIN | - |
| 8831 | 32 | 32 | PLAIN | - |
| 8832 | 33 | 33 | PLAIN | - |
| 8833 | 34 | 34 | PLAIN | - |
| 8834 | 35 | 35 | PLAIN | - |
| 8835 | 37 | 37 | PLAIN | - |
| 8836 | 39 | 39 | PLAIN | - |
| 8839 | 41 | 41 | PLAIN | - |
| 8840 | 43 | 43 | PLAIN | - |
| 8841 | 45 | 45 | PLAIN | - |
| 8842 | 47 | 47 | PLAIN | - |
| 8843 | 49 | 49 | PLAIN | - |
| 8845 | 51 | 51 | PLAIN | - |
| 8846 | 53 | 53 | PLAIN | - |
| 8847 | 55 | 55 | PLAIN | - |
| 8848 | 57 | 57 | PLAIN | - |
| 8849 | 58 | 58 | PLAIN | - |
| 8850 | 59 | 59 | PLAIN | - |
| 8854 | 61 | 61 | PLAIN | - |
| 8855 | 63 | 63 | PLAIN | - |
| 8856 | 65 | 65 | PLAIN | - |
| 8857 | 68 | 68 | PLAIN | - |
| 8859 | 70 | 70 | PLAIN | - |

#### Street: Рихарда Зорге (ID: 390)

Кол-во домов: 66

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 8938 | 2 | 2 | PLAIN | - |
| 8939 | 2/1 | 2 | FRACTION | 1 |
| 8951 | 3 | 3 | PLAIN | - |
| 8965 | 4 | 4 | PLAIN | - |
| 8976 | 5 | 5 | PLAIN | - |
| 8981 | 6 | 6 | PLAIN | - |
| 8983 | 7 | 7 | PLAIN | - |
| 8984 | 8 | 8 | PLAIN | - |
| 8985 | 9 | 9 | PLAIN | - |
| 8986 | 9/1 | 9 | FRACTION | 1 |
| 8987 | 9/2 | 9 | FRACTION | 2 |
| 8988 | 9/3 | 9 | FRACTION | 3 |
| 8989 | 9/5 | 9 | FRACTION | 5 |
| 8924 | 10 | 10 | PLAIN | - |
| 8925 | 11 | 11 | PLAIN | - |
| 8926 | 12 | 12 | PLAIN | - |
| 8927 | 13 | 13 | PLAIN | - |
| 8928 | 14/1 | 14 | FRACTION | 1 |
| 8929 | 14/2 | 14 | FRACTION | 2 |
| 8930 | 15 | 15 | PLAIN | - |
| 8931 | 16 | 16 | PLAIN | - |
| 8934 | 16а | 16 | LETTER | а |
| 8932 | 16/1 | 16 | FRACTION | 1 |
| 8933 | 16/2 | 16 | FRACTION | 2 |
| 8935 | 17 | 17 | PLAIN | - |
| 8936 | 18 | 18 | PLAIN | - |
| 8937 | 19 | 19 | PLAIN | - |
| 8940 | 20 | 20 | PLAIN | - |
| 8941 | 21 | 21 | PLAIN | - |
| 8942 | 22 | 22 | PLAIN | - |
| 8943 | 23 | 23 | PLAIN | - |
| 8944 | 24 | 24 | PLAIN | - |
| 8945 | 24А | 24 | LETTER | а |
| 8946 | 25 | 25 | PLAIN | - |
| 8947 | 26 | 26 | PLAIN | - |
| 8948 | 27 | 27 | PLAIN | - |
| 8949 | 28 | 28 | PLAIN | - |
| 8950 | 29 | 29 | PLAIN | - |
| 8952 | 30 | 30 | PLAIN | - |
| 8953 | 31 | 31 | PLAIN | - |
| 8954 | 32 | 32 | PLAIN | - |
| 8955 | 33 | 33 | PLAIN | - |
| 8956 | 34 | 34 | PLAIN | - |
| 8957 | 35 | 35 | PLAIN | - |
| 8958 | 36 | 36 | PLAIN | - |
| 8959 | 37 | 37 | PLAIN | - |
| 8962 | 37а | 37 | LETTER | а |
| 8961 | 37Б | 37 | LETTER | б |
| 8960 | 37/1 | 37 | FRACTION | 1 |
| 8963 | 38 | 38 | PLAIN | - |
| 8964 | 39 | 39 | PLAIN | - |
| 8966 | 40 | 40 | PLAIN | - |
| 8967 | 41 | 41 | PLAIN | - |
| 8968 | 42 | 42 | PLAIN | - |
| 8969 | 43 | 43 | PLAIN | - |
| 8970 | 44 | 44 | PLAIN | - |
| 8971 | 45 | 45 | PLAIN | - |
| 8972 | 45/1 | 45 | FRACTION | 1 |
| 8973 | 46 | 46 | PLAIN | - |
| 8974 | 47 | 47 | PLAIN | - |
| 8975 | 48 | 48 | PLAIN | - |
| 8977 | 50 | 50 | PLAIN | - |
| 8978 | 52 | 52 | PLAIN | - |
| 8979 | 52А | 52 | LETTER | а |
| 8980 | 54 | 54 | PLAIN | - |
| 8982 | 68 | 68 | PLAIN | - |

#### Street: Строителей (ID: 399)

Кол-во домов: 27

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9251 | 1 | 1 | PLAIN | - |
| 9262 | 1а | 1 | LETTER | а |
| 9263 | 2 | 2 | PLAIN | - |
| 9270 | 2А | 2 | LETTER | а |
| 9271 | 3/2 | 3 | FRACTION | 2 |
| 9272 | 4 | 4 | PLAIN | - |
| 9273 | 5 | 5 | PLAIN | - |
| 9274 | 6 | 6 | PLAIN | - |
| 9275 | 7 | 7 | PLAIN | - |
| 9276 | 8 | 8 | PLAIN | - |
| 9277 | 9 | 9 | PLAIN | - |
| 9252 | 10 | 10 | PLAIN | - |
| 9253 | 11 | 11 | PLAIN | - |
| 9254 | 12 | 12 | PLAIN | - |
| 9255 | 13 | 13 | PLAIN | - |
| 9256 | 14 | 14 | PLAIN | - |
| 9257 | 15 | 15 | PLAIN | - |
| 9258 | 16 | 16 | PLAIN | - |
| 9259 | 17 | 17 | PLAIN | - |
| 9260 | 18 | 18 | PLAIN | - |
| 9261 | 19 | 19 | PLAIN | - |
| 9264 | 20 | 20 | PLAIN | - |
| 9265 | 21 | 21 | PLAIN | - |
| 9266 | 22 | 22 | PLAIN | - |
| 9267 | 23 | 23 | PLAIN | - |
| 9268 | 23/1 | 23 | FRACTION | 1 |
| 9269 | 24 | 24 | PLAIN | - |

#### Street: Тагира Кусимова (ID: 400)

Кол-во домов: 15

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|
| 9278 | 1 | 1 | PLAIN | - |
| 9285 | 2 | 2 | PLAIN | - |
| 9286 | 3 | 3 | PLAIN | - |
| 9287 | 4 | 4 | PLAIN | - |
| 9288 | 5 | 5 | PLAIN | - |
| 9289 | 6 | 6 | PLAIN | - |
| 9290 | 7 | 7 | PLAIN | - |
| 9291 | 8 | 8 | PLAIN | - |
| 9292 | 9 | 9 | PLAIN | - |
| 9279 | 10 | 10 | PLAIN | - |
| 9280 | 11 | 11 | PLAIN | - |
| 9281 | 12 | 12 | PLAIN | - |
| 9282 | 14 | 14 | PLAIN | - |
| 9283 | 16 | 16 | PLAIN | - |
| 9284 | 18 | 18 | PLAIN | - |

#### Street: Южная (ID: 430)

Кол-во домов: 0

| House ID | Number | Base | Type | Suffix |
|---|---|---|---|---|

---

# House Number Groups

Дома, сгруппированные по (улица, base). Такие группы — источник реальных данных для тестов address resolution.

Всего групп: **2951**.

## 60 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 1
- 1/1

## 60 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 2

## 60 лет Победы / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 3

## 60 лет Победы / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 5

## 60 лет Победы / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 6
- 6/1
- 6/2

## 60 лет Победы / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 7

## 60 лет Победы / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 8

## 60 лет Победы / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 9

## 60 лет Победы / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 10

## 60 лет Победы / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 11

## 60 лет Победы / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 12

## 60 лет Победы / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 13

## 60 лет Победы / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 15
- 15А

## 60 лет Победы / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 17

## 60 лет Победы / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 18
- 18а
- 18б
- 18/1
- 18/2

## 60 лет Победы / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 19

## 60 лет Победы / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 20
- 20/2

## 60 лет Победы / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 21

## 60 лет Победы / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 22

## 60 лет Победы / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 23

## 60 лет Победы / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 24

## 60 лет Победы / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 25

## 60 лет Победы / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 26

## 60 лет Победы / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 27

## 60 лет Победы / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 28

## 60 лет Победы / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 29

## 60 лет Победы / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 30

## 60 лет Победы / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 31

## 60 лет Победы / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 32

## 60 лет Победы / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 33

## 60 лет Победы / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 34

## 60 лет Победы / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 35

## 60 лет Победы / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 36

## 60 лет Победы / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 37

## 60 лет Победы / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 39

## 60 лет Победы / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 40

## 60 лет Победы / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 41

## 60 лет Победы / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 42

## 60 лет Победы / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 45

## 60 лет Победы / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 46
- 46А
- 46/1

## 60 лет Победы / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 47

## 60 лет Победы / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 48

## 60 лет Победы / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 49

## 60 лет Победы / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 50

## 60 лет Победы / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 51
- 51/1

## 60 лет Победы / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 52

## 60 лет Победы / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 53

## 60 лет Победы / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 54

## 60 лет Победы / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 56

## 60 лет Победы / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 57

## 60 лет Победы / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 58

## 60 лет Победы / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 59

## 60 лет Победы / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 60

## 60 лет Победы / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 61

## 60 лет Победы / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 62

## 60 лет Победы / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 63

## 60 лет Победы / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 64

## 60 лет Победы / base=68

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 68

## 60 лет Победы / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 72

## 60 лет Победы / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 79
- 79/1

## 60 лет Победы / base=81

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 81

## 60 лет Победы / base=83

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 83

## 60 лет Победы / base=85

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335

- 85

## Абзелиловская / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 1
- 1а

## Абзелиловская / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 3

## Абзелиловская / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 4

## Абзелиловская / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 5

## Абзелиловская / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 6

## Абзелиловская / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 8

## Абзелиловская / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 9

## Абзелиловская / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 10

## Абзелиловская / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 11

## Абзелиловская / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 12

## Абзелиловская / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 13

## Абзелиловская / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 14

## Абзелиловская / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 15

## Абзелиловская / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 17

## Абзелиловская / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 18

## Абзелиловская / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 19

## Абзелиловская / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338

- 23

## Вафира Тайсина / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 1А
- 1Б

## Вафира Тайсина / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 2
- 2/1
- 2/2

## Вафира Тайсина / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 3

## Вафира Тайсина / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 4

## Вафира Тайсина / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 6

## Вафира Тайсина / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 8

## Вафира Тайсина / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 9

## Вафира Тайсина / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 10

## Вафира Тайсина / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 11
- 11/1

## Вафира Тайсина / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 12

## Вафира Тайсина / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 14

## Вафира Тайсина / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 15

## Вафира Тайсина / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 16

## Вафира Тайсина / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 17

## Вафира Тайсина / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 19

## Вафира Тайсина / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 21

## Вафира Тайсина / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343

- 23

## Весенняя / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 344

- 7

## Гинията Ушанова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 1

## Гинията Ушанова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 2

## Гинията Ушанова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 3

## Гинията Ушанова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 4

## Гинията Ушанова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 5

## Гинията Ушанова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 6

## Гинията Ушанова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 7

## Гинията Ушанова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 8

## Гинията Ушанова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 9

## Гинията Ушанова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 10

## Гинията Ушанова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 11

## Гинията Ушанова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 12

## Гинията Ушанова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 13

## Гинията Ушанова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 14

## Гинията Ушанова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 15

## Гинията Ушанова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 16

## Гинията Ушанова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 17

## Гинията Ушанова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 18

## Гинията Ушанова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 19

## Гинията Ушанова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 20

## Гинията Ушанова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 21

## Гинията Ушанова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 22

## Гинията Ушанова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 23

## Гинията Ушанова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 24

## Гинията Ушанова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 25

## Гинията Ушанова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 26

## Гинията Ушанова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 27

## Гинията Ушанова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 28

## Гинията Ушанова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 29

## Гинията Ушанова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 30

## Гинията Ушанова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 31

## Гинията Ушанова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 32

## Гинията Ушанова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 33

## Гинията Ушанова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 34

## Гинията Ушанова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 35

## Гинията Ушанова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 36

## Гинията Ушанова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 37

## Гинията Ушанова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 38

## Гинията Ушанова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 39

## Гинията Ушанова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 40

## Гинията Ушанова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 346

- 56

## Емельяна Пугачева / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 4

## Емельяна Пугачева / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 5

## Емельяна Пугачева / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 6

## Емельяна Пугачева / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 7

## Емельяна Пугачева / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 9

## Емельяна Пугачева / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 12

## Емельяна Пугачева / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 15

## Емельяна Пугачева / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 17

## Емельяна Пугачева / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 25

## Емельяна Пугачева / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 26

## Емельяна Пугачева / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 349

- 44

## Загира Исмагилова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 1

## Загира Исмагилова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 3

## Загира Исмагилова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 5

## Загира Исмагилова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 9

## Загира Исмагилова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 10

## Загира Исмагилова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 11

## Загира Исмагилова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 12

## Загира Исмагилова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 13

## Загира Исмагилова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 14

## Загира Исмагилова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 15/1

## Загира Исмагилова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 16

## Загира Исмагилова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 17

## Загира Исмагилова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 18

## Загира Исмагилова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 19

## Загира Исмагилова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 20

## Загира Исмагилова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 22

## Загира Исмагилова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 23

## Загира Исмагилова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 25

## Загира Исмагилова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 27/1

## Загира Исмагилова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 29

## Загира Исмагилова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 31

## Загира Исмагилова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 32/1

## Загира Исмагилова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 33

## Загира Исмагилова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 34

## Загира Исмагилова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 35

## Загира Исмагилова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 36

## Загира Исмагилова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 38

## Загира Исмагилова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 39

## Загира Исмагилова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 40

## Загира Исмагилова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 41

## Загира Исмагилова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 42

## Загира Исмагилова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 43

## Загира Исмагилова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 44

## Загира Исмагилова / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 46

## Загира Исмагилова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350

- 49

## Зайнаб Биишевой / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 9/1

## Зайнаб Биишевой / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 22

## Зайнаб Биишевой / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 23

## Зайнаб Биишевой / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 24

## Зайнаб Биишевой / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 25

## Зайнаб Биишевой / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 26

## Зайнаб Биишевой / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 30

## Зайнаб Биишевой / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 32

## Зайнаб Биишевой / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 36

## Зайнаб Биишевой / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 37
- 37/1

## Зайнаб Биишевой / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 39

## Зайнаб Биишевой / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 40

## Зайнаб Биишевой / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 44

## Зайнаб Биишевой / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 46

## Зайнаб Биишевой / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 48

## Зайнаб Биишевой / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 49

## Зайнаб Биишевой / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 50/1

## Зайнаб Биишевой / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 52

## Зайнаб Биишевой / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 54

## Зайнаб Биишевой / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 56

## Зайнаб Биишевой / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351

- 64

## Ишмухамета Мырзакаева / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 1
- 1/1

## Ишмухамета Мырзакаева / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 2

## Ишмухамета Мырзакаева / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 4

## Ишмухамета Мырзакаева / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 5

## Ишмухамета Мырзакаева / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 6

## Ишмухамета Мырзакаева / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 7

## Ишмухамета Мырзакаева / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 8

## Ишмухамета Мырзакаева / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 9

## Ишмухамета Мырзакаева / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 10

## Ишмухамета Мырзакаева / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 11
- 11к1

## Ишмухамета Мырзакаева / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 12

## Ишмухамета Мырзакаева / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 13
- 13/1

## Ишмухамета Мырзакаева / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 14

## Ишмухамета Мырзакаева / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 15

## Ишмухамета Мырзакаева / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 16

## Ишмухамета Мырзакаева / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 18

## Ишмухамета Мырзакаева / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 19

## Ишмухамета Мырзакаева / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 20

## Ишмухамета Мырзакаева / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 21

## Ишмухамета Мырзакаева / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 22

## Ишмухамета Мырзакаева / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 23

## Ишмухамета Мырзакаева / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 24

## Ишмухамета Мырзакаева / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 25
- 25/1

## Ишмухамета Мырзакаева / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 26

## Ишмухамета Мырзакаева / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 27

## Ишмухамета Мырзакаева / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 28

## Ишмухамета Мырзакаева / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 29

## Ишмухамета Мырзакаева / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 30

## Ишмухамета Мырзакаева / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 32

## Ишмухамета Мырзакаева / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 33

## Ишмухамета Мырзакаева / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 34

## Ишмухамета Мырзакаева / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 35
- 35/2

## Ишмухамета Мырзакаева / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 36

## Ишмухамета Мырзакаева / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 37

## Ишмухамета Мырзакаева / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 38

## Ишмухамета Мырзакаева / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 40

## Ишмухамета Мырзакаева / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 41

## Ишмухамета Мырзакаева / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 42

## Ишмухамета Мырзакаева / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 44

## Ишмухамета Мырзакаева / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 48

## Ишмухамета Мырзакаева / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 52/1

## Ишмухамета Мырзакаева / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 54

## Ишмухамета Мырзакаева / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 56

## Ишмухамета Мырзакаева / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 58

## Ишмухамета Мырзакаева / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 60

## Ишмухамета Мырзакаева / base=66

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356

- 66

## Кима Ахмедьянова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 1
- 1а

## Кима Ахмедьянова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 2

## Кима Ахмедьянова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 3

## Кима Ахмедьянова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 4

## Кима Ахмедьянова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 5

## Кима Ахмедьянова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 6

## Кима Ахмедьянова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 7

## Кима Ахмедьянова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 8

## Кима Ахмедьянова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 9

## Кима Ахмедьянова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 10

## Кима Ахмедьянова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 11

## Кима Ахмедьянова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 12

## Кима Ахмедьянова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 13

## Кима Ахмедьянова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 14

## Кима Ахмедьянова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 15

## Кима Ахмедьянова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 16

## Кима Ахмедьянова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 17

## Кима Ахмедьянова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 19

## Кима Ахмедьянова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 20

## Кима Ахмедьянова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 21

## Кима Ахмедьянова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 22

## Кима Ахмедьянова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 23

## Кима Ахмедьянова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 24

## Кима Ахмедьянова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 25

## Кима Ахмедьянова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 26

## Кима Ахмедьянова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 27

## Кима Ахмедьянова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 28

## Кима Ахмедьянова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 29

## Кима Ахмедьянова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 30

## Кима Ахмедьянова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 32

## Кима Ахмедьянова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 34

## Кима Ахмедьянова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 35

## Кима Ахмедьянова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 36

## Кима Ахмедьянова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 37

## Кима Ахмедьянова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 38
- 38/1
- 38/2
- 38/3

## Кима Ахмедьянова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 39

## Кима Ахмедьянова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 40
- 40/1
- 40/3

## Кима Ахмедьянова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 41

## Кима Ахмедьянова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 42

## Кима Ахмедьянова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 43

## Кима Ахмедьянова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 44

## Кима Ахмедьянова / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 46

## Кима Ахмедьянова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 48

## Кима Ахмедьянова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 49

## Кима Ахмедьянова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 50

## Кима Ахмедьянова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 51

## Кима Ахмедьянова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 52

## Кима Ахмедьянова / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 53

## Кима Ахмедьянова / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 54

## Кима Ахмедьянова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 56

## Кима Ахмедьянова / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 57

## Кима Ахмедьянова / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 58

## Кима Ахмедьянова / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 59

## Кима Ахмедьянова / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 60

## Кима Ахмедьянова / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 62

## Кима Ахмедьянова / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 63

## Кима Ахмедьянова / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 65

## Кима Ахмедьянова / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 67

## Кима Ахмедьянова / base=68

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 68

## Кима Ахмедьянова / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 69

## Кима Ахмедьянова / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 70

## Кима Ахмедьянова / base=71

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 71

## Кима Ахмедьянова / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 72
- 72/1

## Кима Ахмедьянова / base=74

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 74

## Кима Ахмедьянова / base=76

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357

- 76

## Ленина / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 422

- 33

## Ленина / base=500

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 422

- 500

## Магнитогорская / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 1

## Магнитогорская / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 3

## Магнитогорская / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 4

## Магнитогорская / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 6

## Магнитогорская / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 7

## Магнитогорская / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 8

## Магнитогорская / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 9

## Магнитогорская / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 10

## Магнитогорская / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 13

## Магнитогорская / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 14

## Магнитогорская / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 15

## Магнитогорская / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 16

## Магнитогорская / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 17

## Магнитогорская / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 18

## Магнитогорская / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 20

## Магнитогорская / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 22

## Магнитогорская / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 24

## Магнитогорская / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 26

## Магнитогорская / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 28

## Магнитогорская / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367

- 30
- 30/1

## Малика Якшимбетова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 2
- 2/1

## Малика Якшимбетова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 4

## Малика Якшимбетова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 6

## Малика Якшимбетова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 8

## Малика Якшимбетова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 10

## Малика Якшимбетова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 12

## Малика Якшимбетова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 13

## Малика Якшимбетова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 14

## Малика Якшимбетова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 15

## Малика Якшимбетова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 17

## Малика Якшимбетова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 19

## Малика Якшимбетова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 20

## Малика Якшимбетова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 21

## Малика Якшимбетова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 22

## Малика Якшимбетова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 23

## Малика Якшимбетова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 24

## Малика Якшимбетова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 26

## Малика Якшимбетова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 27

## Малика Якшимбетова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 28

## Малика Якшимбетова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 30

## Малика Якшимбетова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 34

## Малика Якшимбетова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 40

## Малика Якшимбетова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369

- 41

## Миллята Хакимова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 1

## Миллята Хакимова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 2
- 2/1

## Миллята Хакимова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 3

## Миллята Хакимова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 4

## Миллята Хакимова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 5

## Миллята Хакимова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 6

## Миллята Хакимова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 7

## Миллята Хакимова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 8

## Миллята Хакимова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 9

## Миллята Хакимова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 10

## Миллята Хакимова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 11

## Миллята Хакимова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 12

## Миллята Хакимова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 13

## Миллята Хакимова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 14

## Миллята Хакимова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 15

## Миллята Хакимова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 16

## Миллята Хакимова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 17

## Миллята Хакимова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 18

## Миллята Хакимова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 19

## Миллята Хакимова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 20

## Миллята Хакимова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 21

## Миллята Хакимова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 22

## Миллята Хакимова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 23

## Миллята Хакимова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 25

## Миллята Хакимова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 27

## Миллята Хакимова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 31

## Миллята Хакимова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 35

## Миллята Хакимова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 39

## Миллята Хакимова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 47

## Миллята Хакимова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 49

## Миллята Хакимова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 51

## Миллята Хакимова / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 55

## Миллята Хакимова / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373

- 57

## Мустая Карима / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 1

## Мустая Карима / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 2

## Мустая Карима / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 3

## Мустая Карима / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 4

## Мустая Карима / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 5

## Мустая Карима / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 6

## Мустая Карима / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 7

## Мустая Карима / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 8

## Мустая Карима / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 9

## Мустая Карима / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 10

## Мустая Карима / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 11

## Мустая Карима / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 12

## Мустая Карима / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 13

## Мустая Карима / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 14

## Мустая Карима / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 15

## Мустая Карима / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 16

## Мустая Карима / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 17

## Мустая Карима / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 18

## Мустая Карима / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 19

## Мустая Карима / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 20

## Мустая Карима / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 21

## Мустая Карима / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 22

## Мустая Карима / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 23

## Мустая Карима / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 24

## Мустая Карима / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 25

## Мустая Карима / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 26

## Мустая Карима / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 27

## Мустая Карима / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 28

## Мустая Карима / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 29

## Мустая Карима / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 30

## Мустая Карима / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 31

## Мустая Карима / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 32

## Мустая Карима / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 33

## Мустая Карима / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 34

## Мустая Карима / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 35

## Мустая Карима / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 36

## Мустая Карима / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 37

## Мустая Карима / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 38

## Мустая Карима / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 39

## Мустая Карима / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 40

## Мустая Карима / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 41

## Мустая Карима / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 42

## Мустая Карима / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 43

## Мустая Карима / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 45

## Мустая Карима / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 46

## Мустая Карима / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 48

## Мустая Карима / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 49

## Мустая Карима / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 50

## Мустая Карима / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 51

## Мустая Карима / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 53

## Мустая Карима / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 54

## Мустая Карима / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 55

## Мустая Карима / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 57

## Мустая Карима / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 59

## Мустая Карима / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 60

## Мустая Карима / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 61

## Мустая Карима / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 62

## Мустая Карима / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 63

## Мустая Карима / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 65

## Мустая Карима / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379

- 67
- 67/1

## Рамазана Уметбаева / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 1
- 1а
- 1/2
- 1/3

## Рамазана Уметбаева / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 2

## Рамазана Уметбаева / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 4

## Рамазана Уметбаева / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 5

## Рамазана Уметбаева / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 6

## Рамазана Уметбаева / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 7

## Рамазана Уметбаева / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 8

## Рамазана Уметбаева / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 9

## Рамазана Уметбаева / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 10
- 10к3

## Рамазана Уметбаева / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 11

## Рамазана Уметбаева / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 12

## Рамазана Уметбаева / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 13

## Рамазана Уметбаева / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 14

## Рамазана Уметбаева / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 15

## Рамазана Уметбаева / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 17
- 17/1

## Рамазана Уметбаева / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 18

## Рамазана Уметбаева / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 19
- 19/1

## Рамазана Уметбаева / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 20

## Рамазана Уметбаева / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 21

## Рамазана Уметбаева / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 23/1

## Рамазана Уметбаева / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 24

## Рамазана Уметбаева / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 25
- 25/1

## Рамазана Уметбаева / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 27
- 27/1
- 27/2
- 27/3

## Рамазана Уметбаева / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 28

## Рамазана Уметбаева / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 29
- 29/1

## Рамазана Уметбаева / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 30

## Рамазана Уметбаева / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 31

## Рамазана Уметбаева / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 32

## Рамазана Уметбаева / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386

- 36

## Расуля Кужахметова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 1

## Расуля Кужахметова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 2

## Расуля Кужахметова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 3

## Расуля Кужахметова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 4

## Расуля Кужахметова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 5

## Расуля Кужахметова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 6

## Расуля Кужахметова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 7

## Расуля Кужахметова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 8

## Расуля Кужахметова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 9

## Расуля Кужахметова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 10

## Расуля Кужахметова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 11

## Расуля Кужахметова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 12

## Расуля Кужахметова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 13

## Расуля Кужахметова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 14

## Расуля Кужахметова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 15

## Расуля Кужахметова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 16

## Расуля Кужахметова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 17

## Расуля Кужахметова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 18

## Расуля Кужахметова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 19

## Расуля Кужахметова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 20

## Расуля Кужахметова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 21
- 21/1

## Расуля Кужахметова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 22

## Расуля Кужахметова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 23

## Расуля Кужахметова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 24

## Расуля Кужахметова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 25

## Расуля Кужахметова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 26
- 26А

## Расуля Кужахметова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 27

## Расуля Кужахметова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 28

## Расуля Кужахметова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 29

## Расуля Кужахметова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 30

## Расуля Кужахметова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 31

## Расуля Кужахметова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 32

## Расуля Кужахметова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 33

## Расуля Кужахметова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 35

## Расуля Кужахметова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 36

## Расуля Кужахметова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 37

## Расуля Кужахметова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 38

## Расуля Кужахметова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 39

## Расуля Кужахметова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387

- 40

## Сафи Истамгалина / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 439

- 31

## Сафы Истамгалина / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 17

## Сафы Истамгалина / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 19

## Сафы Истамгалина / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 21

## Сафы Истамгалина / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 23

## Сафы Истамгалина / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 25

## Сафы Истамгалина / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 27

## Сафы Истамгалина / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 29

## Сафы Истамгалина / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 31

## Сафы Истамгалина / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 33

## Сафы Истамгалина / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 35

## Сафы Истамгалина / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 37

## Сафы Истамгалина / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 39

## Сафы Истамгалина / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 40

## Сафы Истамгалина / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 41

## Сафы Истамгалина / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 42

## Сафы Истамгалина / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 43

## Сафы Истамгалина / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 45

## Сафы Истамгалина / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 47

## Сафы Истамгалина / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 48

## Сафы Истамгалина / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 49

## Сафы Истамгалина / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 51

## Сафы Истамгалина / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 52

## Сафы Истамгалина / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 53

## Сафы Истамгалина / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 54

## Сафы Истамгалина / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 55

## Сафы Истамгалина / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 56

## Сафы Истамгалина / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 58

## Сафы Истамгалина / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 395

- 60

## Сосновая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 1
- 1/1

## Сосновая / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 3

## Сосновая / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 15

## Сосновая / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 17

## Сосновая / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 19

## Сосновая / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 21

## Сосновая / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 23

## Сосновая / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 25

## Сосновая / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 27

## Сосновая / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 33

## Сосновая / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 35

## Сосновая / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398

- 37

## Фаттаха Ибрагимова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 1
- 1А

## Фаттаха Ибрагимова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 2

## Фаттаха Ибрагимова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 4

## Фаттаха Ибрагимова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 5

## Фаттаха Ибрагимова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 6

## Фаттаха Ибрагимова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 7

## Фаттаха Ибрагимова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 8

## Фаттаха Ибрагимова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 9

## Фаттаха Ибрагимова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 10

## Фаттаха Ибрагимова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 11

## Фаттаха Ибрагимова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 12

## Фаттаха Ибрагимова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 13

## Фаттаха Ибрагимова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 14

## Фаттаха Ибрагимова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 16

## Фаттаха Ибрагимова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 18

## Фаттаха Ибрагимова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 20

## Фаттаха Ибрагимова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 22

## Фаттаха Ибрагимова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 24

## Фаттаха Ибрагимова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 26

## Фаттаха Ибрагимова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 28

## Фаттаха Ибрагимова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 30

## Фаттаха Ибрагимова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 32

## Фаттаха Ибрагимова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 34

## Фаттаха Ибрагимова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 36

## Фаттаха Ибрагимова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 38

## Фаттаха Ибрагимова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 40

## Фаттаха Ибрагимова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 42

## Фаттаха Ибрагимова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 44

## Фаттаха Ибрагимова / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 46

## Фаттаха Ибрагимова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 48

## Фаттаха Ибрагимова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 50

## Фаттаха Ибрагимова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 51

## Фаттаха Ибрагимова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 52

## Фаттаха Ибрагимова / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 54

## Фаттаха Ибрагимова / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 55

## Фаттаха Ибрагимова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 56

## Фаттаха Ибрагимова / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 58

## Фаттаха Ибрагимова / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 60

## Фаттаха Ибрагимова / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 62

## Фаттаха Ибрагимова / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409

- 64

## Фахиры Гумеровой / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 1

## Фахиры Гумеровой / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 2

## Фахиры Гумеровой / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 3

## Фахиры Гумеровой / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 4

## Фахиры Гумеровой / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 7

## Фахиры Гумеровой / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 8
- 8А

## Фахиры Гумеровой / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 9

## Фахиры Гумеровой / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 10

## Фахиры Гумеровой / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 11

## Фахиры Гумеровой / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 12

## Фахиры Гумеровой / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 13

## Фахиры Гумеровой / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 14

## Фахиры Гумеровой / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 19

## Фахиры Гумеровой / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 21

## Фахиры Гумеровой / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 23

## Фахиры Гумеровой / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 25

## Фахиры Гумеровой / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 27

## Фахиры Гумеровой / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 29

## Фахиры Гумеровой / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 31

## Фахиры Гумеровой / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 33

## Фахиры Гумеровой / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 35
- 35/1

## Фахиры Гумеровой / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 37

## Фахиры Гумеровой / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 38Б

## Фахиры Гумеровой / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 39
- 39/1

## Фахиры Гумеровой / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 40

## Фахиры Гумеровой / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 41

## Фахиры Гумеровой / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 43

## Фахиры Гумеровой / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 47

## Фахиры Гумеровой / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 49

## Фахиры Гумеровой / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 51

## Фахиры Гумеровой / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 53

## Фахиры Гумеровой / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 55

## Фахиры Гумеровой / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 57

## Фахиры Гумеровой / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 59

## Фахиры Гумеровой / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 61

## Фахиры Гумеровой / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 63

## Фахиры Гумеровой / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 65

## Фахиры Гумеровой / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 67

## Фахиры Гумеровой / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 69

## Фахиры Гумеровой / base=71

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 71

## Фахиры Гумеровой / base=73

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410

- 73

## Яныбая Хамматова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 1

## Яныбая Хамматова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 3

## Яныбая Хамматова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 5

## Яныбая Хамматова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 7

## Яныбая Хамматова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 9

## Яныбая Хамматова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 11

## Яныбая Хамматова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 13

## Яныбая Хамматова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 15

## Яныбая Хамматова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 17
- 17к1

## Яныбая Хамматова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 19

## Яныбая Хамматова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 21

## Яныбая Хамматова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 23

## Яныбая Хамматова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 25

## Яныбая Хамматова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 27
- 27А

## Яныбая Хамматова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 31

## Яныбая Хамматова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 33

## Яныбая Хамматова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 35

## Яныбая Хамматова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 37

## Яныбая Хамматова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421

- 47

## 50 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 1/1
- 1/4
- 1/5
- 1/6
- 1/7
- 1/8

## 50 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 2
- 2/5
- 2/7
- 2/9

## 50 лет Победы / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 6

## 50 лет Победы / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 7

## 50 лет Победы / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 10

## 50 лет Победы / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 12

## 50 лет Победы / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 13

## 50 лет Победы / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 16

## 50 лет Победы / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 17

## 50 лет Победы / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 19

## 50 лет Победы / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 20

## 50 лет Победы / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 21

## 50 лет Победы / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 22

## 50 лет Победы / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 23

## 50 лет Победы / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 24

## 50 лет Победы / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 25

## 50 лет Победы / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 26

## 50 лет Победы / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 28

## 50 лет Победы / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 29

## 50 лет Победы / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 31

## 50 лет Победы / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 32

## 50 лет Победы / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 33

## 50 лет Победы / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 34

## 50 лет Победы / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 35

## 50 лет Победы / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 37

## 50 лет Победы / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 41

## 50 лет Победы / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 43

## 50 лет Победы / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 46

## 50 лет Победы / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 49

## 50 лет Победы / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 50

## 50 лет Победы / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 51

## 50 лет Победы / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 53

## 50 лет Победы / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 54

## 50 лет Победы / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 56

## 50 лет Победы / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 57

## 50 лет Победы / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 58

## 50 лет Победы / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 62

## 50 лет Победы / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 64

## 50 лет Победы / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 65

## 50 лет Победы / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 67

## 50 лет Победы / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 70
- 70/1

## 50 лет Победы / base=71

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 71

## 50 лет Победы / base=73

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 73

## 50 лет Победы / base=74

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 74

## 50 лет Победы / base=75

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 75

## 50 лет Победы / base=76

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 76

## 50 лет Победы / base=78

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 78

## 50 лет Победы / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 79

## 50 лет Победы / base=80

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 80

## 50 лет Победы / base=82

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 82

## 50 лет Победы / base=84

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 84

## 50 лет Победы / base=86

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 86

## 50 лет Победы / base=87

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 87

## 50 лет Победы / base=89

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334

- 89

## 65 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 1
- 1/2

## 65 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 2
- 2/1

## 65 лет Победы / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 5

## 65 лет Победы / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 6

## 65 лет Победы / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 7

## 65 лет Победы / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 8

## 65 лет Победы / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 10

## 65 лет Победы / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 12

## 65 лет Победы / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 13

## 65 лет Победы / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 14

## 65 лет Победы / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 15

## 65 лет Победы / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 16

## 65 лет Победы / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 17

## 65 лет Победы / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 18

## 65 лет Победы / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 19
- 19/1

## 65 лет Победы / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 21

## 65 лет Победы / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 25

## 65 лет Победы / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 26

## 65 лет Победы / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 34

## 65 лет Победы / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 39

## 65 лет Победы / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 40

## 65 лет Победы / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 41

## 65 лет Победы / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 44
- 44/1

## 65 лет Победы / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 45

## 65 лет Победы / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 46

## 65 лет Победы / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 47

## 65 лет Победы / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 48

## 65 лет Победы / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 50

## 65 лет Победы / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 51

## 65 лет Победы / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 53

## 65 лет Победы / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 55

## 65 лет Победы / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 57

## 65 лет Победы / base=66

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 66

## 65 лет Победы / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 69

## 65 лет Победы / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 70
- 70/1

## 65 лет Победы / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 72

## 65 лет Победы / base=74

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 74

## 65 лет Победы / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 79

## 65 лет Победы / base=81

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 81

## 65 лет Победы / base=83

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 83

## 65 лет Победы / base=84

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 84

## 65 лет Победы / base=85

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336

- 85

## Ахмета Лутфуллина / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 6

## Ахмета Лутфуллина / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 8

## Ахмета Лутфуллина / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 13
- 13/1

## Ахмета Лутфуллина / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 15

## Ахмета Лутфуллина / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 16

## Ахмета Лутфуллина / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 18

## Ахмета Лутфуллина / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 19

## Ахмета Лутфуллина / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 20

## Ахмета Лутфуллина / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 21

## Ахмета Лутфуллина / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 22

## Ахмета Лутфуллина / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 23/5

## Ахмета Лутфуллина / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 24

## Ахмета Лутфуллина / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 25

## Ахмета Лутфуллина / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 26

## Ахмета Лутфуллина / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 27

## Ахмета Лутфуллина / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 28

## Ахмета Лутфуллина / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 29

## Ахмета Лутфуллина / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 30
- 30/1

## Ахмета Лутфуллина / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 31

## Ахмета Лутфуллина / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 32

## Ахмета Лутфуллина / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 35

## Ахмета Лутфуллина / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 36

## Ахмета Лутфуллина / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 37

## Ахмета Лутфуллина / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 40

## Ахмета Лутфуллина / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 42

## Ахмета Лутфуллина / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 43

## Ахмета Лутфуллина / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 44

## Ахмета Лутфуллина / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 45

## Ахмета Лутфуллина / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 46

## Ахмета Лутфуллина / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 48

## Ахмета Лутфуллина / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341

- 49

## Бииш Батыра / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 1
- 1/1

## Бииш Батыра / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 2

## Бииш Батыра / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 4

## Бииш Батыра / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 5

## Бииш Батыра / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 6

## Бииш Батыра / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 7

## Бииш Батыра / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 8

## Бииш Батыра / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 9

## Бииш Батыра / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 10

## Бииш Батыра / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 11

## Бииш Батыра / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 12

## Бииш Батыра / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 13

## Бииш Батыра / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 14
- 14/1
- 14/2
- 14/3

## Бииш Батыра / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 15
- 15/1
- 15/3

## Бииш Батыра / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 16
- 16а
- 16/1
- 16/2

## Бииш Батыра / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 17/2
- 17/3

## Бииш Батыра / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 18

## Бииш Батыра / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 19

## Бииш Батыра / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 20

## Бииш Батыра / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 21

## Бииш Батыра / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 22

## Бииш Батыра / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 23

## Бииш Батыра / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 25

## Бииш Батыра / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 26

## Бииш Батыра / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 27

## Бииш Батыра / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 28

## Бииш Батыра / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 29

## Бииш Батыра / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 30

## Бииш Батыра / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 31

## Бииш Батыра / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 32

## Бииш Батыра / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 33

## Бииш Батыра / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 34

## Бииш Батыра / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 35

## Бииш Батыра / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 36

## Бииш Батыра / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 37

## Бииш Батыра / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 38

## Бииш Батыра / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 39

## Бииш Батыра / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 40

## Бииш Батыра / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 41

## Бииш Батыра / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 42

## Бииш Батыра / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 44

## Бииш Батыра / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 47

## Бииш Батыра / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 48

## Бииш Батыра / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 50

## Бииш Батыра / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342

- 53

## Иншара Султанбаева / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 353

- 50

## Иншара Султанбаева / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 353

- 51

## Иншара Султанбаева / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 353

- 56

## Иншара Султанбаева / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 353

- 57

## Иншара Султанбаева / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 353

- 59

## Ишмурзы Хидиятова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 1

## Ишмурзы Хидиятова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 2
- 2А

## Ишмурзы Хидиятова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 3

## Ишмурзы Хидиятова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 4

## Ишмурзы Хидиятова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 5
- 5/1
- 5/2
- 5/3

## Ишмурзы Хидиятова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 6

## Ишмурзы Хидиятова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 7
- 7а
- 7/2

## Ишмурзы Хидиятова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 9
- 9/1
- 9/3

## Ишмурзы Хидиятова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 10
- 10/1

## Ишмурзы Хидиятова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 11

## Ишмурзы Хидиятова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 13

## Ишмурзы Хидиятова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 14

## Ишмурзы Хидиятова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 15
- 15/1

## Ишмурзы Хидиятова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 16

## Ишмурзы Хидиятова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 17

## Ишмурзы Хидиятова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 18
- 18/1

## Ишмурзы Хидиятова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 19
- 19/1
- 19/2

## Ишмурзы Хидиятова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 20

## Ишмурзы Хидиятова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 21

## Ишмурзы Хидиятова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 22

## Ишмурзы Хидиятова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 23
- 23/1

## Ишмурзы Хидиятова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 25/1

## Ишмурзы Хидиятова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 26

## Ишмурзы Хидиятова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 27

## Ишмурзы Хидиятова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 28

## Ишмурзы Хидиятова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 29

## Ишмурзы Хидиятова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 31

## Ишмурзы Хидиятова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 32

## Ишмурзы Хидиятова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 33

## Ишмурзы Хидиятова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 34

## Ишмурзы Хидиятова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 35/1

## Ишмурзы Хидиятова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 36

## Ишмурзы Хидиятова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 38

## Ишмурзы Хидиятова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 40

## Ишмурзы Хидиятова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 41

## Ишмурзы Хидиятова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 42

## Ишмурзы Хидиятова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 43

## Ишмурзы Хидиятова / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 45

## Ишмурзы Хидиятова / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 46

## Ишмурзы Хидиятова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 47

## Ишмурзы Хидиятова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 48

## Ишмурзы Хидиятова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 49

## Ишмурзы Хидиятова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 50

## Ишмурзы Хидиятова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 51

## Ишмурзы Хидиятова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 52

## Ишмурзы Хидиятова / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 53

## Ишмурзы Хидиятова / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 54

## Ишмурзы Хидиятова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 56

## Ишмурзы Хидиятова / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 58

## Ишмурзы Хидиятова / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 59

## Ишмурзы Хидиятова / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355

- 61

## Курьятмас / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 1
- 1/1

## Курьятмас / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 2
- 2/1

## Курьятмас / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 4

## Курьятмас / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 5

## Курьятмас / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 7

## Курьятмас / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 9

## Курьятмас / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 10

## Курьятмас / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 11

## Курьятмас / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 12

## Курьятмас / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 13

## Курьятмас / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 14

## Курьятмас / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 15

## Курьятмас / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 16/1

## Курьятмас / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 17

## Курьятмас / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 18

## Курьятмас / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 19

## Курьятмас / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 21

## Курьятмас / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 22

## Курьятмас / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 23

## Курьятмас / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 24

## Курьятмас / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 25

## Курьятмас / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 26

## Курьятмас / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 31

## Курьятмас / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 32

## Курьятмас / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 33

## Курьятмас / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 34
- 34/1

## Курьятмас / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 35

## Курьятмас / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 37

## Курьятмас / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 38

## Курьятмас / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 39

## Курьятмас / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 41

## Курьятмас / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 42/1

## Курьятмас / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 43

## Курьятмас / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 45

## Курьятмас / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 49

## Курьятмас / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363

- 51

## Луговая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 1

## Луговая / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 2
- 2а
- 2/1
- 2/2
- 2/3

## Луговая / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 3
- 3/1

## Луговая / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 4
- 4/2

## Луговая / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 5

## Луговая / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 6

## Луговая / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 7

## Луговая / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 10

## Луговая / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 12

## Луговая / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 14
- 14/1

## Луговая / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 18

## Луговая / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 20

## Луговая / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 21

## Луговая / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 25
- 25/1

## Луговая / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 26

## Луговая / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 27

## Луговая / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 29

## Луговая / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 31

## Луговая / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 34

## Луговая / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 35

## Луговая / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 41

## Луговая / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 46

## Луговая / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 49
- 49а

## Луговая / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 50

## Луговая / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 52

## Луговая / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 53

## Луговая / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 54/2

## Луговая / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 55

## Луговая / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 57

## Луговая / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 59

## Луговая / base=66

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 66

## Луговая / base=68

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366

- 68

## Минислама Мирсаяпова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 1
- 1/2
- 1/3
- 1/5

## Минислама Мирсаяпова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 2/3
- 2/7

## Минислама Мирсаяпова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 5

## Минислама Мирсаяпова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 6

## Минислама Мирсаяпова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 8

## Минислама Мирсаяпова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 11

## Минислама Мирсаяпова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 13

## Минислама Мирсаяпова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 14

## Минислама Мирсаяпова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 15

## Минислама Мирсаяпова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 17

## Минислама Мирсаяпова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 18

## Минислама Мирсаяпова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 20

## Минислама Мирсаяпова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 22

## Минислама Мирсаяпова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 24

## Минислама Мирсаяпова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 25

## Минислама Мирсаяпова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 28

## Минислама Мирсаяпова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 29

## Минислама Мирсаяпова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 30

## Минислама Мирсаяпова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 31
- 31а

## Минислама Мирсаяпова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 33

## Минислама Мирсаяпова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 34

## Минислама Мирсаяпова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 42

## Минислама Мирсаяпова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 43

## Минислама Мирсаяпова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 47

## Минислама Мирсаяпова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 48

## Минислама Мирсаяпова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 50

## Минислама Мирсаяпова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 52

## Минислама Мирсаяпова / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 54

## Минислама Мирсаяпова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 56

## Минислама Мирсаяпова / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 58

## Минислама Мирсаяпова / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 59

## Минислама Мирсаяпова / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 60

## Минислама Мирсаяпова / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 61

## Минислама Мирсаяпова / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 62

## Минислама Мирсаяпова / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 63

## Минислама Мирсаяпова / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 64

## Минислама Мирсаяпова / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 65

## Минислама Мирсаяпова / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 69

## Минислама Мирсаяпова / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 70

## Минислама Мирсаяпова / base=71

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 71

## Минислама Мирсаяпова / base=73

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 73

## Минислама Мирсаяпова / base=74

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 74

## Минислама Мирсаяпова / base=75

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 75

## Минислама Мирсаяпова / base=77

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 77

## Минислама Мирсаяпова / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 79

## Минислама Мирсаяпова / base=80

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 80

## Минислама Мирсаяпова / base=82

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 82

## Минислама Мирсаяпова / base=83

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 83

## Минислама Мирсаяпова / base=84

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 84

## Минислама Мирсаяпова / base=85

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 85

## Минислама Мирсаяпова / base=87

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 87

## Минислама Мирсаяпова / base=88

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 88

## Минислама Мирсаяпова / base=89

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 89

## Минислама Мирсаяпова / base=94

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 94

## Минислама Мирсаяпова / base=95

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 95

## Минислама Мирсаяпова / base=507

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374

- 507к4

## Мурзахана Шамсутдинова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 34

## Мурзахана Шамсутдинова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 48

## Мурзахана Шамсутдинова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 50

## Мурзахана Шамсутдинова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 56

## Мурзахана Шамсутдинова / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 58

## Мурзахана Шамсутдинова / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 61

## Мурзахана Шамсутдинова / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 65

## Мурзахана Шамсутдинова / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 378

- 67

## Пятая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 1
- 1/3
- 1/7
- 1/9

## Пятая / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 3

## Пятая / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 4

## Пятая / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 5

## Пятая / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 6

## Пятая / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 7

## Пятая / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 9

## Пятая / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 10

## Пятая / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 14

## Пятая / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 15

## Пятая / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 16

## Пятая / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 17

## Пятая / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 19

## Пятая / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 21

## Пятая / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 22

## Пятая / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 23

## Пятая / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 24

## Пятая / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 26

## Пятая / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 29

## Пятая / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 34

## Пятая / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 35

## Пятая / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 36

## Пятая / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 37

## Пятая / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 38

## Пятая / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 39

## Пятая / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 43

## Пятая / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 45

## Пятая / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 47

## Пятая / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384

- 51

## Раиса Усманова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 1/1
- 1/10
- 1/2
- 1/3
- 1/6
- 1/7
- 1/9

## Раиса Усманова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 2
- 2/1
- 2/10
- 2/6

## Раиса Усманова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 5

## Раиса Усманова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 6

## Раиса Усманова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 8

## Раиса Усманова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 9

## Раиса Усманова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 10

## Раиса Усманова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 12

## Раиса Усманова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 13

## Раиса Усманова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 14

## Раиса Усманова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 15/2

## Раиса Усманова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 16
- 16/1
- 16/3

## Раиса Усманова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 17
- 17/1
- 17/2

## Раиса Усманова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 18
- 18/2

## Раиса Усманова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 19

## Раиса Усманова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 20

## Раиса Усманова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 22

## Раиса Усманова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 23

## Раиса Усманова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 24

## Раиса Усманова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 25

## Раиса Усманова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 26

## Раиса Усманова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 27

## Раиса Усманова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 28

## Раиса Усманова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 29

## Раиса Усманова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 30

## Раиса Усманова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 31

## Раиса Усманова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 32

## Раиса Усманова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 37

## Раиса Усманова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 39

## Раиса Усманова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 40

## Раиса Усманова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 41

## Раиса Усманова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 42

## Раиса Усманова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 43

## Раиса Усманова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 44

## Раиса Усманова / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 45

## Раиса Усманова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 47

## Раиса Усманова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 49

## Раиса Усманова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385

- 52

## Рафика Сальманова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 1/3

## Рафика Сальманова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 3

## Рафика Сальманова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 5

## Рафика Сальманова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 7

## Рафика Сальманова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 8

## Рафика Сальманова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 9

## Рафика Сальманова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 11

## Рафика Сальманова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 12

## Рафика Сальманова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 13

## Рафика Сальманова / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 14

## Рафика Сальманова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 17

## Рафика Сальманова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 18

## Рафика Сальманова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 19

## Рафика Сальманова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 22

## Рафика Сальманова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 23

## Рафика Сальманова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 24

## Рафика Сальманова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 26

## Рафика Сальманова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 27

## Рафика Сальманова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 29

## Рафика Сальманова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 30

## Рафика Сальманова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 31

## Рафика Сальманова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 32

## Рафика Сальманова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 33

## Рафика Сальманова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 36

## Рафика Сальманова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 37

## Рафика Сальманова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 38

## Рафика Сальманова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 39

## Рафика Сальманова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 41

## Рафика Сальманова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 42

## Рафика Сальманова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 43

## Рафика Сальманова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 44

## Рафика Сальманова / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 45

## Рафика Сальманова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 47

## Рафика Сальманова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 48

## Рафика Сальманова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 49

## Рафика Сальманова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 50

## Рафика Сальманова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 51

## Рафика Сальманова / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 52

## Рафика Сальманова / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 53

## Рафика Сальманова / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 54

## Рафика Сальманова / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 55

## Рафика Сальманова / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 56

## Рафика Сальманова / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 59

## Рафика Сальманова / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 61

## Рафика Сальманова / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 62

## Рафика Сальманова / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 63

## Рафика Сальманова / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 64

## Рафика Сальманова / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 65

## Рафика Сальманова / base=66

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 66

## Рафика Сальманова / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 69

## Рафика Сальманова / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 70

## Рафика Сальманова / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 72

## Рафика Сальманова / base=75

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 75

## Рафика Сальманова / base=76

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 76

## Рафика Сальманова / base=77

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 77

## Рафика Сальманова / base=80

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 80

## Рафика Сальманова / base=81

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 81/1

## Рафика Сальманова / base=83

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 83

## Рафика Сальманова / base=84

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 84

## Рафика Сальманова / base=86

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 86

## Рафика Сальманова / base=87

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 87

## Рафика Сальманова / base=90

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389

- 90

## Садовая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 1
- 1а
- 1/1

## Садовая / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 2

## Садовая / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 3

## Садовая / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 6

## Садовая / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 7/1

## Садовая / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 8

## Садовая / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 9

## Садовая / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 10

## Садовая / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 11

## Садовая / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 12

## Садовая / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 13

## Садовая / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 14
- 14/1

## Садовая / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 15

## Садовая / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 16
- 16/1

## Садовая / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 17

## Садовая / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 19
- 19/1
- 19/2
- 19/4

## Садовая / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 20

## Садовая / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 21
- 21/2

## Садовая / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 22

## Садовая / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 23

## Садовая / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 24

## Садовая / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 25

## Садовая / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 26

## Садовая / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 27

## Садовая / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 28

## Садовая / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 29

## Садовая / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 30

## Садовая / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 31

## Садовая / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 32

## Садовая / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 33

## Садовая / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 34

## Садовая / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 35

## Садовая / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 36

## Садовая / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 37

## Садовая / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 40

## Садовая / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 42

## Садовая / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 43

## Садовая / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 45

## Садовая / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 46

## Садовая / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 47

## Садовая / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 48

## Садовая / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 49

## Садовая / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 52

## Садовая / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391

- 53

## Салавата Кадырова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 392

- 17

## Салавата Кадырова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 392

- 38

## Сарии Миржановой / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 1
- 1а
- 1б
- 1/2

## Сарии Миржановой / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 2
- 2а
- 2/1

## Сарии Миржановой / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 3/1

## Сарии Миржановой / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 5

## Сарии Миржановой / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 6

## Сарии Миржановой / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 7

## Сарии Миржановой / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 9

## Сарии Миржановой / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 11

## Сарии Миржановой / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 12

## Сарии Миржановой / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 13

## Сарии Миржановой / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 14

## Сарии Миржановой / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 15/1

## Сарии Миржановой / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 16
- 16/1
- 16/2
- 16/3

## Сарии Миржановой / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 17
- 17/2
- 17/3

## Сарии Миржановой / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 18/1
- 18/2

## Сарии Миржановой / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 19

## Сарии Миржановой / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 20

## Сарии Миржановой / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 21

## Сарии Миржановой / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 22

## Сарии Миржановой / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 23

## Сарии Миржановой / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 24

## Сарии Миржановой / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 25

## Сарии Миржановой / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 26

## Сарии Миржановой / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 27

## Сарии Миржановой / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 28

## Сарии Миржановой / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 29

## Сарии Миржановой / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 30

## Сарии Миржановой / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 31

## Сарии Миржановой / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 32

## Сарии Миржановой / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 33

## Сарии Миржановой / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 34

## Сарии Миржановой / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 36

## Сарии Миржановой / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 38

## Сарии Миржановой / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 39

## Сарии Миржановой / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 40

## Сарии Миржановой / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 41

## Сарии Миржановой / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 44

## Сарии Миржановой / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 45

## Сарии Миржановой / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 46

## Сарии Миржановой / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 47

## Сарии Миржановой / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 48

## Сарии Миржановой / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 50
- 50/1

## Сарии Миржановой / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 51

## Сарии Миржановой / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394

- 52

## Солнечная / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 1

## Солнечная / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 2

## Солнечная / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 3

## Солнечная / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 5

## Солнечная / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 7/1

## Солнечная / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 8

## Солнечная / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 9

## Солнечная / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 10

## Солнечная / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 16

## Солнечная / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 17/1

## Солнечная / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 18

## Солнечная / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 19

## Солнечная / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 20

## Солнечная / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 21

## Солнечная / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 25

## Солнечная / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 26

## Солнечная / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 28

## Солнечная / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 29

## Солнечная / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 31

## Солнечная / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 32

## Солнечная / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 33

## Солнечная / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 35

## Солнечная / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 38

## Солнечная / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 39

## Солнечная / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 40

## Солнечная / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 41

## Солнечная / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 49

## Солнечная / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 50
- 50/1

## Солнечная / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 53

## Солнечная / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 57

## Солнечная / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 59

## Солнечная / base=73

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 73

## Солнечная / base=77

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 77

## Солнечная / base=78

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 78

## Солнечная / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397

- 79

## Тамьян / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 1/1

## Тамьян / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 2/1
- 2/2

## Тамьян / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 3

## Тамьян / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 4

## Тамьян / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 6

## Тамьян / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 7

## Тамьян / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 9

## Тамьян / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 10

## Тамьян / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 13

## Тамьян / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 14

## Тамьян / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 15

## Тамьян / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 16/1
- 16/2

## Тамьян / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 17
- 17/1

## Тамьян / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 18
- 18/1
- 18/2
- 18/3

## Тамьян / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 19

## Тамьян / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 20
- 20/1

## Тамьян / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 21

## Тамьян / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 22

## Тамьян / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 23

## Тамьян / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 25

## Тамьян / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 27

## Тамьян / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 30

## Тамьян / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 31

## Тамьян / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 33

## Тамьян / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 34

## Тамьян / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 35

## Тамьян / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 36

## Тамьян / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 37

## Тамьян / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 38

## Тамьян / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 40

## Тамьян / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 41

## Тамьян / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 42

## Тамьян / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 43

## Тамьян / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 46

## Тамьян / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 53

## Тамьян / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401

- 54

## Тунгаур / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 1
- 1/1
- 1/2
- 1/3

## Тунгаур / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 2/1
- 2/11
- 2/3
- 2/4
- 2/5
- 2/7

## Тунгаур / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 3

## Тунгаур / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 5

## Тунгаур / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 6

## Тунгаур / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 7

## Тунгаур / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 8

## Тунгаур / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 9

## Тунгаур / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 10

## Тунгаур / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 11

## Тунгаур / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 12

## Тунгаур / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 13

## Тунгаур / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 14
- 14/1

## Тунгаур / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 15
- 15/1
- 15/2
- 15/3

## Тунгаур / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 16/1
- 16/3

## Тунгаур / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 17
- 17/1
- 17/2

## Тунгаур / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 18/1
- 18/2

## Тунгаур / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 19

## Тунгаур / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 21

## Тунгаур / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 22

## Тунгаур / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 23
- 23/1

## Тунгаур / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 25

## Тунгаур / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 26

## Тунгаур / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 27

## Тунгаур / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 28

## Тунгаур / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 30

## Тунгаур / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 31

## Тунгаур / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 32

## Тунгаур / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 33

## Тунгаур / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 34

## Тунгаур / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 35
- 35/1

## Тунгаур / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 38

## Тунгаур / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 40

## Тунгаур / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 41

## Тунгаур / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 42

## Тунгаур / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 43

## Тунгаур / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 44

## Тунгаур / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 46

## Тунгаур / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 52

## Тунгаур / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403

- 53

## Файзи Гаскарова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 1
- 1А
- 1/1
- 1/2

## Файзи Гаскарова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 2

## Файзи Гаскарова / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 3

## Файзи Гаскарова / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 4

## Файзи Гаскарова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 5

## Файзи Гаскарова / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 6

## Файзи Гаскарова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 7

## Файзи Гаскарова / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 8

## Файзи Гаскарова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 9

## Файзи Гаскарова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 10

## Файзи Гаскарова / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 11

## Файзи Гаскарова / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 12

## Файзи Гаскарова / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 13

## Файзи Гаскарова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 15
- 15/1

## Файзи Гаскарова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 16

## Файзи Гаскарова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 17/1

## Файзи Гаскарова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 18
- 18/1

## Файзи Гаскарова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 19
- 19/2

## Файзи Гаскарова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 20
- 20/3

## Файзи Гаскарова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 21
- 21/1

## Файзи Гаскарова / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 22

## Файзи Гаскарова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 23

## Файзи Гаскарова / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 24

## Файзи Гаскарова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 25

## Файзи Гаскарова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 26

## Файзи Гаскарова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 27

## Файзи Гаскарова / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 28

## Файзи Гаскарова / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 29

## Файзи Гаскарова / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 30

## Файзи Гаскарова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 31

## Файзи Гаскарова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 32

## Файзи Гаскарова / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 33

## Файзи Гаскарова / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 34

## Файзи Гаскарова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 35

## Файзи Гаскарова / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 36

## Файзи Гаскарова / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 37

## Файзи Гаскарова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 38

## Файзи Гаскарова / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 39

## Файзи Гаскарова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 40

## Файзи Гаскарова / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 41

## Файзи Гаскарова / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 42

## Файзи Гаскарова / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 43

## Файзи Гаскарова / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 44

## Файзи Гаскарова / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 45

## Файзи Гаскарова / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 46

## Файзи Гаскарова / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 47

## Файзи Гаскарова / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 48

## Файзи Гаскарова / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 49

## Файзи Гаскарова / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 50

## Файзи Гаскарова / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 51

## Файзи Гаскарова / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 53

## Файзи Гаскарова / base=55

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 55

## Файзи Гаскарова / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407

- 57
- 57/1
- 57/4

## Хадии Давлетшиной / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 1

## Хадии Давлетшиной / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 3

## Хадии Давлетшиной / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 6

## Хадии Давлетшиной / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 7

## Хадии Давлетшиной / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 8

## Хадии Давлетшиной / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 9

## Хадии Давлетшиной / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 10

## Хадии Давлетшиной / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 11

## Хадии Давлетшиной / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 12

## Хадии Давлетшиной / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 13

## Хадии Давлетшиной / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 14

## Хадии Давлетшиной / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 15

## Хадии Давлетшиной / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 17

## Хадии Давлетшиной / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 18

## Хадии Давлетшиной / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 19

## Хадии Давлетшиной / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 20

## Хадии Давлетшиной / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 21

## Хадии Давлетшиной / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 22

## Хадии Давлетшиной / base=24

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 24

## Хадии Давлетшиной / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 25

## Хадии Давлетшиной / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 26

## Хадии Давлетшиной / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 27
- 27/2

## Хадии Давлетшиной / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 28

## Хадии Давлетшиной / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 29

## Хадии Давлетшиной / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 30

## Хадии Давлетшиной / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 31

## Хадии Давлетшиной / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 33

## Хадии Давлетшиной / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 34

## Хадии Давлетшиной / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 35

## Хадии Давлетшиной / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 36

## Хадии Давлетшиной / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 37

## Хадии Давлетшиной / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 38

## Хадии Давлетшиной / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 40

## Хадии Давлетшиной / base=41

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 41

## Хадии Давлетшиной / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 42

## Хадии Давлетшиной / base=43

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 43

## Хадии Давлетшиной / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 44

## Хадии Давлетшиной / base=45

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 45

## Хадии Давлетшиной / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 46
- 46/1

## Хадии Давлетшиной / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 47

## Хадии Давлетшиной / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 48

## Хадии Давлетшиной / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 49

## Хадии Давлетшиной / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 50

## Хадии Давлетшиной / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 51

## Хадии Давлетшиной / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 52

## Хадии Давлетшиной / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 53

## Хадии Давлетшиной / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 54

## Хадии Давлетшиной / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 56

## Хадии Давлетшиной / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 57

## Хадии Давлетшиной / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 59

## Хадии Давлетшиной / base=61

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 61

## Хадии Давлетшиной / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 62

## Хадии Давлетшиной / base=63

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 63

## Хадии Давлетшиной / base=64

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 64

## Хадии Давлетшиной / base=65

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 65

## Хадии Давлетшиной / base=68

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 68

## Хадии Давлетшиной / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 72

## Хадии Давлетшиной / base=75

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 75

## Хадии Давлетшиной / base=77

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 77

## Хадии Давлетшиной / base=78

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 78

## Хадии Давлетшиной / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 79

## Хадии Давлетшиной / base=83

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 83

## Хадии Давлетшиной / base=86

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 86

## Хадии Давлетшиной / base=87

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 87

## Хадии Давлетшиной / base=90

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411

- 90

## Целинная / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 1а
- 1/4
- 1/6
- 1/7
- 1/8
- 1/9

## Целинная / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 2
- 2/4
- 2/5
- 2/7
- 2/8

## Целинная / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 4

## Целинная / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 5

## Целинная / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 7

## Целинная / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 8

## Целинная / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 11

## Целинная / base=12

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 12

## Целинная / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 14

## Целинная / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 15

## Целинная / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 17

## Целинная / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 20/1

## Целинная / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 21
- 21А

## Целинная / base=22

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 22

## Целинная / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 27

## Целинная / base=28

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 28

## Целинная / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 29

## Целинная / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 30

## Целинная / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 31

## Целинная / base=33

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 33

## Целинная / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 34

## Целинная / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 35

## Целинная / base=36

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 36

## Целинная / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 38

## Целинная / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 42

## Целинная / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 44

## Целинная / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 46

## Целинная / base=47

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 47

## Целинная / base=48

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 48

## Целинная / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 49

## Целинная / base=53

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 53

## Целинная / base=56

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 56

## Целинная / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 57

## Целинная / base=58

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 58

## Целинная / base=59

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 59

## Целинная / base=60

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 60

## Целинная / base=62

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 62

## Целинная / base=66

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 66

## Целинная / base=68

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 68

## Целинная / base=69

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 69

## Целинная / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 70

## Целинная / base=71

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 71

## Целинная / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 72

## Целинная / base=73

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 73

## Целинная / base=74

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 74

## Целинная / base=76

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412

- 76

## Мусы Гареева / base=1

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 1

## Мусы Гареева / base=2

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 2

## Мусы Гареева / base=3

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 3

## Мусы Гареева / base=4

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 4

## Мусы Гареева / base=5

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 5

## Мусы Гареева / base=6

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 6

## Мусы Гареева / base=7

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 7

## Мусы Гареева / base=8

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 8

## Мусы Гареева / base=9

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 9

## Мусы Гареева / base=10

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 10

## Мусы Гареева / base=11

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 11

## Мусы Гареева / base=12

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 12

## Мусы Гареева / base=13

- Town: Аскарово (ID: 4)
- District: Даутово (ID: 24)
- Street ID: 380

- 13

## Ак Кайын / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 2

## Ак Кайын / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 3

## Ак Кайын / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 4

## Ак Кайын / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 5

## Ак Кайын / base=6

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 6

## Ак Кайын / base=8

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 339

- 8

## Ахмет Заки Валиди / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 1

## Ахмет Заки Валиди / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 2

## Ахмет Заки Валиди / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 3

## Ахмет Заки Валиди / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 4

## Ахмет Заки Валиди / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 5

## Ахмет Заки Валиди / base=6

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 6

## Ахмет Заки Валиди / base=7

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 7

## Ахмет Заки Валиди / base=9

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 9

## Ахмет Заки Валиди / base=10

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 10

## Ахмет Заки Валиди / base=11

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 11

## Ахмет Заки Валиди / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 12

## Ахмет Заки Валиди / base=13

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 13

## Ахмет Заки Валиди / base=14

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 14

## Ахмет Заки Валиди / base=15

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 15

## Ахмет Заки Валиди / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 16

## Ахмет Заки Валиди / base=17

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 17

## Ахмет Заки Валиди / base=19

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 19
- 19/3

## Ахмет Заки Валиди / base=21

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 21

## Ахмет Заки Валиди / base=22

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 22

## Ахмет Заки Валиди / base=23

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 23

## Ахмет Заки Валиди / base=24

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 24

## Ахмет Заки Валиди / base=25

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 25

## Ахмет Заки Валиди / base=26

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 26

## Ахмет Заки Валиди / base=27

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 27

## Ахмет Заки Валиди / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 28

## Ахмет Заки Валиди / base=29

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 29

## Ахмет Заки Валиди / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 30

## Ахмет Заки Валиди / base=31

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 31

## Ахмет Заки Валиди / base=32

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 32

## Ахмет Заки Валиди / base=33

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 33

## Ахмет Заки Валиди / base=35

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340

- 35

## Ленина / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 423

- 12

## Урал Батыра / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 1

## Урал Батыра / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 2
- 2/1

## Урал Батыра / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 3

## Урал Батыра / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 4

## Урал Батыра / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 5

## Урал Батыра / base=6

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 6

## Урал Батыра / base=7

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 7

## Урал Батыра / base=8

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 8

## Урал Батыра / base=9

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 9

## Урал Батыра / base=10

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 10

## Урал Батыра / base=11

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 11

## Урал Батыра / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 12

## Урал Батыра / base=13

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 13

## Урал Батыра / base=14

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 14

## Урал Батыра / base=15

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 15

## Урал Батыра / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 16

## Урал Батыра / base=17

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 17

## Урал Батыра / base=18

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 18

## Урал Батыра / base=19

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 19

## Урал Батыра / base=20

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 20/1

## Урал Батыра / base=21

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 21
- 21к4
- 21к5
- 21/1
- 21/2

## Урал Батыра / base=22

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 22

## Урал Батыра / base=23

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 23
- 23к1

## Урал Батыра / base=24

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 24

## Урал Батыра / base=25

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 25

## Урал Батыра / base=26

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 26

## Урал Батыра / base=27

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 27

## Урал Батыра / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 28
- 28к1

## Урал Батыра / base=29

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 29

## Урал Батыра / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 30
- 30к1

## Урал Батыра / base=31

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 31

## Урал Батыра / base=32

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 32

## Урал Батыра / base=33

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 33

## Урал Батыра / base=34

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 34

## Урал Батыра / base=35

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 35

## Урал Батыра / base=36

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 36

## Урал Батыра / base=38

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 38

## Урал Батыра / base=39

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 39
- 39А

## Урал Батыра / base=40

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 40

## Урал Батыра / base=41

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 41

## Урал Батыра / base=42

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 42

## Урал Батыра / base=44

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 44

## Урал Батыра / base=46

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 46

## Урал Батыра / base=48

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 48

## Урал Батыра / base=50

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404

- 50

## Уральская / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 405

- 16

## Уральская / base=20

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 405

- 20

## Уральская / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 405

- 30

## Уральская / base=32

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 405

- 32

## Уральская / base=39

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 405

- 39

## Файзрахмана Хисматуллина / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 1

## Файзрахмана Хисматуллина / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 2

## Файзрахмана Хисматуллина / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 3

## Файзрахмана Хисматуллина / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 4

## Файзрахмана Хисматуллина / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 5

## Файзрахмана Хисматуллина / base=7

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 7

## Файзрахмана Хисматуллина / base=8

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 8

## Файзрахмана Хисматуллина / base=9

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 9

## Файзрахмана Хисматуллина / base=10

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 10

## Файзрахмана Хисматуллина / base=11

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 11

## Файзрахмана Хисматуллина / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 12

## Файзрахмана Хисматуллина / base=13

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 13

## Файзрахмана Хисматуллина / base=14

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 14

## Файзрахмана Хисматуллина / base=15

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 15

## Файзрахмана Хисматуллина / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 16

## Файзрахмана Хисматуллина / base=17

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 17

## Файзрахмана Хисматуллина / base=18

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 18

## Файзрахмана Хисматуллина / base=19

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 19

## Файзрахмана Хисматуллина / base=20

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 20

## Файзрахмана Хисматуллина / base=21

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 21

## Файзрахмана Хисматуллина / base=22

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 22

## Файзрахмана Хисматуллина / base=23

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 23

## Файзрахмана Хисматуллина / base=24

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 24

## Файзрахмана Хисматуллина / base=25

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 25

## Файзрахмана Хисматуллина / base=26

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 26

## Файзрахмана Хисматуллина / base=27

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 27

## Файзрахмана Хисматуллина / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 28

## Файзрахмана Хисматуллина / base=29

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 29

## Файзрахмана Хисматуллина / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 30

## Файзрахмана Хисматуллина / base=31

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 31

## Файзрахмана Хисматуллина / base=32

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 32

## Файзрахмана Хисматуллина / base=33

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 33

## Файзрахмана Хисматуллина / base=34

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 34

## Файзрахмана Хисматуллина / base=35

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 35

## Файзрахмана Хисматуллина / base=36

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 36

## Файзрахмана Хисматуллина / base=37

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 37

## Файзрахмана Хисматуллина / base=38

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 38

## Файзрахмана Хисматуллина / base=39

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 39

## Файзрахмана Хисматуллина / base=40

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 40

## Файзрахмана Хисматуллина / base=41

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 41

## Файзрахмана Хисматуллина / base=42

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 42

## Файзрахмана Хисматуллина / base=43

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 43

## Файзрахмана Хисматуллина / base=44

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 44

## Файзрахмана Хисматуллина / base=45

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 45

## Файзрахмана Хисматуллина / base=46

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 46

## Файзрахмана Хисматуллина / base=47

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 47

## Файзрахмана Хисматуллина / base=48

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 48

## Файзрахмана Хисматуллина / base=49

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 49

## Файзрахмана Хисматуллина / base=50

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 50

## Файзрахмана Хисматуллина / base=51

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 51

## Файзрахмана Хисматуллина / base=52

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 52

## Файзрахмана Хисматуллина / base=53

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 53

## Файзрахмана Хисматуллина / base=54

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 54

## Файзрахмана Хисматуллина / base=55

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 55

## Файзрахмана Хисматуллина / base=56

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 56

## Файзрахмана Хисматуллина / base=57

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 57

## Файзрахмана Хисматуллина / base=58

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 58

## Файзрахмана Хисматуллина / base=59

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 59

## Файзрахмана Хисматуллина / base=60

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 60

## Файзрахмана Хисматуллина / base=62

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408

- 62
- 62к2

## Шагали Шакман / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 1

## Шагали Шакман / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 2

## Шагали Шакман / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 3

## Шагали Шакман / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 4

## Шагали Шакман / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 5

## Шагали Шакман / base=6

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 6

## Шагали Шакман / base=8

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 8

## Шагали Шакман / base=10

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 10

## Шагали Шакман / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 12

## Шагали Шакман / base=14

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 14

## Шагали Шакман / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 16

## Шагали Шакман / base=18

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 414

- 18

## Шагали Шакмана / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 415

- 1/1

## Шагали Шакмана / base=9

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 415

- 9

## Шагали Шакмана / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 415

- 16/1

## Шайхзады Бабича / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 1

## Шайхзады Бабича / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 2

## Шайхзады Бабича / base=3

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 3

## Шайхзады Бабича / base=4

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 4

## Шайхзады Бабича / base=5

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 5

## Шайхзады Бабича / base=6

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 6

## Шайхзады Бабича / base=7

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 7

## Шайхзады Бабича / base=8

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 8

## Шайхзады Бабича / base=9

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 9

## Шайхзады Бабича / base=10

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 10

## Шайхзады Бабича / base=11

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 11

## Шайхзады Бабича / base=12

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 12

## Шайхзады Бабича / base=13

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 13

## Шайхзады Бабича / base=14

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 14

## Шайхзады Бабича / base=15

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 15

## Шайхзады Бабича / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 16

## Шайхзады Бабича / base=17

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 17

## Шайхзады Бабича / base=18

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 18

## Шайхзады Бабича / base=19

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 19

## Шайхзады Бабича / base=20

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 20

## Шайхзады Бабича / base=21

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 21

## Шайхзады Бабича / base=22

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 22

## Шайхзады Бабича / base=23

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 23

## Шайхзады Бабича / base=24

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 24

## Шайхзады Бабича / base=25

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 25

## Шайхзады Бабича / base=26

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 26

## Шайхзады Бабича / base=27

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 27

## Шайхзады Бабича / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 28
- 28/1

## Шайхзады Бабича / base=29

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 29

## Шайхзады Бабича / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 30

## Шайхзады Бабича / base=31

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 31

## Шайхзады Бабича / base=32

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 32

## Шайхзады Бабича / base=33

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 33

## Шайхзады Бабича / base=35

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 35

## Шайхзады Бабича / base=37

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 37

## Шайхзады Бабича / base=39

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 39

## Шайхзады Бабича / base=41

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 41

## Шайхзады Бабича / base=43

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 43
- 43/1

## Шайхзады Бабича / base=45

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 45

## Шайхзады Бабича / base=47

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 47

## Шайхзады Бабича / base=49

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 49

## Шайхзады Бабича / base=51

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 51

## Шайхзады Бабича / base=53

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 53

## Шайхзады Бабича / base=55

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417

- 55

## 40 лет Октября / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 332

- 2

## 40 лет Октября / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 332

- 4

## 40 лет Октября / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 332

- 10

## 40 лет Октября / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 332

- 11

## 40 лет Октября / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 332

- 15

## Гагарина / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 1
- 1а

## Гагарина / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 2а

## Гагарина / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 3

## Гагарина / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 4

## Гагарина / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 5

## Гагарина / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 6

## Гагарина / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 7

## Гагарина / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 8

## Гагарина / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 9

## Гагарина / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345

- 11

## Горная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 1
- 1а
- 1б

## Горная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 2
- 2а
- 2б
- 2В
- 2/1

## Горная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 3
- 3А

## Горная / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 4

## Горная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 5

## Горная / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 6

## Горная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 7

## Горная / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 8
- 8а

## Горная / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 9

## Горная / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 10

## Горная / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 11

## Горная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 12

## Горная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 13
- 13А

## Горная / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 14

## Горная / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 15

## Горная / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 16

## Горная / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 17

## Горная / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 18

## Горная / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 19

## Горная / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 20

## Горная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 21
- 21А
- 21Б

## Горная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 23

## Горная / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 24

## Горная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 25

## Горная / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 26

## Горная / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 27

## Горная / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 28

## Горная / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 29

## Горная / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 30

## Горная / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 31

## Горная / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 32

## Горная / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 33

## Горная / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 34

## Горная / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 35

## Горная / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 36

## Горная / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 37

## Горная / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 38

## Горная / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 39

## Горная / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 40

## Горная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 41

## Горная / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 42

## Горная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 43
- 43а

## Горная / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 44

## Горная / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 45

## Горная / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 46

## Горная / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 47а

## Горная / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 48

## Горная / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 49

## Горная / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 50
- 50а
- 50б

## Горная / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 51

## Горная / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 53

## Горная / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 55

## Горная / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347

- 57

## Кирова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 1

## Кирова / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 2

## Кирова / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 3

## Кирова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 4

## Кирова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 5
- 5а

## Кирова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 6

## Кирова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 7

## Кирова / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 8

## Кирова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 9

## Кирова / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 10

## Кирова / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 11

## Кирова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 12

## Кирова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 14

## Кирова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 16

## Кирова / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 18

## Кирова / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 20

## Кирова / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 22

## Кирова / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 24

## Кирова / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 26

## Кирова / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358

- 28

## Колхозная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 1

## Колхозная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 2
- 2а
- 2б

## Колхозная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 3

## Колхозная / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 4

## Колхозная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 5

## Колхозная / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 6

## Колхозная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 7

## Колхозная / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 8

## Колхозная / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 9

## Колхозная / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 10

## Колхозная / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 11

## Колхозная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 12

## Колхозная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 13

## Колхозная / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 14

## Колхозная / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 16

## Колхозная / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 17

## Колхозная / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 18

## Колхозная / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 19

## Колхозная / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 20

## Колхозная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 21

## Колхозная / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 22

## Колхозная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 23

## Колхозная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 25

## Колхозная / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 26

## Колхозная / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 27

## Колхозная / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 28

## Колхозная / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 29

## Колхозная / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 30

## Колхозная / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 31

## Колхозная / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 32

## Колхозная / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 33

## Колхозная / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 34

## Колхозная / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 35

## Колхозная / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 36

## Колхозная / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 37

## Колхозная / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 38

## Колхозная / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 40

## Колхозная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 41

## Колхозная / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 42

## Колхозная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 43

## Колхозная / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 44

## Колхозная / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 46

## Колхозная / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 48

## Колхозная / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 50

## Колхозная / base=52

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 52

## Колхозная / base=54

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 54

## Колхозная / base=56

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 56

## Колхозная / base=58

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 58

## Колхозная / base=60

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359

- 60

## Комарова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 1
- 1к1

## Комарова / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 2
- 2к1

## Комарова / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 3

## Комарова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 4

## Комарова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 5
- 5к1

## Комарова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 6
- 6а
- 6к1

## Комарова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 7
- 7А

## Комарова / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 8

## Комарова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 9

## Комарова / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 10

## Комарова / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 11

## Комарова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 12

## Комарова / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 13

## Комарова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 14

## Комарова / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 15

## Комарова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 16

## Комарова / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 17

## Комарова / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 18

## Комарова / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 19

## Комарова / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 20

## Комарова / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 21

## Комарова / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 22

## Комарова / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360

- 23

## Коммунистическая / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 1
- 1а
- 1Б
- 1к1
- 1к2
- 1к3
- 1к4
- 1к5
- 1к6

## Коммунистическая / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 2
- 2а
- 2б
- 2к1
- 2к2
- 2к3
- 2к5
- 2/4

## Коммунистическая / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 3

## Коммунистическая / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 5

## Коммунистическая / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 7

## Коммунистическая / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 8
- 8а

## Коммунистическая / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 9

## Коммунистическая / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 10

## Коммунистическая / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 11
- 11/1

## Коммунистическая / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 16

## Коммунистическая / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 19

## Коммунистическая / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 21
- 21б
- 21в
- 21к4
- 21/2
- 21/3

## Коммунистическая / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 22
- 22/1

## Коммунистическая / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 23

## Коммунистическая / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 24

## Коммунистическая / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 25
- 25А

## Коммунистическая / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 26

## Коммунистическая / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 27

## Коммунистическая / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 28/1
- 28/3

## Коммунистическая / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 29

## Коммунистическая / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 30

## Коммунистическая / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 31

## Коммунистическая / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 32
- 32/1

## Коммунистическая / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 33

## Коммунистическая / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 34

## Коммунистическая / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 35

## Коммунистическая / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 36

## Коммунистическая / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 37

## Коммунистическая / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 38
- 38/1

## Коммунистическая / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 39

## Коммунистическая / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 41

## Коммунистическая / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 43

## Коммунистическая / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361

- 45

## Комсомольская / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 1

## Комсомольская / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 2

## Комсомольская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 3

## Комсомольская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 4
- 4А

## Комсомольская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 5

## Комсомольская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 6

## Комсомольская / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 7

## Комсомольская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 8

## Комсомольская / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 9

## Комсомольская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 10

## Комсомольская / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 12

## Комсомольская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 14

## Комсомольская / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 15

## Комсомольская / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 16

## Комсомольская / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 17

## Комсомольская / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 18

## Комсомольская / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 19

## Комсомольская / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 20

## Комсомольская / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 21

## Комсомольская / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 22

## Комсомольская / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 24

## Комсомольская / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 26

## Комсомольская / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 28

## Комсомольская / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 30

## Комсомольская / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 32

## Комсомольская / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362

- 34

## Ленина / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 1

## Ленина / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 2
- 2а
- 2б
- 2в
- 2/1

## Ленина / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 3

## Ленина / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 4
- 4а

## Ленина / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 5

## Ленина / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 6

## Ленина / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 7

## Ленина / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 8

## Ленина / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 9

## Ленина / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 10

## Ленина / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 11

## Ленина / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 12

## Ленина / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 13

## Ленина / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 14
- 14к1

## Ленина / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 15

## Ленина / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 16/1

## Ленина / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 17

## Ленина / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 18

## Ленина / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 19

## Ленина / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 22

## Ленина / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 23

## Ленина / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 24

## Ленина / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 25

## Ленина / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 26

## Ленина / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 27

## Ленина / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 28

## Ленина / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 29/1

## Ленина / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 30

## Ленина / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 31

## Ленина / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 32

## Ленина / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 33

## Ленина / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 34

## Ленина / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 35

## Ленина / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 36

## Ленина / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 37

## Ленина / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 38
- 38/1

## Ленина / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 39

## Ленина / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 40

## Ленина / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 41

## Ленина / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 42

## Ленина / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 43

## Ленина / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 44

## Ленина / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 46

## Ленина / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 48

## Ленина / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 49

## Ленина / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 50

## Ленина / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 51
- 51А

## Ленина / base=52

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 52
- 52к1

## Ленина / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 53

## Ленина / base=54

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 54

## Ленина / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 55

## Ленина / base=56

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 56

## Ленина / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 57

## Ленина / base=58

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 58

## Ленина / base=60

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 60

## Ленина / base=61

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 61

## Ленина / base=62

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 62

## Ленина / base=63

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 63

## Ленина / base=64

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 64

## Ленина / base=65

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 65

## Ленина / base=66

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 66

## Ленина / base=68

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 68

## Ленина / base=69

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 69

## Ленина / base=71

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 71

## Ленина / base=72

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 72

## Ленина / base=73

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 73

## Ленина / base=74

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 74

## Ленина / base=75

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 75

## Ленина / base=76

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 76

## Ленина / base=77

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 77

## Ленина / base=78

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 78

## Ленина / base=79

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 79

## Ленина / base=80

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 80

## Ленина / base=81

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 81

## Ленина / base=85

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 85

## Ленина / base=87

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 87

## Ленина / base=89

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 89

## Ленина / base=91

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 91

## Ленина / base=95

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 95

## Ленина / base=97

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 97

## Ленина / base=99

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 99

## Ленина / base=100

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 100

## Ленина / base=101

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 101

## Ленина / base=105

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 105

## Ленина / base=107

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 107

## Ленина / base=109

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 109

## Ленина / base=111

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 111

## Ленина / base=113

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 113

## Ленина / base=115

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 115

## Ленина / base=119

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 119

## Ленина / base=121

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 121

## Ленина / base=123

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 123

## Ленина / base=125

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 125

## Ленина / base=127

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 127
- 127/1

## Ленина / base=131

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 131

## Ленина / base=133

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 133

## Ленина / base=135

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 135

## Ленина / base=137

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 137

## Ленина / base=139

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 139

## Ленина / base=141

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 141к1

## Ленина / base=143

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 143

## Ленина / base=145

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 145

## Ленина / base=147

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 147

## Ленина / base=149

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 149

## Ленина / base=151

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 151

## Ленина / base=155

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 155/1
- 155/2

## Ленина / base=157

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364

- 157

## Матросова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 1

## Матросова / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 2

## Матросова / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 3
- 3а

## Матросова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 4

## Матросова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 5
- 5а

## Матросова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 6

## Матросова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 7
- 7/1

## Матросова / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 8

## Матросова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 9а
- 9Б

## Матросова / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 10/1
- 10/2

## Матросова / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 11

## Матросова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 12

## Матросова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 14
- 14/1

## Матросова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 16

## Матросова / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 18

## Матросова / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370

- 20

## Мира / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 1
- 1а

## Мира / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 2а

## Мира / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 3
- 3/1

## Мира / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 4/1

## Мира / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 5

## Мира / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 6/1
- 6/2

## Мира / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 7

## Мира / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 8

## Мира / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 9

## Мира / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 10/1
- 10/2

## Мира / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 11
- 11а

## Мира / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 12/2

## Мира / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 13

## Мира / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 14

## Мира / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 15
- 15/1

## Мира / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 16

## Мира / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 17

## Мира / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 18

## Мира / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 19

## Мира / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 20

## Мира / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 22

## Мира / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 23

## Мира / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 25

## Мира / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 27
- 27/1
- 27/2

## Мира / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 29
- 29/1

## Мира / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 31
- 31/1

## Мира / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 33

## Мира / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 35

## Мира / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 37

## Мира / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 39

## Мира / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 41

## Мира / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 43

## Мира / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375

- 45

## Молодежная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 1

## Молодежная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 2

## Молодежная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 3

## Молодежная / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 4

## Молодежная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 5

## Молодежная / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 6

## Молодежная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 7
- 7а

## Молодежная / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 8

## Молодежная / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 9

## Молодежная / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 10
- 10а
- 10б
- 10/1

## Молодежная / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 11

## Молодежная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 12
- 12а

## Молодежная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 13
- 13/3

## Молодежная / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 14

## Молодежная / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 15

## Молодежная / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 16

## Молодежная / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 17

## Молодежная / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 18

## Молодежная / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 19

## Молодежная / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 20
- 20б

## Молодежная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 21

## Молодежная / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 22

## Молодежная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 23

## Молодежная / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 24
- 24а

## Молодежная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 25
- 25а
- 25к1

## Молодежная / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 26

## Молодежная / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 27

## Молодежная / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 28
- 28к3

## Молодежная / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 29

## Молодежная / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 30
- 30/1

## Молодежная / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 31

## Молодежная / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 32

## Молодежная / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 33

## Молодежная / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 35

## Молодежная / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 36
- 36/2
- 36/3

## Молодежная / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 37

## Молодежная / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 38

## Молодежная / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 39
- 39А

## Молодежная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 41
- 41а

## Молодежная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 43

## Молодежная / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 44

## Молодежная / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 45

## Молодежная / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 47

## Молодежная / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 49

## Молодежная / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 51

## Молодежная / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 53

## Молодежная / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 55

## Молодежная / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 57
- 57а

## Молодежная / base=59

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376

- 59

## Мугалляма Мирхайдарова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 1

## Мугалляма Мирхайдарова / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 2

## Мугалляма Мирхайдарова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 4

## Мугалляма Мирхайдарова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 5

## Мугалляма Мирхайдарова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 6

## Мугалляма Мирхайдарова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 7

## Мугалляма Мирхайдарова / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 8

## Мугалляма Мирхайдарова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 9

## Мугалляма Мирхайдарова / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 10

## Мугалляма Мирхайдарова / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 11

## Мугалляма Мирхайдарова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 12

## Мугалляма Мирхайдарова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 14

## Мугалляма Мирхайдарова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 377

- 16

## Партизанская / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 1

## Партизанская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 3

## Партизанская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 4

## Партизанская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 5

## Партизанская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 6
- 6А

## Партизанская / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 7

## Партизанская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 8

## Партизанская / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 9

## Партизанская / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 11

## Партизанская / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 12

## Партизанская / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 13

## Партизанская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 14
- 14а

## Партизанская / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 15

## Партизанская / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 16

## Партизанская / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 17

## Партизанская / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 18

## Партизанская / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 19

## Партизанская / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 20

## Партизанская / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 21

## Партизанская / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 23

## Партизанская / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 24
- 24/2

## Партизанская / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 25

## Партизанская / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 26

## Партизанская / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 27

## Партизанская / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 28

## Партизанская / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 29

## Партизанская / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 30

## Партизанская / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 31

## Партизанская / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 32

## Партизанская / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 33

## Партизанская / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 34

## Партизанская / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 35

## Партизанская / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 36

## Партизанская / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 37

## Партизанская / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 38

## Партизанская / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 39

## Партизанская / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 40

## Партизанская / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 41

## Партизанская / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 42

## Партизанская / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 43

## Партизанская / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 44

## Партизанская / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 45

## Партизанская / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 46

## Партизанская / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 47

## Партизанская / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 48

## Партизанская / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 49

## Партизанская / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 50

## Партизанская / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 51

## Партизанская / base=52

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 52

## Партизанская / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 53

## Партизанская / base=54

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 54

## Партизанская / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 55

## Партизанская / base=56

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 56

## Партизанская / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 57
- 57а

## Партизанская / base=58

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 58

## Партизанская / base=59

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 59Б

## Партизанская / base=60

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 60

## Партизанская / base=61

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 61

## Партизанская / base=62

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 62

## Партизанская / base=63

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 63

## Партизанская / base=64

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 64

## Партизанская / base=65

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381

- 65

## Первомайская / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 1

## Первомайская / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 2

## Первомайская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 3

## Первомайская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 4

## Первомайская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 5

## Первомайская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 6

## Первомайская / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 7

## Первомайская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 8

## Первомайская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 382

- 10

## Салавата Юлаева / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 1

## Салавата Юлаева / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 2
- 2а

## Салавата Юлаева / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 3

## Салавата Юлаева / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 4

## Салавата Юлаева / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 5

## Салавата Юлаева / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 6

## Салавата Юлаева / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 7

## Салавата Юлаева / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 8
- 8/1

## Салавата Юлаева / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 9

## Салавата Юлаева / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 11

## Салавата Юлаева / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 12
- 12а

## Салавата Юлаева / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 13

## Салавата Юлаева / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 14

## Салавата Юлаева / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 16

## Салавата Юлаева / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 18

## Салавата Юлаева / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 19

## Салавата Юлаева / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 20

## Салавата Юлаева / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 21

## Салавата Юлаева / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 22

## Салавата Юлаева / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 23

## Салавата Юлаева / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 24

## Салавата Юлаева / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 25

## Салавата Юлаева / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 26

## Салавата Юлаева / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 27

## Салавата Юлаева / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 28

## Салавата Юлаева / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 29

## Салавата Юлаева / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 30

## Салавата Юлаева / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 31

## Салавата Юлаева / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 33
- 33а

## Салавата Юлаева / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 34

## Салавата Юлаева / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 35

## Салавата Юлаева / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 36

## Салавата Юлаева / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 37

## Салавата Юлаева / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 38
- 38А

## Салавата Юлаева / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 40

## Салавата Юлаева / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 42

## Салавата Юлаева / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 44

## Салавата Юлаева / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 46
- 46/1

## Салавата Юлаева / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 48

## Салавата Юлаева / base=65

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393

- 65а
- 65/1

## Советская / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 1

## Советская / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 2

## Советская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 3

## Советская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 4А
- 4Б

## Советская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 5

## Советская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 6

## Советская / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 7

## Советская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 8

## Советская / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 9

## Советская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 10

## Советская / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 11

## Советская / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 13

## Советская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 14

## Советская / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 15

## Советская / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 16

## Советская / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 17

## Советская / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 19

## Советская / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 20

## Советская / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 21

## Советская / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 22

## Советская / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 23

## Советская / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 24

## Советская / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 26

## Советская / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 27

## Советская / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396

- 36

## Тангатарская / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 2

## Тангатарская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 3

## Тангатарская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 4

## Тангатарская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 5
- 5а

## Тангатарская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 6

## Тангатарская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 8к1

## Тангатарская / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 9

## Тангатарская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 10
- 10к2

## Тангатарская / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 12/1
- 12/2

## Тангатарская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 14

## Тангатарская / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 15

## Тангатарская / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 17

## Тангатарская / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 19

## Тангатарская / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 21

## Тангатарская / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 23

## Тангатарская / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 24

## Тангатарская / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 25

## Тангатарская / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 26

## Тангатарская / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 27

## Тангатарская / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 28

## Тангатарская / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 29

## Тангатарская / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 30

## Тангатарская / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 31

## Тангатарская / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 32

## Тангатарская / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 33

## Тангатарская / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 34
- 34А

## Тангатарская / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 35

## Тангатарская / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 36

## Тангатарская / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 37

## Тангатарская / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 39
- 39/1

## Тангатарская / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 40

## Тангатарская / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 41

## Тангатарская / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 42

## Тангатарская / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 43

## Тангатарская / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 44

## Тангатарская / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 45

## Тангатарская / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 46

## Тангатарская / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 47

## Тангатарская / base=48

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 48

## Тангатарская / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 49/1

## Тангатарская / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 50

## Тангатарская / base=52

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 52

## Тангатарская / base=54

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 54

## Тангатарская / base=56

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 56

## Тангатарская / base=58

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 58

## Тангатарская / base=60

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 60

## Тангатарская / base=62

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 62

## Тангатарская / base=64

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 64

## Тангатарская / base=66

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402

- 66

## Учалинская / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 1

## Учалинская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 3
- 3/1

## Учалинская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 5

## Учалинская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 8

## Учалинская / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 9

## Учалинская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 10

## Учалинская / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 11

## Учалинская / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 12

## Учалинская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 14

## Учалинская / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 16
- 16к1
- 16/2

## Учалинская / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406

- 18
- 18а

## Чапаева / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 1

## Чапаева / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 18

## Чапаева / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 19

## Чапаева / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 21

## Чапаева / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 23

## Чапаева / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 25

## Чапаева / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 413

- 27

## Шаймуратова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 1

## Шаймуратова / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 3

## Шаймуратова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 4
- 4/1

## Шаймуратова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 5

## Шаймуратова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 6/1

## Шаймуратова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 9

## Шаймуратова / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 11

## Шаймуратова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 12
- 12а

## Шаймуратова / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 13

## Шаймуратова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 14
- 14/1
- 14/2

## Шаймуратова / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 15

## Шаймуратова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 16
- 16/1

## Шаймуратова / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 17

## Шаймуратова / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 18

## Шаймуратова / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 19

## Шаймуратова / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 20

## Шаймуратова / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 21

## Шаймуратова / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 22

## Шаймуратова / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 23

## Шаймуратова / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 24

## Шаймуратова / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 25

## Шаймуратова / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 26

## Шаймуратова / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 27

## Шаймуратова / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 28

## Шаймуратова / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 29

## Шаймуратова / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 30

## Шаймуратова / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 31

## Шаймуратова / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 32

## Шаймуратова / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 33

## Шаймуратова / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 34

## Шаймуратова / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 36

## Шаймуратова / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 37

## Шаймуратова / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 38

## Шаймуратова / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 39а
- 39Б

## Шаймуратова / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 40

## Шаймуратова / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 41

## Шаймуратова / base=42

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 42

## Шаймуратова / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 43

## Шаймуратова / base=44

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 44

## Шаймуратова / base=45

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 45

## Шаймуратова / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 47

## Шаймуратова / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 49

## Шаймуратова / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 50

## Шаймуратова / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 51

## Шаймуратова / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 53
- 53к1

## Шаймуратова / base=54

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 54

## Шаймуратова / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 55
- 55/1

## Шаймуратова / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 57

## Шаймуратова / base=61

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 61

## Шаймуратова / base=63

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 63

## Шаймуратова / base=65

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 65

## Шаймуратова / base=67

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 67

## Шаймуратова / base=68

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 68

## Шаймуратова / base=71

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 71

## Шаймуратова / base=76

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 76

## Шаймуратова / base=77

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 77

## Шаймуратова / base=78

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 78

## Шаймуратова / base=80

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 80

## Шаймуратова / base=81

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 81

## Шаймуратова / base=84

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 84

## Шаймуратова / base=86

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416

- 86
- 86/1

## Школьная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 1

## Школьная / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 4

## Школьная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 5

## Школьная / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 6

## Школьная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 7

## Школьная / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 418

- 26

## Юбилейная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 1
- 1а

## Юбилейная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 3
- 3а

## Юбилейная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 5

## Юбилейная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 7

## Юбилейная / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 9

## Юбилейная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 12/1

## Юбилейная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 13

## Юбилейная / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 14

## Юбилейная / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 15

## Юбилейная / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 17

## Юбилейная / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 19

## Юбилейная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 21

## Юбилейная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 23
- 23/1

## Юбилейная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 25

## Юбилейная / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 27

## Юбилейная / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 29

## Юбилейная / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 31

## Юбилейная / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 33
- 33а
- 33б
- 33В
- 33к1
- 33к2
- 33к4

## Юбилейная / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 35
- 35/1
- 35/2
- 35/3
- 35/4

## Юбилейная / base=37

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 37

## Юбилейная / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 39

## Юбилейная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 41/2

## Юбилейная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419

- 43/1

## Южная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 1

## Южная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 2
- 2а
- 2б

## Южная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 3

## Южная / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 4

## Южная / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 5

## Южная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 7

## Южная / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 8

## Южная / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 9

## Южная / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 10

## Южная / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 11А

## Южная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 12

## Южная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 13

## Южная / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 14

## Южная / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 15

## Южная / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 16

## Южная / base=17

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 17

## Южная / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 18

## Южная / base=19

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 19

## Южная / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 20

## Южная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 21

## Южная / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 22

## Южная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 23

## Южная / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 24

## Южная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 25

## Южная / base=26

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 26

## Южная / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 27

## Южная / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 28

## Южная / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 29

## Южная / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 30

## Южная / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 32

## Южная / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 34

## Южная / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 36

## Южная / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 38

## Южная / base=40

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420

- 40

## 40 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 1

## 40 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 2

## 40 лет Победы / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 3

## 40 лет Победы / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 4

## 40 лет Победы / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 5

## 40 лет Победы / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 6

## 40 лет Победы / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 7

## 40 лет Победы / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 8

## 40 лет Победы / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 9

## 40 лет Победы / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 10

## 40 лет Победы / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 11

## 40 лет Победы / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 12

## 40 лет Победы / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 13

## 40 лет Победы / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 14

## 40 лет Победы / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 15

## 40 лет Победы / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 16
- 16/1

## 40 лет Победы / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 17

## 40 лет Победы / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 18

## 40 лет Победы / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 19

## 40 лет Победы / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 20

## 40 лет Победы / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 21

## 40 лет Победы / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 22

## 40 лет Победы / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 23

## 40 лет Победы / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 24

## 40 лет Победы / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 25

## 40 лет Победы / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 26

## 40 лет Победы / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 27

## 40 лет Победы / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 28

## 40 лет Победы / base=29

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 29

## 40 лет Победы / base=30

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 30

## 40 лет Победы / base=31

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 31

## 40 лет Победы / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 32

## 40 лет Победы / base=34

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 34

## 40 лет Победы / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 35

## 40 лет Победы / base=36

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 36

## 40 лет Победы / base=37

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 37

## 40 лет Победы / base=39

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 39

## 40 лет Победы / base=41

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 41

## 40 лет Победы / base=43

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 43

## 40 лет Победы / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 45

## 40 лет Победы / base=47

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 47

## 40 лет Победы / base=49

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 49
- 49/2

## 40 лет Победы / base=51

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333

- 51

## 70 лет Октября / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 1

## 70 лет Октября / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 2

## 70 лет Октября / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 3

## 70 лет Октября / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 4

## 70 лет Октября / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 5

## 70 лет Октября / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 6

## 70 лет Октября / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 8

## 70 лет Октября / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 9

## 70 лет Октября / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 10

## 70 лет Октября / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 11

## 70 лет Октября / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 12

## 70 лет Октября / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 14

## 70 лет Октября / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 15
- 15/1

## 70 лет Октября / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 16

## 70 лет Октября / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 17
- 17к1
- 17к2
- 17к3
- 17к4

## 70 лет Октября / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 18

## 70 лет Октября / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 19
- 19к1
- 19к2
- 19к3

## 70 лет Октября / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 21

## 70 лет Октября / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 22
- 22/1
- 22/2

## 70 лет Октября / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 23

## 70 лет Октября / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 25

## 70 лет Октября / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 26

## 70 лет Октября / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 27

## 70 лет Октября / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 28

## 70 лет Октября / base=29

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 29

## 70 лет Октября / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 32

## 70 лет Октября / base=33

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 33

## 70 лет Октября / base=34

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 34

## 70 лет Октября / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 35

## 70 лет Октября / base=36

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 36

## 70 лет Октября / base=37

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 37

## 70 лет Октября / base=38

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 38

## 70 лет Октября / base=41

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 41

## 70 лет Октября / base=43

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 43

## 70 лет Октября / base=46

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 46

## 70 лет Октября / base=47

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 47

## 70 лет Октября / base=48

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 48

## 70 лет Октября / base=49

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 49

## 70 лет Октября / base=50

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 50

## 70 лет Октября / base=51

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 51
- 51к2
- 51к3
- 51к4
- 51к5
- 51/1

## 70 лет Октября / base=52

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 52

## 70 лет Октября / base=53

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 53
- 53к1
- 53к2
- 53к3

## 70 лет Октября / base=54

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 54

## 70 лет Октября / base=55

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 55

## 70 лет Октября / base=56

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 56

## 70 лет Октября / base=57

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 57

## 70 лет Октября / base=58

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 58

## 70 лет Октября / base=59

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 59

## 70 лет Октября / base=60

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 60

## 70 лет Октября / base=63

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 63

## 70 лет Октября / base=65

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 65

## 70 лет Октября / base=67

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 67

## 70 лет Октября / base=69

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 69

## 70 лет Октября / base=71

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 71

## 70 лет Октября / base=73

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 73

## 70 лет Октября / base=75

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 75

## 70 лет Октября / base=77

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 77

## 70 лет Октября / base=79

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 79

## 70 лет Октября / base=81

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 81

## 70 лет Октября / base=83

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 83

## 70 лет Октября / base=85

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 85

## 70 лет Октября / base=87

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 87

## 70 лет Октября / base=89

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337

- 89

## Дружбы / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 1

## Дружбы / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 2

## Дружбы / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 3

## Дружбы / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 4

## Дружбы / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 5

## Дружбы / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 6

## Дружбы / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 7

## Дружбы / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 8

## Дружбы / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 9

## Дружбы / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 10

## Дружбы / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 11
- 11к1

## Дружбы / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 12

## Дружбы / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 13

## Дружбы / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 14

## Дружбы / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 15

## Дружбы / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 16

## Дружбы / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 17

## Дружбы / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 18

## Дружбы / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 19

## Дружбы / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 20

## Дружбы / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 21

## Дружбы / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 22

## Дружбы / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 23
- 23А

## Дружбы / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 24

## Дружбы / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 25

## Дружбы / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 26

## Дружбы / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 27

## Дружбы / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 28

## Дружбы / base=30

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 30

## Дружбы / base=31

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 31

## Дружбы / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 32

## Дружбы / base=33

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 33

## Дружбы / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348

- 35/1

## Идяш / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 1

## Идяш / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 2

## Идяш / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 3

## Идяш / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 4

## Идяш / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 5

## Идяш / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 6

## Идяш / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 7

## Идяш / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 8

## Идяш / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 9

## Идяш / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 10

## Идяш / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 12

## Идяш / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 14

## Идяш / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 16

## Идяш / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 18

## Идяш / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 20

## Идяш / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 22

## Идяш / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 24

## Идяш / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 26

## Идяш / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 28

## Идяш / base=30

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 30

## Идяш / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 32

## Идяш / base=34

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 34

## Идяш / base=36

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 36

## Идяш / base=38

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 38

## Идяш / base=40

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 40

## Идяш / base=41

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 41

## Идяш / base=42

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 42

## Идяш / base=43

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 43

## Идяш / base=44

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 44

## Идяш / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 45
- 45/1

## Идяш / base=46

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 46

## Идяш / base=47

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 47

## Идяш / base=48

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 48

## Идяш / base=49

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 49

## Идяш / base=50

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 50

## Идяш / base=51

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 51

## Идяш / base=52

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 52

## Идяш / base=53

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 53

## Идяш / base=56

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 56

## Идяш / base=57

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 57

## Идяш / base=86

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 86А

## Идяш / base=87

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 87

## Идяш / base=91

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 91

## Идяш / base=93

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352

- 93

## Искра / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 1

## Искра / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 2

## Искра / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 3

## Искра / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 4

## Искра / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 6

## Искра / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 7

## Искра / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 8

## Искра / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 9

## Искра / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 10

## Искра / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 11

## Искра / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 12

## Искра / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 13

## Искра / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 14

## Искра / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 15

## Искра / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 16

## Искра / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 17

## Искра / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 19

## Искра / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 21

## Искра / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 23

## Искра / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 25

## Искра / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 26

## Искра / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 354

- 27

## Лесная / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 1

## Лесная / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 2

## Лесная / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 3

## Лесная / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 4

## Лесная / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 5

## Лесная / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 6

## Лесная / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 7

## Лесная / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 8

## Лесная / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 9

## Лесная / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 11

## Лесная / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 13

## Лесная / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 14

## Лесная / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 15

## Лесная / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 16

## Лесная / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 18

## Лесная / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 20

## Лесная / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 22

## Лесная / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 24

## Лесная / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 365

- 26

## Мажита Гафури / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 1
- 1/1

## Мажита Гафури / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 2

## Мажита Гафури / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 4

## Мажита Гафури / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 10

## Мажита Гафури / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 13

## Мажита Гафури / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 14

## Мажита Гафури / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 15

## Мажита Гафури / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 16

## Мажита Гафури / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 17

## Мажита Гафури / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 18

## Мажита Гафури / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 19

## Мажита Гафури / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 20

## Мажита Гафури / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 21

## Мажита Гафури / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 22

## Мажита Гафури / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 23

## Мажита Гафури / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 25

## Мажита Гафури / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368

- 27

## Мелиораторов / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 1

## Мелиораторов / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 2

## Мелиораторов / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 3

## Мелиораторов / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 4

## Мелиораторов / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 5

## Мелиораторов / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 6
- 6к1

## Мелиораторов / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 7
- 7а

## Мелиораторов / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 8
- 8к1

## Мелиораторов / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 9

## Мелиораторов / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 10

## Мелиораторов / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 11

## Мелиораторов / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 12

## Мелиораторов / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 13

## Мелиораторов / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 14

## Мелиораторов / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 15

## Мелиораторов / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 16

## Мелиораторов / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 17

## Мелиораторов / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 19

## Мелиораторов / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 20

## Мелиораторов / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 21

## Мелиораторов / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 22

## Мелиораторов / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 23

## Мелиораторов / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 24

## Мелиораторов / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371

- 26

## Механизаторов / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 1

## Механизаторов / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 2

## Механизаторов / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 3

## Механизаторов / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 4

## Механизаторов / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 5

## Механизаторов / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 6

## Механизаторов / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 7

## Механизаторов / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 8

## Механизаторов / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 9

## Механизаторов / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 10

## Механизаторов / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 11

## Механизаторов / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 12

## Механизаторов / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 13

## Механизаторов / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 14

## Механизаторов / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 15

## Механизаторов / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 16

## Механизаторов / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 17

## Механизаторов / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 18

## Механизаторов / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 19

## Механизаторов / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 20

## Механизаторов / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 372

- 22

## Пионерская / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 1

## Пионерская / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 2
- 2А
- 2/1
- 2/3

## Пионерская / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 3

## Пионерская / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 4/1

## Пионерская / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 5

## Пионерская / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 7

## Пионерская / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 9

## Пионерская / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 11

## Пионерская / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 13

## Пионерская / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 15

## Пионерская / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 17

## Пионерская / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 18/1
- 18/2

## Пионерская / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 19

## Пионерская / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 20

## Пионерская / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 21

## Пионерская / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 23

## Пионерская / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 25

## Пионерская / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 27

## Пионерская / base=29

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 29

## Пионерская / base=31

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 31

## Пионерская / base=33

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383

- 33

## Рауфа Давлетова / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 1
- 1к3
- 1к4
- 1/2
- 1/7

## Рауфа Давлетова / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 2
- 2а
- 2б
- 2/1

## Рауфа Давлетова / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 3

## Рауфа Давлетова / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 4
- 4/1

## Рауфа Давлетова / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 5

## Рауфа Давлетова / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 6
- 6/2
- 6/3

## Рауфа Давлетова / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 7

## Рауфа Давлетова / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 8/4

## Рауфа Давлетова / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 9

## Рауфа Давлетова / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 10/1
- 10/3
- 10/4

## Рауфа Давлетова / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 11

## Рауфа Давлетова / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 12

## Рауфа Давлетова / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 13

## Рауфа Давлетова / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 14/1

## Рауфа Давлетова / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 15
- 15/1
- 15/2

## Рауфа Давлетова / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 16/3

## Рауфа Давлетова / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 17

## Рауфа Давлетова / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 18

## Рауфа Давлетова / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 19

## Рауфа Давлетова / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 20

## Рауфа Давлетова / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 21

## Рауфа Давлетова / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 22

## Рауфа Давлетова / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 23

## Рауфа Давлетова / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 24

## Рауфа Давлетова / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 25

## Рауфа Давлетова / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 26

## Рауфа Давлетова / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 27

## Рауфа Давлетова / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 28

## Рауфа Давлетова / base=29

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 29

## Рауфа Давлетова / base=30

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 30

## Рауфа Давлетова / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 32

## Рауфа Давлетова / base=33

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 33

## Рауфа Давлетова / base=34

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 34

## Рауфа Давлетова / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 35

## Рауфа Давлетова / base=37

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 37

## Рауфа Давлетова / base=39

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 39

## Рауфа Давлетова / base=41

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 41

## Рауфа Давлетова / base=43

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 43

## Рауфа Давлетова / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 45

## Рауфа Давлетова / base=47

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 47

## Рауфа Давлетова / base=49

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 49

## Рауфа Давлетова / base=51

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 51

## Рауфа Давлетова / base=53

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 53

## Рауфа Давлетова / base=55

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 55

## Рауфа Давлетова / base=57

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 57

## Рауфа Давлетова / base=58

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 58

## Рауфа Давлетова / base=59

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 59

## Рауфа Давлетова / base=61

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 61

## Рауфа Давлетова / base=63

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 63

## Рауфа Давлетова / base=65

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 65

## Рауфа Давлетова / base=68

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 68

## Рауфа Давлетова / base=70

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388

- 70

## Рихарда Зорге / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 2
- 2/1

## Рихарда Зорге / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 3

## Рихарда Зорге / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 4

## Рихарда Зорге / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 5

## Рихарда Зорге / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 6

## Рихарда Зорге / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 7

## Рихарда Зорге / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 8

## Рихарда Зорге / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 9
- 9/1
- 9/2
- 9/3
- 9/5

## Рихарда Зорге / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 10

## Рихарда Зорге / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 11

## Рихарда Зорге / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 12

## Рихарда Зорге / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 13

## Рихарда Зорге / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 14/1
- 14/2

## Рихарда Зорге / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 15

## Рихарда Зорге / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 16
- 16а
- 16/1
- 16/2

## Рихарда Зорге / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 17

## Рихарда Зорге / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 18

## Рихарда Зорге / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 19

## Рихарда Зорге / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 20

## Рихарда Зорге / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 21

## Рихарда Зорге / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 22

## Рихарда Зорге / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 23

## Рихарда Зорге / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 24
- 24А

## Рихарда Зорге / base=25

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 25

## Рихарда Зорге / base=26

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 26

## Рихарда Зорге / base=27

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 27

## Рихарда Зорге / base=28

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 28

## Рихарда Зорге / base=29

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 29

## Рихарда Зорге / base=30

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 30

## Рихарда Зорге / base=31

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 31

## Рихарда Зорге / base=32

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 32

## Рихарда Зорге / base=33

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 33

## Рихарда Зорге / base=34

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 34

## Рихарда Зорге / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 35

## Рихарда Зорге / base=36

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 36

## Рихарда Зорге / base=37

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 37
- 37а
- 37Б
- 37/1

## Рихарда Зорге / base=38

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 38

## Рихарда Зорге / base=39

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 39

## Рихарда Зорге / base=40

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 40

## Рихарда Зорге / base=41

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 41

## Рихарда Зорге / base=42

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 42

## Рихарда Зорге / base=43

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 43

## Рихарда Зорге / base=44

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 44

## Рихарда Зорге / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 45
- 45/1

## Рихарда Зорге / base=46

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 46

## Рихарда Зорге / base=47

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 47

## Рихарда Зорге / base=48

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 48

## Рихарда Зорге / base=50

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 50

## Рихарда Зорге / base=52

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 52
- 52А

## Рихарда Зорге / base=54

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 54

## Рихарда Зорге / base=68

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390

- 68

## Строителей / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 1
- 1а

## Строителей / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 2
- 2А

## Строителей / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 3/2

## Строителей / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 4

## Строителей / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 5

## Строителей / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 6

## Строителей / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 7

## Строителей / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 8

## Строителей / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 9

## Строителей / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 10

## Строителей / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 11

## Строителей / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 12

## Строителей / base=13

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 13

## Строителей / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 14

## Строителей / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 15

## Строителей / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 16

## Строителей / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 17

## Строителей / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 18

## Строителей / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 19

## Строителей / base=20

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 20

## Строителей / base=21

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 21

## Строителей / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 22

## Строителей / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 23
- 23/1

## Строителей / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399

- 24

## Тагира Кусимова / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 1

## Тагира Кусимова / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 2

## Тагира Кусимова / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 3

## Тагира Кусимова / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 4

## Тагира Кусимова / base=5

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 5

## Тагира Кусимова / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 6

## Тагира Кусимова / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 7

## Тагира Кусимова / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 8

## Тагира Кусимова / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 9

## Тагира Кусимова / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 10

## Тагира Кусимова / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 11

## Тагира Кусимова / base=12

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 12

## Тагира Кусимова / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 14

## Тагира Кусимова / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 16

## Тагира Кусимова / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 400

- 18

---

# Potential House Suggestion Cases

Фактические группы данных, для которых существующая логика ``AddressSuggestionService`` может сформировать кандидатов. Это НЕ утверждение о бизнес-валидности suggestion — только наблюдаемые комбинации данных БД и существующих правил совместимости (одинаковый base + совместимый тип).

Всего потенциальных групп: **315**.

## 60 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## 60 лет Победы / base=6

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 6, 6/1, 6/2

### Potential input patterns

- **Дробь (FRACTION)**: `6/3` → 6/1, 6/2
- **Дом без указания варианта (PLAIN)**: `6` → 6/1, 6/2

## 60 лет Победы / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 15, 15А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15А

## 60 лет Победы / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 18, 18а, 18б, 18/1, 18/2

### Potential input patterns

- **Дробь (FRACTION)**: `18/3` → 18/1, 18/2
- **Литера у дома (LETTER)**: `18в` → 18а, 18б
- **Дом без указания варианта (PLAIN)**: `18` → 18а, 18б, 18/1, 18/2

## 60 лет Победы / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 20, 20/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20/2

## 60 лет Победы / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 46, 46А, 46/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `46` → 46А, 46/1

## 60 лет Победы / base=51

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 51, 51/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `51` → 51/1

## 60 лет Победы / base=79

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 335
- Available candidates: 79, 79/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `79` → 79/1

## Абзелиловская / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 338
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Вафира Тайсина / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343
- Available candidates: 1А, 1Б

### Potential input patterns

- **Литера у дома (LETTER)**: `1а` → 1А, 1Б
- **Дом без указания варианта (PLAIN)**: `1` → 1А, 1Б

## Вафира Тайсина / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343
- Available candidates: 2, 2/1, 2/2

### Potential input patterns

- **Дробь (FRACTION)**: `2/3` → 2/1, 2/2
- **Дом без указания варианта (PLAIN)**: `2` → 2/1, 2/2

## Вафира Тайсина / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 343
- Available candidates: 11, 11/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11/1

## Загира Исмагилова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350
- Available candidates: 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## Загира Исмагилова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350
- Available candidates: 27/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `27` → 27/1

## Загира Исмагилова / base=32

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 350
- Available candidates: 32/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `32` → 32/1

## Зайнаб Биишевой / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351
- Available candidates: 9/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `9` → 9/1

## Зайнаб Биишевой / base=37

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351
- Available candidates: 37, 37/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `37` → 37/1

## Зайнаб Биишевой / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 351
- Available candidates: 50/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `50` → 50/1

## Ишмухамета Мырзакаева / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Ишмухамета Мырзакаева / base=11

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 11, 11к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11к1

## Ишмухамета Мырзакаева / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 13, 13/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `13` → 13/1

## Ишмухамета Мырзакаева / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 25, 25/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25/1

## Ишмухамета Мырзакаева / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 35, 35/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `35` → 35/2

## Ишмухамета Мырзакаева / base=52

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 356
- Available candidates: 52/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `52` → 52/1

## Кима Ахмедьянова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Кима Ахмедьянова / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357
- Available candidates: 38, 38/1, 38/2, 38/3

### Potential input patterns

- **Дробь (FRACTION)**: `38/4` → 38/1, 38/2, 38/3
- **Дом без указания варианта (PLAIN)**: `38` → 38/1, 38/2, 38/3

## Кима Ахмедьянова / base=40

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357
- Available candidates: 40, 40/1, 40/3

### Potential input patterns

- **Дробь (FRACTION)**: `40/2` → 40/1, 40/3
- **Дом без указания варианта (PLAIN)**: `40` → 40/1, 40/3

## Кима Ахмедьянова / base=72

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 357
- Available candidates: 72, 72/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `72` → 72/1

## Магнитогорская / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 367
- Available candidates: 30, 30/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `30` → 30/1

## Малика Якшимбетова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 369
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## Миллята Хакимова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 373
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## Мустая Карима / base=67

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 379
- Available candidates: 67, 67/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `67` → 67/1

## Рамазана Уметбаева / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 1, 1а, 1/2, 1/3

### Potential input patterns

- **Дробь (FRACTION)**: `1/1` → 1/2, 1/3
- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1/2, 1/3

## Рамазана Уметбаева / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 10, 10к3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `10` → 10к3

## Рамазана Уметбаева / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 17, 17/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `17` → 17/1

## Рамазана Уметбаева / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 19, 19/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `19` → 19/1

## Рамазана Уметбаева / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 23/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/1

## Рамазана Уметбаева / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 25, 25/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25/1

## Рамазана Уметбаева / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 27, 27/1, 27/2, 27/3

### Potential input patterns

- **Дробь (FRACTION)**: `27/4` → 27/1, 27/2, 27/3
- **Дом без указания варианта (PLAIN)**: `27` → 27/1, 27/2, 27/3

## Рамазана Уметбаева / base=29

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 386
- Available candidates: 29, 29/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `29` → 29/1

## Расуля Кужахметова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387
- Available candidates: 21, 21/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `21` → 21/1

## Расуля Кужахметова / base=26

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 387
- Available candidates: 26, 26А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `26` → 26А

## Сосновая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 398
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Фаттаха Ибрагимова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 409
- Available candidates: 1, 1А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1А

## Фахиры Гумеровой / base=8

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410
- Available candidates: 8, 8А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8А

## Фахиры Гумеровой / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410
- Available candidates: 35, 35/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `35` → 35/1

## Фахиры Гумеровой / base=38

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410
- Available candidates: 38Б

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `38` → 38Б

## Фахиры Гумеровой / base=39

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 410
- Available candidates: 39, 39/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `39` → 39/1

## Яныбая Хамматова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421
- Available candidates: 17, 17к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `17` → 17к1

## Яныбая Хамматова / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-1 (ID: 22)
- Street ID: 421
- Available candidates: 27, 27А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `27` → 27А

## 50 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334
- Available candidates: 1/1, 1/4, 1/5, 1/6, 1/7, 1/8

### Potential input patterns

- **Дробь (FRACTION)**: `1/2` → 1/1, 1/4, 1/5, 1/6, 1/7, 1/8
- **Дом без указания варианта (PLAIN)**: `1` → 1/1, 1/4, 1/5, 1/6, 1/7, 1/8

## 50 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334
- Available candidates: 2, 2/5, 2/7, 2/9

### Potential input patterns

- **Дробь (FRACTION)**: `2/1` → 2/5, 2/7, 2/9
- **Дом без указания варианта (PLAIN)**: `2` → 2/5, 2/7, 2/9

## 50 лет Победы / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 334
- Available candidates: 70, 70/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `70` → 70/1

## 65 лет Победы / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336
- Available candidates: 1, 1/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/2

## 65 лет Победы / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## 65 лет Победы / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336
- Available candidates: 19, 19/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `19` → 19/1

## 65 лет Победы / base=44

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336
- Available candidates: 44, 44/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `44` → 44/1

## 65 лет Победы / base=70

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 336
- Available candidates: 70, 70/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `70` → 70/1

## Ахмета Лутфуллина / base=13

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341
- Available candidates: 13, 13/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `13` → 13/1

## Ахмета Лутфуллина / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341
- Available candidates: 23/5

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/5

## Ахмета Лутфуллина / base=30

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 341
- Available candidates: 30, 30/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `30` → 30/1

## Бииш Батыра / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Бииш Батыра / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342
- Available candidates: 14, 14/1, 14/2, 14/3

### Potential input patterns

- **Дробь (FRACTION)**: `14/4` → 14/1, 14/2, 14/3
- **Дом без указания варианта (PLAIN)**: `14` → 14/1, 14/2, 14/3

## Бииш Батыра / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342
- Available candidates: 15, 15/1, 15/3

### Potential input patterns

- **Дробь (FRACTION)**: `15/2` → 15/1, 15/3
- **Дом без указания варианта (PLAIN)**: `15` → 15/1, 15/3

## Бииш Батыра / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342
- Available candidates: 16, 16а, 16/1, 16/2

### Potential input patterns

- **Дробь (FRACTION)**: `16/3` → 16/1, 16/2
- **Дом без указания варианта (PLAIN)**: `16` → 16а, 16/1, 16/2

## Бииш Батыра / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 342
- Available candidates: 17/2, 17/3

### Potential input patterns

- **Дробь (FRACTION)**: `17/1` → 17/2, 17/3
- **Дом без указания варианта (PLAIN)**: `17` → 17/2, 17/3

## Ишмурзы Хидиятова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 2, 2А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2А

## Ишмурзы Хидиятова / base=5

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 5, 5/1, 5/2, 5/3

### Potential input patterns

- **Дробь (FRACTION)**: `5/4` → 5/1, 5/2, 5/3
- **Дом без указания варианта (PLAIN)**: `5` → 5/1, 5/2, 5/3

## Ишмурзы Хидиятова / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 7, 7а, 7/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7а, 7/2

## Ишмурзы Хидиятова / base=9

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 9, 9/1, 9/3

### Potential input patterns

- **Дробь (FRACTION)**: `9/2` → 9/1, 9/3
- **Дом без указания варианта (PLAIN)**: `9` → 9/1, 9/3

## Ишмурзы Хидиятова / base=10

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 10, 10/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `10` → 10/1

## Ишмурзы Хидиятова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 15, 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## Ишмурзы Хидиятова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 18, 18/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `18` → 18/1

## Ишмурзы Хидиятова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 19, 19/1, 19/2

### Potential input patterns

- **Дробь (FRACTION)**: `19/3` → 19/1, 19/2
- **Дом без указания варианта (PLAIN)**: `19` → 19/1, 19/2

## Ишмурзы Хидиятова / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 23, 23/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/1

## Ишмурзы Хидиятова / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 25/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25/1

## Ишмурзы Хидиятова / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 355
- Available candidates: 35/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `35` → 35/1

## Курьятмас / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Курьятмас / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## Курьятмас / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363
- Available candidates: 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## Курьятмас / base=34

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363
- Available candidates: 34, 34/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `34` → 34/1

## Курьятмас / base=42

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 363
- Available candidates: 42/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `42` → 42/1

## Луговая / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 2, 2а, 2/1, 2/2, 2/3

### Potential input patterns

- **Дробь (FRACTION)**: `2/4` → 2/1, 2/2, 2/3
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2/1, 2/2, 2/3

## Луговая / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 3, 3/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3/1

## Луговая / base=4

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 4, 4/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4/2

## Луговая / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 14, 14/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14/1

## Луговая / base=25

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 25, 25/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25/1

## Луговая / base=49

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 49, 49а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `49` → 49а

## Луговая / base=54

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 366
- Available candidates: 54/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `54` → 54/2

## Минислама Мирсаяпова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374
- Available candidates: 1, 1/2, 1/3, 1/5

### Potential input patterns

- **Дробь (FRACTION)**: `1/1` → 1/2, 1/3, 1/5
- **Дом без указания варианта (PLAIN)**: `1` → 1/2, 1/3, 1/5

## Минислама Мирсаяпова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374
- Available candidates: 2/3, 2/7

### Potential input patterns

- **Дробь (FRACTION)**: `2/1` → 2/3, 2/7
- **Дом без указания варианта (PLAIN)**: `2` → 2/3, 2/7

## Минислама Мирсаяпова / base=31

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374
- Available candidates: 31, 31а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `31` → 31а

## Минислама Мирсаяпова / base=507

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 374
- Available candidates: 507к4

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `507` → 507к4

## Пятая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 384
- Available candidates: 1, 1/3, 1/7, 1/9

### Potential input patterns

- **Дробь (FRACTION)**: `1/1` → 1/3, 1/7, 1/9
- **Дом без указания варианта (PLAIN)**: `1` → 1/3, 1/7, 1/9

## Раиса Усманова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 1/1, 1/10, 1/2, 1/3, 1/6, 1/7, 1/9

### Potential input patterns

- **Дробь (FRACTION)**: `1/4` → 1/1, 1/10, 1/2, 1/3, 1/6, 1/7, 1/9
- **Дом без указания варианта (PLAIN)**: `1` → 1/1, 1/10, 1/2, 1/3, 1/6, 1/7, 1/9

## Раиса Усманова / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 2, 2/1, 2/10, 2/6

### Potential input patterns

- **Дробь (FRACTION)**: `2/2` → 2/1, 2/10, 2/6
- **Дом без указания варианта (PLAIN)**: `2` → 2/1, 2/10, 2/6

## Раиса Усманова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 15/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/2

## Раиса Усманова / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 16, 16/1, 16/3

### Potential input patterns

- **Дробь (FRACTION)**: `16/2` → 16/1, 16/3
- **Дом без указания варианта (PLAIN)**: `16` → 16/1, 16/3

## Раиса Усманова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 17, 17/1, 17/2

### Potential input patterns

- **Дробь (FRACTION)**: `17/3` → 17/1, 17/2
- **Дом без указания варианта (PLAIN)**: `17` → 17/1, 17/2

## Раиса Усманова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 385
- Available candidates: 18, 18/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `18` → 18/2

## Рафика Сальманова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389
- Available candidates: 1/3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/3

## Рафика Сальманова / base=81

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 389
- Available candidates: 81/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `81` → 81/1

## Садовая / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 1, 1а, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1/1

## Садовая / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 7/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7/1

## Садовая / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 14, 14/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14/1

## Садовая / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 16, 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## Садовая / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 19, 19/1, 19/2, 19/4

### Potential input patterns

- **Дробь (FRACTION)**: `19/3` → 19/1, 19/2, 19/4
- **Дом без указания варианта (PLAIN)**: `19` → 19/1, 19/2, 19/4

## Садовая / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 391
- Available candidates: 21, 21/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `21` → 21/2

## Сарии Миржановой / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 1, 1а, 1б, 1/2

### Potential input patterns

- **Литера у дома (LETTER)**: `1в` → 1а, 1б
- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1б, 1/2

## Сарии Миржановой / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 2, 2а, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2/1

## Сарии Миржановой / base=3

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 3/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3/1

## Сарии Миржановой / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## Сарии Миржановой / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 16, 16/1, 16/2, 16/3

### Potential input patterns

- **Дробь (FRACTION)**: `16/4` → 16/1, 16/2, 16/3
- **Дом без указания варианта (PLAIN)**: `16` → 16/1, 16/2, 16/3

## Сарии Миржановой / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 17, 17/2, 17/3

### Potential input patterns

- **Дробь (FRACTION)**: `17/1` → 17/2, 17/3
- **Дом без указания варианта (PLAIN)**: `17` → 17/2, 17/3

## Сарии Миржановой / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 18/1, 18/2

### Potential input patterns

- **Дробь (FRACTION)**: `18/3` → 18/1, 18/2
- **Дом без указания варианта (PLAIN)**: `18` → 18/1, 18/2

## Сарии Миржановой / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 394
- Available candidates: 50, 50/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `50` → 50/1

## Солнечная / base=7

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397
- Available candidates: 7/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7/1

## Солнечная / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397
- Available candidates: 17/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `17` → 17/1

## Солнечная / base=50

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 397
- Available candidates: 50, 50/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `50` → 50/1

## Тамьян / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Тамьян / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 2/1, 2/2

### Potential input patterns

- **Дробь (FRACTION)**: `2/3` → 2/1, 2/2
- **Дом без указания варианта (PLAIN)**: `2` → 2/1, 2/2

## Тамьян / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 16/1, 16/2

### Potential input patterns

- **Дробь (FRACTION)**: `16/3` → 16/1, 16/2
- **Дом без указания варианта (PLAIN)**: `16` → 16/1, 16/2

## Тамьян / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 17, 17/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `17` → 17/1

## Тамьян / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 18, 18/1, 18/2, 18/3

### Potential input patterns

- **Дробь (FRACTION)**: `18/4` → 18/1, 18/2, 18/3
- **Дом без указания варианта (PLAIN)**: `18` → 18/1, 18/2, 18/3

## Тамьян / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 401
- Available candidates: 20, 20/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20/1

## Тунгаур / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 1, 1/1, 1/2, 1/3

### Potential input patterns

- **Дробь (FRACTION)**: `1/4` → 1/1, 1/2, 1/3
- **Дом без указания варианта (PLAIN)**: `1` → 1/1, 1/2, 1/3

## Тунгаур / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 2/1, 2/11, 2/3, 2/4, 2/5, 2/7

### Potential input patterns

- **Дробь (FRACTION)**: `2/2` → 2/1, 2/11, 2/3, 2/4, 2/5, 2/7
- **Дом без указания варианта (PLAIN)**: `2` → 2/1, 2/11, 2/3, 2/4, 2/5, 2/7

## Тунгаур / base=14

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 14, 14/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14/1

## Тунгаур / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 15, 15/1, 15/2, 15/3

### Potential input patterns

- **Дробь (FRACTION)**: `15/4` → 15/1, 15/2, 15/3
- **Дом без указания варианта (PLAIN)**: `15` → 15/1, 15/2, 15/3

## Тунгаур / base=16

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 16/1, 16/3

### Potential input patterns

- **Дробь (FRACTION)**: `16/2` → 16/1, 16/3
- **Дом без указания варианта (PLAIN)**: `16` → 16/1, 16/3

## Тунгаур / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 17, 17/1, 17/2

### Potential input patterns

- **Дробь (FRACTION)**: `17/3` → 17/1, 17/2
- **Дом без указания варианта (PLAIN)**: `17` → 17/1, 17/2

## Тунгаур / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 18/1, 18/2

### Potential input patterns

- **Дробь (FRACTION)**: `18/3` → 18/1, 18/2
- **Дом без указания варианта (PLAIN)**: `18` → 18/1, 18/2

## Тунгаур / base=23

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 23, 23/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/1

## Тунгаур / base=35

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 403
- Available candidates: 35, 35/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `35` → 35/1

## Файзи Гаскарова / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 1, 1А, 1/1, 1/2

### Potential input patterns

- **Дробь (FRACTION)**: `1/3` → 1/1, 1/2
- **Дом без указания варианта (PLAIN)**: `1` → 1А, 1/1, 1/2

## Файзи Гаскарова / base=15

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 15, 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## Файзи Гаскарова / base=17

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 17/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `17` → 17/1

## Файзи Гаскарова / base=18

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 18, 18/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `18` → 18/1

## Файзи Гаскарова / base=19

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 19, 19/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `19` → 19/2

## Файзи Гаскарова / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 20, 20/3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20/3

## Файзи Гаскарова / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 21, 21/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `21` → 21/1

## Файзи Гаскарова / base=57

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 407
- Available candidates: 57, 57/1, 57/4

### Potential input patterns

- **Дробь (FRACTION)**: `57/2` → 57/1, 57/4
- **Дом без указания варианта (PLAIN)**: `57` → 57/1, 57/4

## Хадии Давлетшиной / base=27

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411
- Available candidates: 27, 27/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `27` → 27/2

## Хадии Давлетшиной / base=46

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 411
- Available candidates: 46, 46/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `46` → 46/1

## Целинная / base=1

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412
- Available candidates: 1а, 1/4, 1/6, 1/7, 1/8, 1/9

### Potential input patterns

- **Дробь (FRACTION)**: `1/1` → 1/4, 1/6, 1/7, 1/8, 1/9
- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1/4, 1/6, 1/7, 1/8, 1/9

## Целинная / base=2

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412
- Available candidates: 2, 2/4, 2/5, 2/7, 2/8

### Potential input patterns

- **Дробь (FRACTION)**: `2/1` → 2/4, 2/5, 2/7, 2/8
- **Дом без указания варианта (PLAIN)**: `2` → 2/4, 2/5, 2/7, 2/8

## Целинная / base=20

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412
- Available candidates: 20/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20/1

## Целинная / base=21

- Town: Аскарово (ID: 4)
- District: Восточный-2 (ID: 21)
- Street ID: 412
- Available candidates: 21, 21А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `21` → 21А

## Ахмет Заки Валиди / base=19

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 340
- Available candidates: 19, 19/3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `19` → 19/3

## Урал Батыра / base=2

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## Урал Батыра / base=20

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 20/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20/1

## Урал Батыра / base=21

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 21, 21к4, 21к5, 21/1, 21/2

### Potential input patterns

- **Корпус (CORPUS)**: `21к1` → 21к4, 21к5
- **Дробь (FRACTION)**: `21/3` → 21/1, 21/2
- **Дом без указания варианта (PLAIN)**: `21` → 21к4, 21к5, 21/1, 21/2

## Урал Батыра / base=23

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 23, 23к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23к1

## Урал Батыра / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 28, 28к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `28` → 28к1

## Урал Батыра / base=30

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 30, 30к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `30` → 30к1

## Урал Батыра / base=39

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 404
- Available candidates: 39, 39А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `39` → 39А

## Файзрахмана Хисматуллина / base=62

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 408
- Available candidates: 62, 62к2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `62` → 62к2

## Шагали Шакмана / base=1

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 415
- Available candidates: 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Шагали Шакмана / base=16

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 415
- Available candidates: 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## Шайхзады Бабича / base=28

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417
- Available candidates: 28, 28/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `28` → 28/1

## Шайхзады Бабича / base=43

- Town: Аскарово (ID: 4)
- District: Северный (ID: 23)
- Street ID: 417
- Available candidates: 43, 43/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `43` → 43/1

## Гагарина / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Гагарина / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 345
- Available candidates: 2а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2а

## Горная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 1, 1а, 1б

### Potential input patterns

- **Литера у дома (LETTER)**: `1в` → 1а, 1б
- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1б

## Горная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 2, 2а, 2б, 2В, 2/1

### Potential input patterns

- **Литера у дома (LETTER)**: `2в` → 2В, 2а, 2б
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б, 2В, 2/1

## Горная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 3, 3А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3А

## Горная / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 8, 8а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8а

## Горная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 13, 13А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `13` → 13А

## Горная / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 21, 21А, 21Б

### Potential input patterns

- **Литера у дома (LETTER)**: `21а` → 21А, 21Б
- **Дом без указания варианта (PLAIN)**: `21` → 21А, 21Б

## Горная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 43, 43а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `43` → 43а

## Горная / base=47

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 47а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `47` → 47а

## Горная / base=50

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 347
- Available candidates: 50, 50а, 50б

### Potential input patterns

- **Литера у дома (LETTER)**: `50в` → 50а, 50б
- **Дом без указания варианта (PLAIN)**: `50` → 50а, 50б

## Кирова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 358
- Available candidates: 5, 5а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `5` → 5а

## Колхозная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 359
- Available candidates: 2, 2а, 2б

### Potential input patterns

- **Литера у дома (LETTER)**: `2в` → 2а, 2б
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б

## Комарова / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360
- Available candidates: 1, 1к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1к1

## Комарова / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360
- Available candidates: 2, 2к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2к1

## Комарова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360
- Available candidates: 5, 5к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `5` → 5к1

## Комарова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360
- Available candidates: 6, 6а, 6к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `6` → 6а, 6к1

## Комарова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 360
- Available candidates: 7, 7А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7А

## Коммунистическая / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 1, 1а, 1Б, 1к1, 1к2, 1к3, 1к4, 1к5, 1к6

### Potential input patterns

- **Корпус (CORPUS)**: `1к7` → 1к1, 1к2, 1к3, 1к4, 1к5, 1к6
- **Литера у дома (LETTER)**: `1б` → 1Б, 1а
- **Дом без указания варианта (PLAIN)**: `1` → 1а, 1Б, 1к1, 1к2, 1к3, 1к4, 1к5, 1к6

## Коммунистическая / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 2, 2а, 2б, 2к1, 2к2, 2к3, 2к5, 2/4

### Potential input patterns

- **Корпус (CORPUS)**: `2к4` → 2к1, 2к2, 2к3, 2к5
- **Литера у дома (LETTER)**: `2в` → 2а, 2б
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б, 2к1, 2к2, 2к3, 2к5, 2/4

## Коммунистическая / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 8, 8а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8а

## Коммунистическая / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 11, 11/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11/1

## Коммунистическая / base=21

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 21, 21б, 21в, 21к4, 21/2, 21/3

### Potential input patterns

- **Дробь (FRACTION)**: `21/1` → 21/2, 21/3
- **Литера у дома (LETTER)**: `21а` → 21б, 21в
- **Дом без указания варианта (PLAIN)**: `21` → 21б, 21в, 21к4, 21/2, 21/3

## Коммунистическая / base=22

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 22, 22/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `22` → 22/1

## Коммунистическая / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 25, 25А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25А

## Коммунистическая / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 28/1, 28/3

### Potential input patterns

- **Дробь (FRACTION)**: `28/2` → 28/1, 28/3
- **Дом без указания варианта (PLAIN)**: `28` → 28/1, 28/3

## Коммунистическая / base=32

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 32, 32/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `32` → 32/1

## Коммунистическая / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 361
- Available candidates: 38, 38/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `38` → 38/1

## Комсомольская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 362
- Available candidates: 4, 4А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4А

## Ленина / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 2, 2а, 2б, 2в, 2/1

### Potential input patterns

- **Литера у дома (LETTER)**: `2г` → 2а, 2б, 2в
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б, 2в, 2/1

## Ленина / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 4, 4а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4а

## Ленина / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 14, 14к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14к1

## Ленина / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## Ленина / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 29/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `29` → 29/1

## Ленина / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 38, 38/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `38` → 38/1

## Ленина / base=51

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 51, 51А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `51` → 51А

## Ленина / base=52

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 52, 52к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `52` → 52к1

## Ленина / base=127

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 127, 127/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `127` → 127/1

## Ленина / base=141

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 141к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `141` → 141к1

## Ленина / base=155

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 364
- Available candidates: 155/1, 155/2

### Potential input patterns

- **Дробь (FRACTION)**: `155/3` → 155/1, 155/2
- **Дом без указания варианта (PLAIN)**: `155` → 155/1, 155/2

## Матросова / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 3, 3а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3а

## Матросова / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 5, 5а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `5` → 5а

## Матросова / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 7, 7/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7/1

## Матросова / base=9

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 9а, 9Б

### Potential input patterns

- **Литера у дома (LETTER)**: `9б` → 9Б, 9а
- **Дом без указания варианта (PLAIN)**: `9` → 9а, 9Б

## Матросова / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 10/1, 10/2

### Potential input patterns

- **Дробь (FRACTION)**: `10/3` → 10/1, 10/2
- **Дом без указания варианта (PLAIN)**: `10` → 10/1, 10/2

## Матросова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 370
- Available candidates: 14, 14/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14/1

## Мира / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Мира / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 2а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2а

## Мира / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 3, 3/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3/1

## Мира / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 4/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4/1

## Мира / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 6/1, 6/2

### Potential input patterns

- **Дробь (FRACTION)**: `6/3` → 6/1, 6/2
- **Дом без указания варианта (PLAIN)**: `6` → 6/1, 6/2

## Мира / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 10/1, 10/2

### Potential input patterns

- **Дробь (FRACTION)**: `10/3` → 10/1, 10/2
- **Дом без указания варианта (PLAIN)**: `10` → 10/1, 10/2

## Мира / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 11, 11а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11а

## Мира / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 12/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `12` → 12/2

## Мира / base=15

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 15, 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## Мира / base=27

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 27, 27/1, 27/2

### Potential input patterns

- **Дробь (FRACTION)**: `27/3` → 27/1, 27/2
- **Дом без указания варианта (PLAIN)**: `27` → 27/1, 27/2

## Мира / base=29

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 29, 29/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `29` → 29/1

## Мира / base=31

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 375
- Available candidates: 31, 31/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `31` → 31/1

## Молодежная / base=7

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 7, 7а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7а

## Молодежная / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 10, 10а, 10б, 10/1

### Potential input patterns

- **Литера у дома (LETTER)**: `10в` → 10а, 10б
- **Дом без указания варианта (PLAIN)**: `10` → 10а, 10б, 10/1

## Молодежная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 12, 12а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `12` → 12а

## Молодежная / base=13

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 13, 13/3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `13` → 13/3

## Молодежная / base=20

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 20, 20б

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `20` → 20б

## Молодежная / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 24, 24а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `24` → 24а

## Молодежная / base=25

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 25, 25а, 25к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `25` → 25а, 25к1

## Молодежная / base=28

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 28, 28к3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `28` → 28к3

## Молодежная / base=30

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 30, 30/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `30` → 30/1

## Молодежная / base=36

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 36, 36/2, 36/3

### Potential input patterns

- **Дробь (FRACTION)**: `36/1` → 36/2, 36/3
- **Дом без указания варианта (PLAIN)**: `36` → 36/2, 36/3

## Молодежная / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 39, 39А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `39` → 39А

## Молодежная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 41, 41а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `41` → 41а

## Молодежная / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 376
- Available candidates: 57, 57а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `57` → 57а

## Партизанская / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381
- Available candidates: 6, 6А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `6` → 6А

## Партизанская / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381
- Available candidates: 14, 14а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14а

## Партизанская / base=24

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381
- Available candidates: 24, 24/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `24` → 24/2

## Партизанская / base=57

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381
- Available candidates: 57, 57а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `57` → 57а

## Партизанская / base=59

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 381
- Available candidates: 59Б

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `59` → 59Б

## Салавата Юлаева / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 2, 2а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2а

## Салавата Юлаева / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 8, 8/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8/1

## Салавата Юлаева / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 12, 12а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `12` → 12а

## Салавата Юлаева / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 33, 33а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `33` → 33а

## Салавата Юлаева / base=38

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 38, 38А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `38` → 38А

## Салавата Юлаева / base=46

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 46, 46/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `46` → 46/1

## Салавата Юлаева / base=65

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 393
- Available candidates: 65а, 65/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `65` → 65а, 65/1

## Советская / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 396
- Available candidates: 4А, 4Б

### Potential input patterns

- **Литера у дома (LETTER)**: `4а` → 4А, 4Б
- **Дом без указания варианта (PLAIN)**: `4` → 4А, 4Б

## Тангатарская / base=5

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 5, 5а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `5` → 5а

## Тангатарская / base=8

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 8к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8к1

## Тангатарская / base=10

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 10, 10к2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `10` → 10к2

## Тангатарская / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 12/1, 12/2

### Potential input patterns

- **Дробь (FRACTION)**: `12/3` → 12/1, 12/2
- **Дом без указания варианта (PLAIN)**: `12` → 12/1, 12/2

## Тангатарская / base=34

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 34, 34А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `34` → 34А

## Тангатарская / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 39, 39/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `39` → 39/1

## Тангатарская / base=49

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 402
- Available candidates: 49/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `49` → 49/1

## Учалинская / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406
- Available candidates: 3, 3/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3/1

## Учалинская / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406
- Available candidates: 16, 16к1, 16/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16к1, 16/2

## Учалинская / base=18

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 406
- Available candidates: 18, 18а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `18` → 18а

## Шаймуратова / base=4

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 4, 4/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4/1

## Шаймуратова / base=6

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 6/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `6` → 6/1

## Шаймуратова / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 12, 12а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `12` → 12а

## Шаймуратова / base=14

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 14, 14/1, 14/2

### Potential input patterns

- **Дробь (FRACTION)**: `14/3` → 14/1, 14/2
- **Дом без указания варианта (PLAIN)**: `14` → 14/1, 14/2

## Шаймуратова / base=16

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 16, 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## Шаймуратова / base=39

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 39а, 39Б

### Potential input patterns

- **Литера у дома (LETTER)**: `39б` → 39Б, 39а
- **Дом без указания варианта (PLAIN)**: `39` → 39а, 39Б

## Шаймуратова / base=53

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 53, 53к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `53` → 53к1

## Шаймуратова / base=55

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 55, 55/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `55` → 55/1

## Шаймуратова / base=86

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 416
- Available candidates: 86, 86/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `86` → 86/1

## Юбилейная / base=1

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Юбилейная / base=3

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 3, 3а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3а

## Юбилейная / base=12

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 12/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `12` → 12/1

## Юбилейная / base=23

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 23, 23/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/1

## Юбилейная / base=33

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 33, 33а, 33б, 33В, 33к1, 33к2, 33к4

### Potential input patterns

- **Корпус (CORPUS)**: `33к3` → 33к1, 33к2, 33к4
- **Литера у дома (LETTER)**: `33в` → 33В, 33а, 33б
- **Дом без указания варианта (PLAIN)**: `33` → 33а, 33б, 33В, 33к1, 33к2, 33к4

## Юбилейная / base=35

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 35, 35/1, 35/2, 35/3, 35/4

### Potential input patterns

- **Дробь (FRACTION)**: `35/5` → 35/1, 35/2, 35/3, 35/4
- **Дом без указания варианта (PLAIN)**: `35` → 35/1, 35/2, 35/3, 35/4

## Юбилейная / base=41

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 41/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `41` → 41/2

## Юбилейная / base=43

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 419
- Available candidates: 43/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `43` → 43/1

## Южная / base=2

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420
- Available candidates: 2, 2а, 2б

### Potential input patterns

- **Литера у дома (LETTER)**: `2в` → 2а, 2б
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б

## Южная / base=11

- Town: Аскарово (ID: 4)
- District: Центр (ID: 19)
- Street ID: 420
- Available candidates: 11А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11А

## 40 лет Победы / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333
- Available candidates: 16, 16/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/1

## 40 лет Победы / base=49

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 333
- Available candidates: 49, 49/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `49` → 49/2

## 70 лет Октября / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 15, 15/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `15` → 15/1

## 70 лет Октября / base=17

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 17, 17к1, 17к2, 17к3, 17к4

### Potential input patterns

- **Корпус (CORPUS)**: `17к5` → 17к1, 17к2, 17к3, 17к4
- **Дом без указания варианта (PLAIN)**: `17` → 17к1, 17к2, 17к3, 17к4

## 70 лет Октября / base=19

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 19, 19к1, 19к2, 19к3

### Potential input patterns

- **Корпус (CORPUS)**: `19к4` → 19к1, 19к2, 19к3
- **Дом без указания варианта (PLAIN)**: `19` → 19к1, 19к2, 19к3

## 70 лет Октября / base=22

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 22, 22/1, 22/2

### Potential input patterns

- **Дробь (FRACTION)**: `22/3` → 22/1, 22/2
- **Дом без указания варианта (PLAIN)**: `22` → 22/1, 22/2

## 70 лет Октября / base=51

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 51, 51к2, 51к3, 51к4, 51к5, 51/1

### Potential input patterns

- **Корпус (CORPUS)**: `51к1` → 51к2, 51к3, 51к4, 51к5
- **Дом без указания варианта (PLAIN)**: `51` → 51к2, 51к3, 51к4, 51к5, 51/1

## 70 лет Октября / base=53

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 337
- Available candidates: 53, 53к1, 53к2, 53к3

### Potential input patterns

- **Корпус (CORPUS)**: `53к4` → 53к1, 53к2, 53к3
- **Дом без указания варианта (PLAIN)**: `53` → 53к1, 53к2, 53к3

## Дружбы / base=11

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348
- Available candidates: 11, 11к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `11` → 11к1

## Дружбы / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348
- Available candidates: 23, 23А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23А

## Дружбы / base=35

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 348
- Available candidates: 35/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `35` → 35/1

## Идяш / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352
- Available candidates: 45, 45/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `45` → 45/1

## Идяш / base=86

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 352
- Available candidates: 86А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `86` → 86А

## Мажита Гафури / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 368
- Available candidates: 1, 1/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1/1

## Мелиораторов / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371
- Available candidates: 6, 6к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `6` → 6к1

## Мелиораторов / base=7

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371
- Available candidates: 7, 7а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `7` → 7а

## Мелиораторов / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 371
- Available candidates: 8, 8к1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8к1

## Пионерская / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383
- Available candidates: 2, 2А, 2/1, 2/3

### Potential input patterns

- **Дробь (FRACTION)**: `2/2` → 2/1, 2/3
- **Дом без указания варианта (PLAIN)**: `2` → 2А, 2/1, 2/3

## Пионерская / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383
- Available candidates: 4/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4/1

## Пионерская / base=18

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 383
- Available candidates: 18/1, 18/2

### Potential input patterns

- **Дробь (FRACTION)**: `18/3` → 18/1, 18/2
- **Дом без указания варианта (PLAIN)**: `18` → 18/1, 18/2

## Рауфа Давлетова / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 1, 1к3, 1к4, 1/2, 1/7

### Potential input patterns

- **Корпус (CORPUS)**: `1к1` → 1к3, 1к4
- **Дробь (FRACTION)**: `1/1` → 1/2, 1/7
- **Дом без указания варианта (PLAIN)**: `1` → 1к3, 1к4, 1/2, 1/7

## Рауфа Давлетова / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 2, 2а, 2б, 2/1

### Potential input patterns

- **Литера у дома (LETTER)**: `2в` → 2а, 2б
- **Дом без указания варианта (PLAIN)**: `2` → 2а, 2б, 2/1

## Рауфа Давлетова / base=4

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 4, 4/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `4` → 4/1

## Рауфа Давлетова / base=6

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 6, 6/2, 6/3

### Potential input patterns

- **Дробь (FRACTION)**: `6/1` → 6/2, 6/3
- **Дом без указания варианта (PLAIN)**: `6` → 6/2, 6/3

## Рауфа Давлетова / base=8

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 8/4

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `8` → 8/4

## Рауфа Давлетова / base=10

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 10/1, 10/3, 10/4

### Potential input patterns

- **Дробь (FRACTION)**: `10/2` → 10/1, 10/3, 10/4
- **Дом без указания варианта (PLAIN)**: `10` → 10/1, 10/3, 10/4

## Рауфа Давлетова / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 14/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `14` → 14/1

## Рауфа Давлетова / base=15

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 15, 15/1, 15/2

### Potential input patterns

- **Дробь (FRACTION)**: `15/3` → 15/1, 15/2
- **Дом без указания варианта (PLAIN)**: `15` → 15/1, 15/2

## Рауфа Давлетова / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 388
- Available candidates: 16/3

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `16` → 16/3

## Рихарда Зорге / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 2, 2/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2/1

## Рихарда Зорге / base=9

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 9, 9/1, 9/2, 9/3, 9/5

### Potential input patterns

- **Дробь (FRACTION)**: `9/4` → 9/1, 9/2, 9/3, 9/5
- **Дом без указания варианта (PLAIN)**: `9` → 9/1, 9/2, 9/3, 9/5

## Рихарда Зорге / base=14

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 14/1, 14/2

### Potential input patterns

- **Дробь (FRACTION)**: `14/3` → 14/1, 14/2
- **Дом без указания варианта (PLAIN)**: `14` → 14/1, 14/2

## Рихарда Зорге / base=16

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 16, 16а, 16/1, 16/2

### Potential input patterns

- **Дробь (FRACTION)**: `16/3` → 16/1, 16/2
- **Дом без указания варианта (PLAIN)**: `16` → 16а, 16/1, 16/2

## Рихарда Зорге / base=24

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 24, 24А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `24` → 24А

## Рихарда Зорге / base=37

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 37, 37а, 37Б, 37/1

### Potential input patterns

- **Литера у дома (LETTER)**: `37б` → 37Б, 37а
- **Дом без указания варианта (PLAIN)**: `37` → 37а, 37Б, 37/1

## Рихарда Зорге / base=45

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 45, 45/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `45` → 45/1

## Рихарда Зорге / base=52

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 390
- Available candidates: 52, 52А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `52` → 52А

## Строителей / base=1

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399
- Available candidates: 1, 1а

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `1` → 1а

## Строителей / base=2

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399
- Available candidates: 2, 2А

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `2` → 2А

## Строителей / base=3

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399
- Available candidates: 3/2

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `3` → 3/2

## Строителей / base=23

- Town: Аскарово (ID: 4)
- District: Южный (ID: 20)
- Street ID: 399
- Available candidates: 23, 23/1

### Potential input patterns

- **Дом без указания варианта (PLAIN)**: `23` → 23/1

---

# Landmarks

Landmark может существовать без улицы/дома (это разрешено ORM: ``street_id`` nullable, ``house_id`` nullable) — в таких случаях вместо данных ставится «—».

Всего ориентиров: **3**.

## Landmark: Нижний Магнит

- ID: 7
- Street: Сафи Истамгалина (ID: 439)
- House: 31 (ID: 10094)
- District: Восточный-1 (ID: 22)
- Town: Аскарово (ID: 4)
- Description: —

## Landmark: Районная больница

- ID: 4
- Street: Гагарина (ID: 345)
- House: 5 (ID: 7218)
- District: Центр (ID: 19)
- Town: Аскарово (ID: 4)
- Description: —

## Landmark: Больница

- ID: 3
- Street: Ленина (ID: 364)
- House: 13 (ID: 7939)
- District: Центр (ID: 19)
- Town: Аскарово (ID: 4)
- Description: —

---

# Address Hierarchy

## Ожидаемая иерархия

```
Town
 └── District
      └── Street
           └── House

Town
 └── District
      └── Street
           └── Landmark
```

## Фактическая иерархия (по данным БД)

### Town: Аскарово (ID: 4) — районов: 6

└── District: Восточный-1 (ID: 22) — улиц: 28, домов: 719, ориентиров: 1
    └── Street: 60 лет Победы (ID: 335) — домов: 76, ориентиров: 0
    └── Street: Абзелиловская (ID: 338) — домов: 18, ориентиров: 0
    └── Street: Вафира Тайсина (ID: 343) — домов: 21, ориентиров: 0
    └── Street: Весенняя (ID: 344) — домов: 1, ориентиров: 0
    └── Street: Гинията Ушанова (ID: 346) — домов: 41, ориентиров: 0
    └── Street: Емельяна Пугачева (ID: 349) — домов: 11, ориентиров: 0
    └── Street: Емельяна Пугачёва (ID: 437) — домов: 0, ориентиров: 0
    └── Street: Загира Исмагилова (ID: 350) — домов: 35, ориентиров: 0
    └── Street: Зайнаб Биишевой (ID: 351) — домов: 22, ориентиров: 0
    └── Street: Ишмухамета Мырзакаева (ID: 356) — домов: 51, ориентиров: 0
    └── Street: Кима Ахмедьянова (ID: 357) — домов: 72, ориентиров: 0
    └── Street: Ленина (ID: 422) — домов: 2, ориентиров: 0
    └── Street: Магнитогорская (ID: 367) — домов: 21, ориентиров: 0
    └── Street: Малика Якшимбетова (ID: 369) — домов: 24, ориентиров: 0
    └── Street: Миллята Хакимова (ID: 373) — домов: 34, ориентиров: 0
    └── Street: Миптата Хакимова (ID: 438) — домов: 0, ориентиров: 0
    └── Street: Мустая Карима (ID: 379) — домов: 61, ориентиров: 0
    └── Street: Николая Гоголя (ID: 436) — домов: 0, ориентиров: 0
    └── Street: Рамазана Уметбаева (ID: 386) — домов: 40, ориентиров: 0
    └── Street: Расуля Кужахметова (ID: 387) — домов: 41, ориентиров: 0
    └── Street: Сафи Истамгалина (ID: 439) — домов: 1, ориентиров: 1
    └── Street: Сафы Истамгалина (ID: 395) — домов: 28, ориентиров: 0
    └── Street: Сосновая (ID: 398) — домов: 13, ориентиров: 0
    └── Street: Фаттаха Ибрагимова (ID: 409) — домов: 41, ориентиров: 0
    └── Street: Фахиры Гумеровой (ID: 410) — домов: 44, ориентиров: 0
    └── Street: Шаймуратова (ID: 440) — домов: 0, ориентиров: 0
    └── Street: Юности (ID: 435) — домов: 0, ориентиров: 0
    └── Street: Яныбая Хамматова (ID: 421) — домов: 21, ориентиров: 0
└── District: Восточный-2 (ID: 21) — улиц: 33, домов: 997, ориентиров: 0
    └── Street: 50 лет Победы (ID: 334) — домов: 63, ориентиров: 0
    └── Street: 65 лет Победы (ID: 336) — домов: 47, ориентиров: 0
    └── Street: Ахмета Лутфуллина (ID: 341) — домов: 33, ориентиров: 0
    └── Street: Бииш Батыра (ID: 342) — домов: 55, ориентиров: 0
    └── Street: Валиахмета Сулейманова (ID: 450) — домов: 0, ориентиров: 0
    └── Street: Индиры Султанбаевой (ID: 451) — домов: 0, ориентиров: 0
    └── Street: Иншара Султанбаева (ID: 353) — домов: 5, ориентиров: 0
    └── Street: Ишмурзы Хидиятова (ID: 355) — домов: 65, ориентиров: 0
    └── Street: Курчатова (ID: 445) — домов: 0, ориентиров: 0
    └── Street: Курьятмас (ID: 363) — домов: 39, ориентиров: 0
    └── Street: Луговая (ID: 366) — домов: 41, ориентиров: 0
    └── Street: Минислама Мирсаяпова (ID: 374) — домов: 61, ориентиров: 0
    └── Street: Мисаля Муртасина (ID: 452) — домов: 0, ориентиров: 0
    └── Street: Мурзахана Шамсутдинова (ID: 378) — домов: 8, ориентиров: 0
    └── Street: Нажипа Асанбаева (ID: 448) — домов: 0, ориентиров: 0
    └── Street: Пятая (ID: 384) — домов: 32, ориентиров: 0
    └── Street: Раиса Усманова (ID: 385) — домов: 52, ориентиров: 0
    └── Street: Рамазана Уметбаева (ID: 443) — домов: 0, ориентиров: 0
    └── Street: Рами Гарипова (ID: 449) — домов: 0, ориентиров: 0
    └── Street: Рафика Сальманова (ID: 389) — домов: 62, ориентиров: 0
    └── Street: Сагиры Мишар (ID: 446) — домов: 0, ориентиров: 0
    └── Street: Садовая (ID: 391) — домов: 52, ориентиров: 0
    └── Street: Салавата Кадырова (ID: 392) — домов: 2, ориентиров: 0
    └── Street: Сарии Миржановой (ID: 394) — домов: 57, ориентиров: 0
    └── Street: Солнечная (ID: 397) — домов: 36, ориентиров: 0
    └── Street: Тамьян (ID: 401) — домов: 43, ориентиров: 0
    └── Street: Тукая (ID: 447) — домов: 0, ориентиров: 0
    └── Street: Тунгаур (ID: 403) — домов: 58, ориентиров: 0
    └── Street: Фазиля Искандера (ID: 444) — домов: 0, ориентиров: 0
    └── Street: Файзи Гаскарова (ID: 407) — домов: 63, ориентиров: 0
    └── Street: Хадии Давлетшиной (ID: 411) — домов: 67, ориентиров: 0
    └── Street: Целинная (ID: 412) — домов: 56, ориентиров: 0
    └── Street: Шаймуратова (ID: 442) — домов: 0, ориентиров: 0
└── District: Даутово (ID: 24) — улиц: 26, домов: 13, ориентиров: 0
    └── Street: 10 лет Победы (ID: 454) — домов: 0, ориентиров: 0
    └── Street: 60 лет Победы (ID: 455) — домов: 0, ориентиров: 0
    └── Street: 8 Марта (ID: 453) — домов: 0, ориентиров: 0
    └── Street: Абзелиловская (ID: 456) — домов: 0, ориентиров: 0
    └── Street: Александра Пушкина (ID: 457) — домов: 0, ориентиров: 0
    └── Street: Гайфуллы Сарбаева (ID: 458) — домов: 0, ориентиров: 0
    └── Street: Георгия Васева (ID: 459) — домов: 0, ориентиров: 0
    └── Street: Караташ (ID: 460) — домов: 0, ориентиров: 0
    └── Street: Кизильская (ID: 461) — домов: 0, ориентиров: 0
    └── Street: Кинзи Арсланова (ID: 462) — домов: 0, ориентиров: 0
    └── Street: Кыркты-Тау (ID: 463) — домов: 0, ориентиров: 0
    └── Street: Михаила Лермонтова (ID: 464) — домов: 0, ориентиров: 0
    └── Street: Мусы Гареева (ID: 380) — домов: 13, ориентиров: 0
    └── Street: Мусы Джалиля (ID: 465) — домов: 0, ориентиров: 0
    └── Street: Нургали Фахретдинова (ID: 466) — домов: 0, ориентиров: 0
    └── Street: Рауфа Давлетова (ID: 467) — домов: 0, ориентиров: 0
    └── Street: Сагиды Бердиной (ID: 468) — домов: 0, ориентиров: 0
    └── Street: Салавата Юлаева (ID: 469) — домов: 0, ориентиров: 0
    └── Street: Салимьяна Гайнуллина (ID: 470) — домов: 0, ориентиров: 0
    └── Street: Саляха Кулибая (ID: 471) — домов: 0, ориентиров: 0
    └── Street: Северная (ID: 472) — домов: 0, ориентиров: 0
    └── Street: Сергея Аксакова (ID: 473) — домов: 0, ориентиров: 0
    └── Street: Сергея Есенина (ID: 474) — домов: 0, ориентиров: 0
    └── Street: Центральная (ID: 475) — домов: 0, ориентиров: 0
    └── Street: Шакира Биккулова (ID: 476) — домов: 0, ориентиров: 0
    └── Street: Школьная (ID: 477) — домов: 0, ориентиров: 0
└── District: Северный (ID: 23) — улиц: 14, домов: 220, ориентиров: 0
    └── Street: Ак Кайын (ID: 339) — домов: 6, ориентиров: 0
    └── Street: Ак-Күлгин (ID: 425) — домов: 0, ориентиров: 0
    └── Street: Ахмет Заки Валиди (ID: 340) — домов: 32, ориентиров: 0
    └── Street: Комарова (ID: 428) — домов: 0, ориентиров: 0
    └── Street: Ленина (ID: 423) — домов: 1, ориентиров: 0
    └── Street: Любимая (ID: 427) — домов: 0, ориентиров: 0
    └── Street: Урал Батыра (ID: 404) — домов: 54, ориентиров: 0
    └── Street: Уральская (ID: 405) — домов: 5, ориентиров: 0
    └── Street: Файзрахмана Мустафина (ID: 424) — домов: 0, ориентиров: 0
    └── Street: Файзрахмана Хисматуллина (ID: 408) — домов: 61, ориентиров: 0
    └── Street: Шагали Шакман (ID: 414) — домов: 12, ориентиров: 0
    └── Street: Шагали Шакмана (ID: 415) — домов: 3, ориентиров: 0
    └── Street: Шайхзады Бабича (ID: 417) — домов: 46, ориентиров: 0
    └── Street: Шакимана (ID: 426) — домов: 0, ориентиров: 0
└── District: Центр (ID: 19) — улиц: 24, домов: 905, ориентиров: 2
    └── Street: 40 лет Октября (ID: 332) — домов: 5, ориентиров: 0
    └── Street: Гагарина (ID: 345) — домов: 11, ориентиров: 1
    └── Street: Горная (ID: 347) — домов: 67, ориентиров: 0
    └── Street: Кирова (ID: 358) — домов: 21, ориентиров: 0
    └── Street: Колхозная (ID: 359) — домов: 51, ориентиров: 0
    └── Street: Комарова (ID: 360) — домов: 29, ориентиров: 0
    └── Street: Коммунистическая (ID: 361) — домов: 60, ориентиров: 0
    └── Street: Комсомольская (ID: 362) — домов: 27, ориентиров: 0
    └── Street: Ленина (ID: 364) — домов: 118, ориентиров: 1
    └── Street: Матросова (ID: 370) — домов: 22, ориентиров: 0
    └── Street: Мира (ID: 375) — домов: 43, ориентиров: 0
    └── Street: Молодежная (ID: 376) — домов: 66, ориентиров: 0
    └── Street: Мугалляма Мирхайдарова (ID: 377) — домов: 13, ориентиров: 0
    └── Street: Партизанская (ID: 381) — домов: 66, ориентиров: 0
    └── Street: Первомайская (ID: 382) — домов: 9, ориентиров: 0
    └── Street: Салавата Юлаева (ID: 393) — домов: 47, ориентиров: 0
    └── Street: Советская (ID: 396) — домов: 26, ориентиров: 0
    └── Street: Тангатарская (ID: 402) — домов: 54, ориентиров: 0
    └── Street: Учалинская (ID: 406) — домов: 15, ориентиров: 0
    └── Street: Чапаева (ID: 413) — домов: 7, ориентиров: 0
    └── Street: Шаймуратова (ID: 416) — домов: 70, ориентиров: 0
    └── Street: Школьная (ID: 418) — домов: 6, ориентиров: 0
    └── Street: Юбилейная (ID: 419) — домов: 36, ориентиров: 0
    └── Street: Южная (ID: 420) — домов: 36, ориентиров: 0
└── District: Южный (ID: 20) — улиц: 20, домов: 512, ориентиров: 0
    └── Street: 40 лет Победы (ID: 333) — домов: 45, ориентиров: 0
    └── Street: 70 лет Октября (ID: 337) — домов: 81, ориентиров: 0
    └── Street: Горная (ID: 431) — домов: 0, ориентиров: 0
    └── Street: Дружбы (ID: 348) — домов: 35, ориентиров: 0
    └── Street: Идяш (ID: 352) — домов: 45, ориентиров: 0
    └── Street: Идяшево (ID: 429) — домов: 0, ориентиров: 0
    └── Street: Искра (ID: 354) — домов: 22, ориентиров: 0
    └── Street: Кирова (ID: 434) — домов: 0, ориентиров: 0
    └── Street: Лесная (ID: 365) — домов: 19, ориентиров: 0
    └── Street: Мажита Гафури (ID: 368) — домов: 18, ориентиров: 0
    └── Street: Мелиораторов (ID: 371) — домов: 27, ориентиров: 0
    └── Street: Механизаторов (ID: 372) — домов: 21, ориентиров: 0
    └── Street: Октябрьская (ID: 433) — домов: 0, ориентиров: 0
    └── Street: Партизанская (ID: 432) — домов: 0, ориентиров: 0
    └── Street: Пионерская (ID: 383) — домов: 25, ориентиров: 0
    └── Street: Рауфа Давлетова (ID: 388) — домов: 66, ориентиров: 0
    └── Street: Рихарда Зорге (ID: 390) — домов: 66, ориентиров: 0
    └── Street: Строителей (ID: 399) — домов: 27, ориентиров: 0
    └── Street: Тагира Кусимова (ID: 400) — домов: 15, ориентиров: 0
    └── Street: Южная (ID: 430) — домов: 0, ориентиров: 0

---

# Potential Duplicates

## Streets

Ключ: `(town_id, district_id, normalized name)`.

Не найдено.

## Houses

Ключ: `(street_id, number)`. Ожидается 0 дубликатов (constraint ``uq_house_street_number``).

Не найдено.

## Landmarks

Ключ: `(street_id, normalized name)`.

Не найдено.

---

# Data Anomalies

Данные, которые могут быть полезны для тестирования. Не считаются аномалиями состояния, которые ORM-модели разрешают как валидные (например, Landmark без дома — это нормально, у модели Landmark колонки street_id и house_id nullable).

## Towns without districts (0)

Нет.

## Streets without districts (0)

Нет.

## Districts without streets (0)

Нет.

## Streets without houses (52)

- ID 424: Файзрахмана Мустафина (район id=23, town id=4)
- ID 425: Ак-Күлгин (район id=23, town id=4)
- ID 426: Шакимана (район id=23, town id=4)
- ID 427: Любимая (район id=23, town id=4)
- ID 428: Комарова (район id=23, town id=4)
- ID 429: Идяшево (район id=20, town id=4)
- ID 430: Южная (район id=20, town id=4)
- ID 431: Горная (район id=20, town id=4)
- ID 432: Партизанская (район id=20, town id=4)
- ID 433: Октябрьская (район id=20, town id=4)
- ID 434: Кирова (район id=20, town id=4)
- ID 435: Юности (район id=22, town id=4)
- ID 436: Николая Гоголя (район id=22, town id=4)
- ID 437: Емельяна Пугачёва (район id=22, town id=4)
- ID 438: Миптата Хакимова (район id=22, town id=4)
- ID 440: Шаймуратова (район id=22, town id=4)
- ID 442: Шаймуратова (район id=21, town id=4)
- ID 443: Рамазана Уметбаева (район id=21, town id=4)
- ID 444: Фазиля Искандера (район id=21, town id=4)
- ID 445: Курчатова (район id=21, town id=4)
- ID 446: Сагиры Мишар (район id=21, town id=4)
- ID 447: Тукая (район id=21, town id=4)
- ID 448: Нажипа Асанбаева (район id=21, town id=4)
- ID 449: Рами Гарипова (район id=21, town id=4)
- ID 450: Валиахмета Сулейманова (район id=21, town id=4)
- ID 451: Индиры Султанбаевой (район id=21, town id=4)
- ID 452: Мисаля Муртасина (район id=21, town id=4)
- ID 453: 8 Марта (район id=24, town id=4)
- ID 454: 10 лет Победы (район id=24, town id=4)
- ID 455: 60 лет Победы (район id=24, town id=4)
- ID 456: Абзелиловская (район id=24, town id=4)
- ID 457: Александра Пушкина (район id=24, town id=4)
- ID 458: Гайфуллы Сарбаева (район id=24, town id=4)
- ID 459: Георгия Васева (район id=24, town id=4)
- ID 460: Караташ (район id=24, town id=4)
- ID 461: Кизильская (район id=24, town id=4)
- ID 462: Кинзи Арсланова (район id=24, town id=4)
- ID 463: Кыркты-Тау (район id=24, town id=4)
- ID 464: Михаила Лермонтова (район id=24, town id=4)
- ID 465: Мусы Джалиля (район id=24, town id=4)
- ID 466: Нургали Фахретдинова (район id=24, town id=4)
- ID 467: Рауфа Давлетова (район id=24, town id=4)
- ID 468: Сагиды Бердиной (район id=24, town id=4)
- ID 469: Салавата Юлаева (район id=24, town id=4)
- ID 470: Салимьяна Гайнуллина (район id=24, town id=4)
- ID 471: Саляха Кулибая (район id=24, town id=4)
- ID 472: Северная (район id=24, town id=4)
- ID 473: Сергея Аксакова (район id=24, town id=4)
- ID 474: Сергея Есенина (район id=24, town id=4)
- ID 475: Центральная (район id=24, town id=4)
- ID 476: Шакира Биккулова (район id=24, town id=4)
- ID 477: Школьная (район id=24, town id=4)

## Houses without street (0)

Нет (обязательный NOT NULL FK — невозможны).

## Landmarks without street (0)

Нет.

## Landmarks without house (0)

Нет.

## Unparseable house numbers (1)

Подробности в разделе "# Unparseable House Numbers".

---

# Unparseable House Numbers

Номера домов, которые существующий ``parse_house_number()`` вернул как ``None``. Важно для дальнейшего расширения parser и тестов.

Всего: **1**.

| House ID | Number | Street | District | Town |
|---|---|---|---|---|
| 9112 | 2/1а | Сарии Миржановой | Восточный-2 | Аскарово |

---