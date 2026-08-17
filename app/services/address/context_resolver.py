from app.repositories.address_repo import AddressRepository
from app.schemas.address import AddressContext




class ContextResolver:
    def __init__(
        self,
        address_repo: AddressRepository,
        default_town_name: str,
    ):
        self.address_repo = address_repo
        self.default_town_name = default_town_name

    async def resolve(
        self,
        town_name: str | None,
        district_name: str | None,
    ) -> AddressContext | None:
        """
        Разрешает город и районный контекст.

        Алгоритм:

        1. Если town_name отсутствует:
           использовать default_town_name.

        2. Найти Town.

        3. Если town не найден:
           вернуть None.

        4. Если district_name указан:
           найти конкретный District.
           Если не найден -> None.

        5. Если district_name не указан:
           получить все district_id города.

        6. Вернуть AddressContext.
        """

        resolved_town_name = town_name or self.default_town_name

        town = await self.address_repo.get_town_by_name(
            resolved_town_name
        )

        if town is None:
            return None

        if district_name:
            district = await self.address_repo.get_district_by_name(
                town_id=town.id,
                name=district_name,
            )

            if district is None:
                return None

            return AddressContext(
                town_id=town.id,
                district_ids=[district.id],
            )

        district_ids = (
            await self.address_repo.get_district_ids_by_town(town.id)
        )

        if not district_ids:
            return None

        return AddressContext(
            town_id=town.id,
            district_ids=district_ids,
        )