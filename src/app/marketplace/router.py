import os
import uuid
from typing import Any, Dict, List, Self, Type, Optional, Sequence

from fastapi import (
    Body,
    File,
    Path,
    Query,
    Depends,
    APIRouter,
    UploadFile,
    HTTPException,
)

from app.db.table import Row, Field, Table, TableFile, TableSchema
from app.core.storages import storage

from .models import Rat, RatTable, db
from .schemas import RatRead, RatWrite

router: APIRouter = APIRouter(
    tags=["marketplace"],
    responses={
        401: {"description": "Not authorized"},
        404: {"description": "Not found"},
    },
)


@router.get("/rats/", status_code=200)
async def list_rats() -> List[RatRead]:
    rows = RatTable.select()
    rats = [Rat.from_row(row) for row in rows]
    return [RatRead.from_model(rat) for rat in rats]


@router.post("/rats/", status_code=201)
async def create_rat(rat: RatWrite) -> RatRead:
    rat_obj: Rat = rat.to_model()
    RatTable.create(rat_obj.to_row())
    return RatRead.from_model(rat_obj)


@router.post("/rats/", status_code=201)
async def upload_rat_image(rat_id: int, image: UploadFile) -> RatRead:
    row = RatTable.get(rat_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Rat not found")

    rat = Rat.from_row(row)

    if image.content_type not in ["image/png", "image/jpeg"]:
        raise HTTPException(status_code=400, detail="Icon must be either png or jpeg.")

    ext = image.content_type.split("/")[-1]
    filepath = os.path.join("rats", f"{uuid.uuid4()}.{ext}")

    file = storage.upload(await image.read(), filepath)
    rat.image = file
    RatTable.update(rat.to_row())

    return RatRead.from_model(rat)
