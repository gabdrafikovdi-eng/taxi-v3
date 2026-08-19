from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from app.models.address import Landmark, Street, StreetSynonym, House, District, Town
from app.schemas.address import PricingAddress


class AddressRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_town_by_name(self, name: str) -> Town | None:
        stmt = select(Town).where(func.lower(Town.name) == name.lower())
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_district_by_name(self, town_id: int, name: str) -> District | None:
        stmt = select(District).where(
            func.lower(District.name) == name.lower(),
            District.town_id == town_id,
        )
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def find_streets_exact(
        self, districts_ids: list[int], name: str
    ) -> list[Street]:
        stmt = (
            select(Street)
            .where(
                Street.district_id.in_(districts_ids),
                func.lower(Street.name) == name.lower(),
            )
            .options(selectinload(Street.district).selectinload(District.town))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_streets_by_synonyms(
        self, districts_ids: list[int], name: str
    ) -> list[Street]:
        stmt = (
            select(Street)
            .join(StreetSynonym, Street.id == StreetSynonym.street_id)
            .where(
                Street.district_id.in_(districts_ids),
                func.lower(StreetSynonym.name) == name.lower(),
            )
            .options(selectinload(Street.district).selectinload(District.town))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_street_fuzzy(
        self, district_ids: list[int], name: str, threshold: float, limit: int
    ) -> list[tuple[Street, float]]:
        name = name.strip()
        effective_threshold = threshold

        if len(name) <= 4:
            effective_threshold = 0.2

        similarity_scrore = func.similarity(Street.name, name)

        stmt = (
            select(Street, similarity_scrore.label("similarity"))
            .where(
                Street.district_id.in_(district_ids),
                similarity_scrore >= effective_threshold,
            )
            .order_by(similarity_scrore.desc())
            .limit(limit)
            .options(selectinload(Street.district).selectinload(District.town))
        )
        result = await self.session.execute(stmt)

        return result.all()

    async def find_house(self, street_id: int, number: str) -> House | None:
        stmt = select(House).where(House.street_id == street_id, House.number == number)
        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def find_landmarks(
        self, district_ids: list[int], name: str
    ) -> list[Landmark]:
        stmt = (
            select(Landmark)
            .join(Street, Landmark.street_id == Street.id)
            .where(
                Street.district_id.in_(district_ids),
                Landmark.name.ilike(f"%{name}%"),
            )
            .options(
                selectinload(Landmark.street)
                .selectinload(Street.district)
                .selectinload(District.town),
                selectinload(Landmark.house),
            )
        )
        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def find_landmark_by_street(self, street_id, name: str) -> Landmark | None:
        stmt = (
            select(Landmark)
            .options(selectinload(Landmark.house))
            .where(
                Landmark.street_id == street_id,
                func.lower(Landmark.name) == name.lower(),
            )
        )
        result = await self.session.execute(stmt)

        return result.scalars().first()

    async def get_district_ids_by_town(self, town_id: int) -> list[int]:
        stmt = select(District.id).where(District.town_id == town_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_pricing_address(
        self, town_id: int, district_id: int, street_id: int, house_id: int | None
    ) -> PricingAddress | None:
        stmt = (
            select(
                Town.base_price.label("town_base_price"),
                District.price_override.label("district_price"),
                Street.price_override.label("street_price"),
                House.price_override.label("house_price"),
            )
            .select_from(Town)
            .join(District, District.town_id == Town.id)
            .join(Street, Street.district_id == District.id)
            .join(House, House.street_id == Street.id)
            .where(
                Town.id == town_id,
                District.id == district_id,
                Street.id == street_id,
            )
        )
        if house_id is not None:
            stmt = stmt.where(House.id == house_id)

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        return PricingAddress(
            town_base_price=row.town_base_price,
            district_price=row.district_price,
            street_price=row.street_price,
            house_price=row.house_price,
        )

    async def get_houses_by_street_id(self, street_id: int) -> list[House]:
        stmt = (
            select(House)
            .where(House.street_id == street_id)
            .options(
                selectinload(House.street)
                .selectinload(Street.district)
                .selectinload(District.town)
            )
            .order_by(House.number)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())
