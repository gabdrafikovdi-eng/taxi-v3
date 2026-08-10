from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models.address import Street, StreetSynonym, House, District, Town


class AddressRepository:
    """
    Мок-реализация AddressRepository для разработки и тестов.
    Предоставляет методы для поиска улиц, синонимов, домов и загрузки с районами.
    """

    async def find_street_by_name(self, session: AsyncSession, name: str) -> list[Street]:
        """Найти улицу по названию (частичное совпадение без учёта регистра)."""
        stmt = select(Street).where(Street.name.ilike(f"%{name}%"))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_street_by_synonym(self, session: AsyncSession, name: str) -> Street | None:
        """Найти улицу по синониму (например, 'больница' -> street_id)."""
        stmt = (
            select(Street)
            .join(StreetSynonym, Street.id == StreetSynonym.street_id)
            .where(StreetSynonym.name.ilike(f"%{name}%"))
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_street_with_district(self, session: AsyncSession, street_id: int) -> Street | None:
        """Загрузить улицу с районом и городом для расчёта цены."""
        stmt = (
            select(Street)
            .options(
                selectinload(Street.district).selectinload(District.town)
            )
            .where(Street.id == street_id)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def find_house_by_street_and_number(
        self, session: AsyncSession, street_id: int, number: str
    ) -> House | None:
        """Найти конкретный дом по ID улицы и номеру."""
        stmt = select(House).where(
            House.street_id == street_id,
            House.number.ilike(number)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
