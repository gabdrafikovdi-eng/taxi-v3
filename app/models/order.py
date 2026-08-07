from enum import StrEnum
from uuid import UUID, uuid4


from sqlalchemy import ForeignKey, String, Enum, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class OrderState(StrEnum):
    DRAFT = "draft"  # Заказ в процессе сбора данных
    CONFIRMED = "confirmed"  # Пользователь подтвердил, точка невозврата
    COMPLETED = "completed"  # Заказ завершён успешно
    CANCELLED = "cancelled"  # Заказ отменён


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    call_session_id: Mapped[int] = mapped_column(
        ForeignKey("call_sessions.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    pickup_street: Mapped[str | None] = mapped_column(String(250), nullable=True)
    pickup_street_id: Mapped[int | None] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    destination_street: Mapped[str | None] = mapped_column(String(250), nullable=True)
    destination_street_id: Mapped[int | None] = mapped_column(
        ForeignKey("streets.id", ondelete="SET NULL"), nullable=True, index=True
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
