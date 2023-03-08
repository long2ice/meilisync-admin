import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Json
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.meili import meili
from meilisync_admin.models import Sync, SyncLog

router = APIRouter()


@router.get("", response_model=pydantic_queryset_creator(Sync), summary="获取同步列表")
async def get_list(
    limit: int = 10,
    offset: int = 0,
):
    return await Sync.all().limit(limit).offset(offset).order_by("-id")


class CreateBody(BaseModel):
    label: str
    source_id: int
    full_sync: bool = True
    table: str
    index: str
    primary_key: str = "id"
    enabled: bool = True
    fields: Optional[Json]


@router.post("", status_code=HTTP_201_CREATED, summary="创建同步", description="如果同步记录已存在则返回`409`")
async def create(
    body: CreateBody,
):
    try:
        await Sync.create(**body.dict())
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


class SyncRequest(BaseModel):
    pks: Optional[List[int]] = Body(None, description="同步ID列表")


class RefreshResult(BaseModel):
    sync_id: int
    count: int


@router.post(
    "/refresh",
    summary="刷新同步",
    description="删除所有MeiliSearch中的数据，重新同步所有数据",
    response_model=List[RefreshResult],
)
async def refresh(
    body: Optional[SyncRequest] = None,
):
    qs = Sync.all().select_related("source")
    if body and body.pks:
        qs = qs.filter(pk__in=body.pks)
    ret = []
    for sync in await qs:
        source_obj = sync.source.get_source()
        await meili.delete_all_data(sync.index)
        data = await source_obj.get_full_data(sync)
        if data:
            await meili.add_full_data(sync.index, sync.primary_key, data)
        ret.append(
            RefreshResult(
                sync_id=sync.pk,
                count=len(data),
            )
        )
    return ret


class CheckResult(BaseModel):
    sync_id: int
    count: int
    meili_count: int


@router.get(
    "/check",
    summary="检查同步",
    description="检查同步数据库和MeiliSearch中的数据数量是否一致",
    response_model=List[CheckResult],
)
async def check(
    body: Optional[SyncRequest] = None,
):
    qs = Sync.all().select_related("source")
    if body and body.pks:
        qs = qs.filter(pk__in=body.pks)
    ret = []
    for sync in await qs:
        source_obj = sync.source.get_source()
        count = await source_obj.get_count(sync)
        meili_count = await meili.get_count(sync.index)
        ret.append(
            CheckResult(
                sync_id=sync.pk,
                count=count,
                meili_count=meili_count,
            )
        )
    return ret


@router.delete("/{pk}", status_code=HTTP_204_NO_CONTENT, summary="删除同步")
async def delete(pk: int):
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


@router.get(
    "/logs",
    response_model=pydantic_queryset_creator(SyncLog),
    summary="获取同步日志",
    description="每分钟记录一次，包括同步数量和类型",
)
async def logs(
    start: datetime.datetime,
    end: datetime.datetime,
    sync_id: Optional[int] = None,
    source_id: Optional[int] = None,
):
    qs = SyncLog.filter(
        created_at__range=(start, end),
    )
    if sync_id:
        qs = qs.filter(sync_id=sync_id)
    if source_id:
        qs = qs.filter(sync__source_id=source_id)
    return await qs.all()
