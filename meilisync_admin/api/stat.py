from fastapi import APIRouter
from tortoise.expressions import RawSQL
from tortoise.functions import Count

from meilisync_admin.models import ActionLog, Admin, Meilisearch, Source, Sync, SyncLog

router = APIRouter()


@router.get("")
async def get_stats():
    source_count = await Source.all().count()
    sync_count = await Sync.all().count()
    sync_log_count = await SyncLog.all().count()
    admin_count = await Admin.filter(is_active=True).count()
    action_log_count = await ActionLog.all().count()
    sync_logs = (
        await SyncLog.annotate(count=Count("id"), date=RawSQL("date(created_at)"))
        .group_by("type", "date")
        .values("type", "count", "date")
    )
    meili_count = await Meilisearch.all().count()
    return {
        "admin_count": admin_count,
        "action_log_count": action_log_count,
        "source_count": source_count,
        "sync_count": sync_count,
        "sync_log_count": sync_log_count,
        "sync_logs": sync_logs,
        "meili_count": meili_count,
    }
