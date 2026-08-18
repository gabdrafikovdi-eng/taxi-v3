from app.core.exceptions import PricingError
from app.models.order import Order
from app.repositories.order_repo import OrderRepository
from app.repositories.address_repo import AddressRepository
from app.schemas.address import PricingAddress


class PricingService:
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo
        self.waypoint_coefficient = 0.5

    async def calculate(self, order: Order):
        if not order.can_calculate_price:
            return

        destination_price = await self.address_repo.get_pricing_address(
            town_id=order.destination_town_id,
            district_id=order.destination_district_id,
            street_id=order.destination_street_id,
            house_id=order.destination_house_id,
        )
        
        if destination_price is None:
            raise PricingError(reason="Не удалось определить тариф для destination")

        total = self._resolve_price(destination_price)

        for waypoint in order.waypoints:
            waypoint_pricing = await self.address_repo.get_pricing_address(
                town_id=waypoint.town_id,
                district_id=waypoint.district_id,
                street_id=waypoint.street_id,
                house_id=waypoint.house_id,
            )

            if waypoint_pricing is None:
                raise PricingError("Не удалось определить тариф промежуточной точки")

            waypoint_price = self._resolve_price(waypoint_pricing)

            total += int(waypoint_price * self.waypoint_coefficient)

        return total

    @staticmethod
    def _resolve_price(pricing: PricingAddress) -> int:
        if pricing.house_price is not None:
            return pricing.house_price

        if pricing.street_price is not None:
            return pricing.street_price

        if pricing.district_price is not None:
            return pricing.district_price

        return pricing.town_base_price
