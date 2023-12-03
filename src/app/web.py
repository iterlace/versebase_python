import asyncio
from typing import Optional

from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

import app.marketplace.router
from app.core.config import settings

application = FastAPI()

origins = [
    "http://localhost:.*",
    "http://localhost",
]

application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origin_regex=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
application.include_router(app.progress.router.router)
application.include_router(app.characters.router.router)
application.include_router(app.admin.router.router)


@application.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Optional[Request], exc: ValidationError
) -> JSONResponse:
    # message will consist only of the first error
    err = exc.errors()[0]
    loc = ".".join(str(i) for i in err["loc"])
    message = f"{loc}: {err['msg']}"
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": message, "errors": jsonable_encoder(exc.errors())},
    )


@application.exception_handler(ValueError)
async def value_exception_handler(
    request: Optional[Request], exc: ValueError
) -> JSONResponse:
    body = "; ".join(exc.args)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": body},
    )


@application.on_event("startup")
async def initialize() -> None:
    if settings.ENVIRONMENT == "testing":
        return

    # ...


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(application, host="0.0.0.0", port=8000)
