from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from app.core.database import Base, TimestampMixin


class Town(Base, TimestampMixin):
    __tablename__ = "towns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    base_price: Mapped[int] = mapped_column(nullable=False)
    districts: Mapped[list["District"]] = relationship(
        "District", back_populates="town", cascade="all, delete-orphan"
    )


class District(Base, TimestampMixin):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    town_id: Mapped[int] = mapped_column(
        ForeignKey("towns.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price_override: Mapped[int | None] = mapped_column(nullable=True)
    town: Mapped["Town"] = relationship("Town", back_populates="districts")
    streets: Mapped[list["Street"]] = relationship(
        "Street", back_populates="district", cascade="all, delete-orphan"
    )


class Street(Base, TimestampMixin):
    __tablename__ = "streets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    district_id: Mapped[int] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    price_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district: Mapped["District"] = relationship("District", back_populates="streets")
    synonyms: Mapped[list["StreetSynonym"]] = relationship(
        "StreetSynonym",
        back_populates="street",
        cascade="all, delete-orphan",  # Если удалим улицу, её синонимы удалятся
    )
    houses: Mapped[list["House"]] = relationship(
        "House", back_populates="street", cascade="all, delete-orphan"
    )
    landmarks: Mapped[list["Landmark"]] = relationship(
        "Landmark", back_populates="street", cascade="all, delete-orphan"
    )


class House(Base, TimestampMixin):
    __tablename__ = "houses"
    id: Mapped[int] = mapped_column(primary_key=True)
    street_id: Mapped[int] = mapped_column(
        ForeignKey("streets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    street: Mapped["Street"] = relationship("Street", back_populates="houses")
    landmarks: Mapped[list["Landmark"]] = relationship(
        "Landmark", back_populates="house", cascade="all, delete-orphan"
    )
    __table_args__ = (
        UniqueConstraint("street_id", "number", name="uq_house_street_number"),
    )


class StreetSynonym(Base, TimestampMixin):
    __tablename__ = "street_synonyms"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    street_id: Mapped[int] = mapped_column(
        ForeignKey("streets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    street: Mapped["Street"] = relationship(back_populates="synonyms")

    __table_args__ = (
        UniqueConstraint("street_id", "name", name="uq_street_synonym_name"),
    )


class Landmark(Base, TimestampMixin):
    __tablename__ = "landmarks"

    id: Mapped[int] = mapped_column(primary_key=True)
    street_id: Mapped[int] = mapped_column(
        ForeignKey("streets.id", ondelete="CASCADE"), index=True
    )
    house_id: Mapped[int | None] = mapped_column(
        ForeignKey("houses.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    street: Mapped["Street"] = relationship("Street", back_populates="landmarks")
    house: Mapped["House"] = relationship("House", back_populates="landmarks")
