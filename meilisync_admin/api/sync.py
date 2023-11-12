from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from meilisearch_python_sdk.models.settings import MeilisearchSettings
from meilisync.enums import EventType
from pydantic import BaseModel
from starlette.background import BackgroundTasks
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.exceptions import IntegrityError

from meilisync_admin.libs.redis import Key, r
from meilisync_admin.models import Sync, SyncLog
from meilisync_admin.scheduler import Runner, Scheduler
from meilisync_admin.schema.request import Query

router = APIRouter()


@router.get("", summary="获取同步列表")
async def get_list(
    query: Query = Depends(Query),
    source_id: int | None = None,
    meilisearch_id: int | None = None,
    enabled: bool | None = None,
    label: str | None = None,
):
    qs = Sync.all()
    if source_id:
        qs = qs.filter(source_id=source_id)
    if meilisearch_id:
        qs = qs.filter(meilisearch_id=meilisearch_id)
    if enabled is not None:
        qs = qs.filter(enabled=enabled)
    if label:
        qs = qs.filter(label__icontains=label)
    total = await qs.count()
    data = (
        await qs.select_related("source", "meilisearch")
        .limit(query.limit)
        .offset(query.offset)
        .order_by(*query.orders)
    )
    return dict(total=total, data=data)


@router.get("/basic", summary="获取同步列表基本信息")
async def get_list_basic():
    return await Sync.all().values("id", "label")


class Body(BaseModel):
    label: str
    source_id: int
    meilisearch_id: int
    full_sync: bool = True
    table: str
    index: str
    primary_key: str = "id"
    enabled: bool = True
    fields: dict | None
    index_settings: MeilisearchSettings | None


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    summary="创建同步",
    description="如果同步记录已存在则返回`409`",
)
async def create(
    body: Body,
):
    try:
        sync = await Sync.create(**body.dict())
        await sync.meilisearch
        await sync.create_index()
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


@router.post(
    "/{pk}/refresh",
    summary="刷新同步",
    description="删除所有MeiliSearch中的数据，重新同步所有数据",
    status_code=HTTP_204_NO_CONTENT,
)
async def refresh(
    background_tasks: BackgroundTasks,
    pk: int,
):
    async def _():
        async with r.lock(Key.refresh_lock.format(sync_id=pk), blocking=False):
            sync = await Sync.get(pk=pk).select_related("source", "meilisearch")
            source_obj = sync.source.get_source()
            Scheduler.remove_source(sync.source.pk)
            progress = Runner.get_progress(sync.source.pk)
            await progress.set(**await source_obj.get_current_progress())
            index_exists = await sync.meili_client.index_exists(sync.index)
            if not index_exists:
                await sync.create_index()
            count = await sync.meili_client.refresh_data(
                sync,
                source_obj.get_full_data(
                    sync.sync_config, sync.meilisearch.insert_size or 10000
                ),
            )
            logger.success(f"Refreshed {count} records!")
            await Scheduler.restart_source(
                sync.source,
            )

    background_tasks.add_task(_)


@router.delete("/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除同步")
async def delete(pks: str):
    for pk in pks.split(","):
        sync = await Sync.get(pk=pk)
        await sync.delete()


@router.put(
    "/{pk}",
    status_code=HTTP_204_NO_CONTENT,
    summary="更新同步",
    description="如果同步记录已存在则返回`409`",
)
async def update(
    pk: int,
    body: Body,
):
    sync = await Sync.get(pk=pk).select_related("meilisearch")
    try:
        await sync.update_from_dict(body.model_dump()).save()
        await sync.update_settings()
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


@router.get(
    "/logs",
    summary="获取同步日志",
    description="每分钟记录一次，包括同步数量和类型",
)
async def logs(
    sync_id: int | None = None,
    source_id: int | None = None,
    meilisearch_id: int | None = None,
    query: Query = Depends(Query),
    type: EventType | None = None,
):
    qs = SyncLog.all()
    if sync_id:
        qs = qs.filter(sync_id=sync_id)
    if source_id:
        qs = qs.filter(sync__source_id=source_id)
    if meilisearch_id:
        qs = qs.filter(sync__meilisearch_id=meilisearch_id)
    if type:
        qs = qs.filter(type=type)
    total = await qs.count()
    data = await qs.limit(query.limit).offset(query.offset).order_by(*query.orders)
    return dict(total=total, data=data)


@router.delete("/logs/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除同步记录")
async def delete_sync_logs(pks: str):
    await SyncLog.filter(pk__in=pks.split(",")).delete()


@router.get("/{pk}/progress", summary="获取同步进度")
async def get_progress(pk: int):
    sync = await Sync.get(pk=pk).select_related("source", "meilisearch")
    await sync.get_count()
    return {
        "source_count": sync.source_count,
        "meilisearch_count": sync.meilisearch_count,
    }
