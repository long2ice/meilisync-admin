from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from meilisync.enums import EventType
from pydantic import BaseModel, Json
from starlette.background import BackgroundTasks
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.models import Sync, SyncLog
from meilisync_admin.scheduler import Scheduler
from meilisync_admin.schema.request import Query

router = APIRouter()


class SyncItem(pydantic_model_creator(Sync)):  # type: ignore
    meilisearch_id: int
    source_id: int


class ListResponse(BaseModel):
    total: int
    data: List[SyncItem]


@router.get("", response_model=ListResponse, summary="获取同步列表")
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
    data = await qs.limit(query.limit).offset(query.offset).order_by(*query.orders)
    return ListResponse(total=total, data=data)


class CreateBody(BaseModel):
    label: str
    source_id: int
    meilisearch_id: int
    full_sync: bool = True
    table: str
    index: str
    primary_key: str = "id"
    enabled: bool = True
    fields: Optional[Json]


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    summary="创建同步",
    description="如果同步记录已存在则返回`409`",
)
async def create(
    body: CreateBody,
):
    try:
        await Sync.create(**body.dict())
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


class SyncRequest(BaseModel):
    pks: Optional[List[int]] = Body(None, description="同步ID列表")


@router.post(
    "/refresh",
    summary="刷新同步",
    description="删除所有MeiliSearch中的数据，重新同步所有数据",
    status_code=HTTP_204_NO_CONTENT,
)
async def refresh(
    background_tasks: BackgroundTasks,
    body: Optional[SyncRequest] = None,
):
    async def _():
        qs = Sync.all().select_related("source", "meilisearch")
        if body and body.pks:
            qs = qs.filter(pk__in=body.pks)
        for sync in await qs:
            Scheduler.remove_source(sync.source.pk)
            source_obj = sync.source.get_source()
            data = await source_obj.get_full_data(sync)
            if data:
                await sync.meili_client.refresh_data(sync.index, sync.primary_key, data)
            await Scheduler.restart_source(sync.source)

    background_tasks.add_task(_)


class CheckResult(BaseModel):
    count: int
    meili_count: int


@router.get(
    "/check/{pk}",
    summary="检查同步",
    description="检查同步数据库和MeiliSearch中的数据数量是否一致",
    response_model=CheckResult,
)
async def check(
    pk: int,
):
    sync = await Sync.get(pk=pk).select_related("source", "meilisearch")
    source_obj = sync.source.get_source()
    count = await source_obj.get_count(sync)
    meili_count = await sync.meili_client.get_count(sync.index)
    return CheckResult(
        count=count,
        meili_count=meili_count,
    )


@router.delete("/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除同步")
async def delete(pks: str):
    for pk in pks.split(","):
        sync = await Sync.get(pk=pk)
        await sync.delete()


class UpdateBody(BaseModel):
    source_id: Optional[int]
    full_sync: Optional[bool]
    table: Optional[str]
    index: Optional[str]
    primary_key: Optional[str]
    enabled: Optional[bool]
    fields: Optional[Json]
    meilisearch_id: Optional[int]


@router.patch(
    "/{pk}",
    status_code=HTTP_204_NO_CONTENT,
    summary="更新同步",
    description="如果同步记录已存在则返回`409`",
)
async def update(
    pk: int,
    body: UpdateBody,
):
    sync = await Sync.get(pk=pk)
    try:
        await sync.update_from_dict(body.dict(exclude_none=True)).save()
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


class SyncLogResponse(pydantic_model_creator(SyncLog)):  # type: ignore
    sync_id: int


class LogsResponse(BaseModel):
    total: int
    data: list[SyncLogResponse]


@router.get(
    "/logs",
    response_model=LogsResponse,
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
    qs = qs.limit(query.limit).offset(query.offset).order_by(*query.orders)
    total = await qs.count()
    data = await qs
    return LogsResponse(total=total, data=data)


@router.delete("/logs/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除同步记录")
async def delete_sync_logs(pks: str):
    pk_list = pks.split(",")
    await SyncLog.filter(pk__in=pk_list).delete()
