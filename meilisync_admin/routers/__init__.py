from fastapi import APIRouter

from meilisync_admin.routers import source, sync

router = APIRouter()
router.include_router(source.router, prefix="/source", tags=["Source"])
router.include_router(sync.router, prefix="/sync", tags=["Sync"])
