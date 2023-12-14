import datetime as dt
from typing import Optional

import strawberry
from strawberry.fastapi import GraphQLRouter

from app.db.datatypes import Int, Str, Bool, DType, DateTime

from .models import Rat, Gender, RatTable, db


@strawberry.type
class RatGraphQL:
    id: int
    created_at: dt.datetime
    owner_id: int
    is_booked: bool
    name: str
    age_months: int
    gender: str
    price: int
    phone: str
    description: str
    image: str


# Resolvers
@strawberry.type
class Query:
    @classmethod
    def convert(cls, row: RatTable) -> RatGraphQL:
        rat = Rat.from_row(row)
        return RatGraphQL(
            id=rat.id,
            created_at=rat.created_at,
            owner_id=rat.owner_id,
            is_booked=rat.is_booked,
            name=rat.name,
            age_months=rat.age_months,
            gender=rat.gender.value,
            price=rat.price,
            phone=rat.phone,
            description=rat.description,
            image=rat.image.url(),
        )

    @strawberry.field
    def rats(
        self,
        name: Optional[str] = None,
        is_booked: Optional[bool] = None,
        gender: Optional[str] = None,
    ) -> list[RatGraphQL]:
        filters = {}
        if name:
            filters["name"] = Str(name)
        if is_booked:
            filters["is_booked"] = Bool(is_booked)
        if gender:
            filters["gender"] = Str(gender)

        rows = RatTable.select(filters)
        return [Query.convert(row) for row in rows]


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)
