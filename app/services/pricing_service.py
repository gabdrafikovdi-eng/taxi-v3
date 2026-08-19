from decimal import Decimal
from typing import Final

from app.core.exceptions import PricingError
from app.models.order import Order
from app.repositories.address_repo import AddressRepository
from app.schemas.address import PricingAddress
from app.core.config import address_config


class PricingService:
    waypoint_coefficient: Final = Decimal("0.5")

    def __init__(
        self,
        address_repo: AddressRepository,
        
    ) -> None:
        self.address_repo = address_repo
        self.address_config = address_config

    async def calculate(self, order: Order) -> int | None:
        if not order.can_calculate_price:
            return None

        origin = await self._get_required_pricing(
            town_id=order.pickup_town_id,
            district_id=order.pickup_district_id,
            street_id=order.pickup_street_id,
            house_id=order.pickup_house_id,
            point_name="pickup",
        )

        destination = await self._get_required_pricing(
            town_id=order.destination_town_id,
            district_id=order.destination_district_id,
            street_id=order.destination_street_id,
            house_id=order.destination_house_id,
            point_name="destination",
        )

        origin_is_base = self._is_base_address(
            town_id=order.pickup_town_id,
            district_id=order.pickup_district_id,
        )

        destination_is_base = self._is_base_address(
            town_id=order.destination_town_id,
            district_id=order.destination_district_id,
        )

        total = self._resolve_main_price(
            origin=origin,
            destination=destination,
            origin_is_base=origin_is_base,
            destination_is_base=destination_is_base,
        )

        for waypoint in order.waypoints:
            waypoint_pricing = await self._get_required_pricing(
                town_id=waypoint.waypoint_town_id,
                district_id=waypoint.waypoint_district_id,
                street_id=waypoint.waypoint_street_id,
                house_id=waypoint.waypoint_house_id,
                point_name="waypoint",
            )

            waypoint_price = self._resolve_price(waypoint_pricing)
            total += int(Decimal(waypoint_price) * self.waypoint_coefficient)

        return total

    async def _get_required_pricing(
        self,
        *,
        town_id: int,
        district_id: int | None,
        street_id: int | None,
        house_id: int | None,
        point_name: str,
    ) -> PricingAddress:
        pricing = await self.address_repo.get_pricing_address(
            town_id=town_id,
            district_id=district_id,
            street_id=street_id,
            house_id=house_id,
        )

        if pricing is None:
            raise PricingError(
                reason=f"Не удалось определить тариф для {point_name}",
            )

        return pricing

    def _is_base_address(
        self,
        *,
        town_id: int,
        district_id: int | None,
    ) -> bool:
        return (
            town_id == self.address_config.base_town_id
            and district_id == self.address_config.base_district_id
        )

    def _resolve_main_price(
        self,
        *,
        origin: PricingAddress,
        destination: PricingAddress,
        origin_is_base: bool,
        destination_is_base: bool,
    ) -> int:
        if destination_is_base and not origin_is_base:
            return self._resolve_price(origin)

        return self._resolve_price(destination)

    @staticmethod
    def _resolve_price(pricing: PricingAddress) -> int:
        if pricing.house_price is not None:
            return pricing.house_price

        if pricing.street_price is not None:
            return pricing.street_price

        if pricing.district_price is not None:
            return pricing.district_price

        return pricing.town_base_price