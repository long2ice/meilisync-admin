from aerich import Command
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist

from meilisync_admin.exceptions import (
    custom_http_exception_handler,
    exception_handler,
    not_exists_exception_handler,
    validation_exception_handler,
)
from meilisync_admin.logging import init_logging
from meilisync_admin.routers import router
from meilisync_admin.scheduler import Scheduler
from meilisync_admin.settings import TORTOISE_ORM, settings

if settings.DEBUG:
    app = FastAPI(
        title="MeiliSyncAdmin",
        description="MeiliSync admin dashboard",
        debug=settings.DEBUG,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
else:
    app = FastAPI(
        title="MeiliSyncAdmin",
        description="MeiliSync admin dashboard",
        debug=settings.DEBUG,
        redoc_url=None,
        docs_url=None,
    )
app.include_router(router)
register_tortoise(
    app,
    config=TORTOISE_ORM,
)
app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(DoesNotExist, not_exists_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, exception_handler)


@app.on_event("startup")
async def startup():
    init_logging()
    aerich = Command(TORTOISE_ORM)
    await aerich.init()
    await aerich.upgrade()
    await Scheduler.startup()


@app.on_event("shutdown")
async def shutdown():
    Scheduler.shutdown()
