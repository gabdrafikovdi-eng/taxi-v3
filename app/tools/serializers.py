# app/tools/serializers.py
from app.models.order import Order, Waypoint


def serialize_waypoint(waypoint: Waypoint) -> dict[str, object]:
    return {
        "sequence_number": waypoint.sequence_number,
        "town": waypoint.waypoint_town,
        "district": waypoint.waypoint_district,
        "street": waypoint.waypoint_street,
        "house": waypoint.waypoint_house,
        "landmark": waypoint.waypoint_landmark,
    }


def serialize_order(order: Order) -> dict[str, object]:
    return {
        "order_number": order.order_number,
        "state": order.state.value,
        "price": order.price,
        "passenger_name": order.passenger_name,
        "comment": order.comment,
        "has_both_addresses": order.has_both_addresses,
        "can_confirm": order.can_confirm,
        "is_active": order.is_active,
        "pickup": {
            "town": order.pickup_town,
            "district": order.pickup_district,
            "street": order.pickup_street,
            "house": order.pickup_house,
            "landmark": order.pickup_landmark,
        },
        "destination": {
            "town": order.destination_town,
            "district": order.destination_district,
            "street": order.destination_street,
            "house": order.destination_house,
            "landmark": order.destination_landmark,
        },
        "waypoints": [serialize_waypoint(wp) for wp in order.waypoints],
    }
