from contextlib import asynccontextmanager

from aerich import Command
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise
from tortoise.exceptions import DoesNotExist

from meilisync_admin.api import router
from meilisync_admin.exceptions import (
    custom_http_exception_handler,
    exception_handler,
    not_exists_exception_handler,
    validation_exception_handler,
)
from meilisync_admin.log import init_logging
from meilisync_admin.scheduler import Scheduler
from meilisync_admin.settings import TORTOISE_ORM, settings
from meilisync_admin.static import SPAStaticFiles


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_logging()
    aerich = Command(TORTOISE_ORM)
    await aerich.init()
    await aerich.upgrade(True)
    await Scheduler.startup()
    yield
    Scheduler.shutdown()


if settings.DEBUG:
    app = FastAPI(
        title="MeiliSyncAdmin",
        description="MeiliSync admin dashboard",
        debug=settings.DEBUG,
        lifespan=lifespan,
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
        lifespan=lifespan,
    )
app.include_router(router, prefix="/api")
register_tortoise(
    app,
    config=TORTOISE_ORM,
)
app.mount("/", SPAStaticFiles(directory="static", html=True), name="static")
app.add_exception_handler(HTTPException, custom_http_exception_handler)  # type: ignore
app.add_exception_handler(DoesNotExist, not_exists_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(Exception, exception_handler)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "meilisync_admin.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
