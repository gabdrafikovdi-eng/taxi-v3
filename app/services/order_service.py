from app.services.state_service import StateService


class OrderService:
    def __init__(self, state_service: StateService, address_service, calculate_service):
        self.state_service = state_service
        self.address_service = address_service
        self.calculate_service = calculate_service

    async def create_order(self):
        ...


        