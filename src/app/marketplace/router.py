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
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.storages import storage

from .gql import graphql_app
from .models import Rat, RatTable, db
from .schemas import RatRead, RatWrite

router: APIRouter = APIRouter(
    tags=["marketplace"],
    responses={
        401: {"description": "Not authorized"},
        404: {"description": "Not found"},
    },
)
router.include_router(graphql_app, prefix="/graphql")


#  % settings.MEDIA_URL_PREFIX
@router.get("%s{file_path:path}" % settings.MEDIA_URL_PREFIX, status_code=200)
async def read_media(file_path: str) -> FileResponse:
    filepath = storage._get_filepath(file_path)
    assert ".." not in filepath
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)


@router.get("/rats/", status_code=200)
async def list_rats() -> List[RatRead]:
    rows = RatTable.select()
    rats = [Rat.from_row(row) for row in rows]
    return [RatRead.from_model(rat) for rat in rats]


@router.post("/rats/", status_code=201)
async def create_rat(rat: RatWrite) -> RatRead:
    rat_obj: Rat = rat.to_model()
    rat_obj.id = RatTable.create(rat_obj.to_row())
    return RatRead.from_model(rat_obj)


@router.put("/rats/{rat_id}/", status_code=201)
async def update_rat(rat_id: int, rat: RatWrite) -> RatRead:
    row = RatTable.get(rat_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Rat not found")

    rat_obj = Rat.from_row(row)
    rat_obj.name = rat.name
    rat_obj.age_months = rat.age_months
    rat_obj.gender = rat.gender
    rat_obj.price = rat.price
    rat_obj.phone = rat.phone
    rat_obj.description = rat.description

    RatTable.update(rat_obj.to_row())
    return RatRead.from_model(rat_obj)


@router.patch("/rats/{rat_id}/", status_code=201)
async def upload_rat_image(rat_id: int, image: UploadFile) -> RatRead:
    try:
        row = RatTable.get(rat_id)
    except ValueError:
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


@router.delete("/rats/{rat_id}/", status_code=204)
async def delete_rat(rat_id: int) -> None:
    try:
        row = RatTable.get(rat_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Rat not found")

    RatTable.delete(rat_id)
