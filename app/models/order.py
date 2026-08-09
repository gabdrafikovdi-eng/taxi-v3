from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4


from sqlalchemy import DateTime, ForeignKey, String, Enum, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class OrderState(StrEnum):
    DRAFT = "draft"  # Заказ в процессе сбора данных
    CONFIRMED = "confirmed"  # Пользователь подтвердил
    SEARCHING = "searghing"  # Поиск водителя
    ASSIGNED = "assigned"  # Водитель назначен
    IN_PROGRESS = "in_progress"  # В процессе выполнения
    COMPLETED = "completed"  # Заказ завершён успешно
    CANCELLED = "cancelled"  # Заказ отменён


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    call_session_id: Mapped[UUID] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    pickup_town: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pickup_town_id: Mapped[int | None] = mapped_column(
        ForeignKey("towns.id", ondelete="SET NULL"), nullable=True
    )

    pickup_district: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pickup_district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True
    )

    pickup_street: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pickup_street_id: Mapped[int | None] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    pickup_house: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pickup_house_id: Mapped[int | None] = mapped_column(
        ForeignKey("houses.id", ondelete="SET NULL"), nullable=True
    )
    pickup_landmark: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pickup_landmark_id: Mapped[int | None] = mapped_column(
        ForeignKey("ladnmarks.id", ondelete="SET NULL"), nullable=True
    )

    destination_town: Mapped[str | None] = mapped_column(String(250), nullable=True)
    destination_town_id: Mapped[int | None] = mapped_column(
        ForeignKey("towns.id", ondelete="SET NULL"), nullable=True
    )

    destination_district: Mapped[str | None] = mapped_column(String(250), nullable=True)
    destination_district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True
    )

    destination_street: Mapped[str | None] = mapped_column(String(250), nullable=True)
    destination_street_id: Mapped[int | None] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    destination_house: Mapped[str | None] = mapped_column(String(50), nullable=True)
    destination_house_id: Mapped[int | None] = mapped_column(
        ForeignKey("houses.id", ondelete="SET NULL"), nullable=True
    )
    destination_landmark: Mapped[str | None] = mapped_column(String(250), nullable=True)
    destination_landmark_id: Mapped[int | None] = mapped_column(
        ForeignKey("ladnmarks.id", ondelete="SET NULL"), nullable=True
    )

    passenger_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    comment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    price: Mapped[int | None] = mapped_column(nullable=True)
    state: Mapped[OrderState] = mapped_column(
        Enum(
            OrderState,
            name="order_state",
            native_enum=False,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        default=OrderState.DRAFT,
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True
    )
    waypoints: Mapped[list["Waypoint"]] = relationship(
        "Waypoint", back_populates="order"
    )
    driver_id: Mapped[UUID | None] = mapped_column(nullable=True)
    driver_assigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trip_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trip_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __mapper_args__ = {"version_id_col": version}

    @property
    def has_both_addresses(self) -> bool:
        """
        Оба адреса установлены и валидны.

        Проверяем street_id, а не текстовый адрес, потому что
        street_id заполняется только после успешной валидации.
        """
        return bool(
            self.pickup_street_id is not None and self.destination_street_id is not None
        )

    @property
    def is_priced(self) -> bool:
        """Цена расчитана"""
        return bool(self.price is not None and self.price > 0)

    @property
    def can_calculate_price(self) -> bool:
        """
        Можно рассчитать цену.

        Требования:
        - Заказ в состоянии DRAFT (в других состояниях расчёт не нужен)
        - Оба адреса установлены
        """
        return bool(self.state == OrderState.DRAFT and self.has_both_addresses)

    @property
    def can_confirm(self) -> bool:
        """
        Можно подтвердить заказ.

        Требования:
        - Заказ в состоянии DRAFT
        - Оба адреса установлены
        - Цена рассчитана
        """
        return bool(
            self.state == OrderState.DRAFT
            and self.has_both_addresses
            and self.is_priced
        )

    @property
    def is_active(self) -> bool:
        """Заказ активен (не завершен и не отменен)"""
        return bool(self.state not in (OrderState.CANCELLED, OrderState.COMPLETED))


class Waypoint(Base, TimestampMixin):
    __tablename__ = "waypoints"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    order_id: Mapped[UUID] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"))
    order: Mapped["Order"] = relationship("Order", back_populates="waypoints")
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    waypoint_town: Mapped[str | None] = mapped_column(String(250), nullable=True)
    waypoint_town_id: Mapped[int | None] = mapped_column(
        ForeignKey("towns.id", ondelete="SET NULL"), nullable=True
    )

    waypoint_district: Mapped[str | None] = mapped_column(String(250), nullable=True)
    waypoint_district_id: Mapped[int | None] = mapped_column(
        ForeignKey("districts.id", ondelete="SET NULL"), nullable=True
    )

    waypoint_street: Mapped[str | None] = mapped_column(String(250), nullable=True)
    waypoint_street_id: Mapped[int | None] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    waypoint_house: Mapped[str | None] = mapped_column(String(50), nullable=True)
    waypoint_house_id: Mapped[int | None] = mapped_column(
        ForeignKey("houses.id", ondelete="SET NULL"), nullable=True
    )
    waypoint_landmark: Mapped[str | None] = mapped_column(String(250), nullable=True)
    waypoint_landmark_id: Mapped[int | None] = mapped_column(
        ForeignKey("ladnmarks.id", ondelete="SET NULL"), nullable=True
    )
