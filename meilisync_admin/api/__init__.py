from fastapi import APIRouter, Depends

from meilisync_admin.api import action_log as action_log_api
from meilisync_admin.api import admin, auth, init, meilisearch, source, stat, sync
from meilisync_admin.depends import action_log, auth_required, set_i18n

router = APIRouter(dependencies=[Depends(set_i18n)])
auth_router = APIRouter(dependencies=[Depends(auth_required), Depends(action_log)])

auth_router.include_router(source.router, prefix="/source", tags=["Source"])
auth_router.include_router(sync.router, prefix="/sync", tags=["Sync"])
auth_router.include_router(
    meilisearch.router, prefix="/meilisearch", tags=["Meilisearch"]
)
auth_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
auth_router.include_router(stat.router, prefix="/stat", tags=["Stat"])
auth_router.include_router(
    action_log_api.router, prefix="/action_log", tags=["ActionLog"]
)

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(init.router, prefix="/init", tags=["Init"])
router.include_router(auth_router)
