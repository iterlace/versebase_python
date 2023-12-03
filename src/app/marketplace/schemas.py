import datetime as dt

from app.core.schemas import (
    T,
    ReadSchema,
    WriteSchema,
    ModelEditSchema,
    ModelReadSchema,
    ModelWriteSchema,
)
from app.core.storages import StorageFile

from .models import Rat, Gender


class RatRead(ModelReadSchema[Rat]):
    __model__ = Rat

    id: int
    created_at: dt.datetime
    is_booked: bool
    name: str
    age_months: int
    gender: Gender
    price: int
    phone: str
    description: str
    image_url: str

    @classmethod
    def from_model(cls, rat: Rat) -> "RatRead":
        return RatRead(
            id=rat.id,
            created_at=rat.created_at,
            is_booked=rat.is_booked,
            name=rat.name,
            age_months=rat.age_months,
            gender=rat.gender,
            price=rat.price,
            phone=rat.phone,
            description=rat.description,
            image_url=rat.image.url(),
        )


class RatWrite(ModelWriteSchema[Rat]):
    __model__ = Rat

    name: str
    age_months: int
    gender: Gender
    price: int
    phone: str
    description: str

    def to_model(self) -> Rat:
        return Rat(
            id=-1,
            created_at=dt.datetime.now(),
            owner_id=-1,
            is_booked=False,
            name=self.name,
            age_months=self.age_months,
            gender=self.gender,
            price=self.price,
            phone=self.phone,
            description=self.description,
            image=StorageFile(""),
        )
