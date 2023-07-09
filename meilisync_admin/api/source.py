from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from meilisync.discover import get_source
from meilisync.enums import SourceType
from pydantic import BaseModel
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_412_PRECONDITION_FAILED,
)

from meilisync_admin.models import Source
from meilisync_admin.schema.request import Query

router = APIRouter()


class CheckBody(BaseModel):
    type: SourceType
    connection: Dict


async def check_source(body: CheckBody):
    source_cls = get_source(body.type)
    source = source_cls(progress={}, tables=[], **body.connection)
    try:
        return await source.ping()
    except Exception as e:
        raise HTTPException(status_code=HTTP_412_PRECONDITION_FAILED, detail=str(e))


@router.get("/basic", summary="获取数据源列表基本信息")
async def get_list_basic():
    return await Source.all().values("id", "label")


@router.get("", summary="获取数据源列表")
async def get_list(
    query: Query = Depends(Query),
    label: str | None = None,
    type: SourceType | None = None,
):
    qs = Source.all()
    if label:
        qs = qs.filter(label__icontains=label)
    if type:
        qs = qs.filter(type=type)
    total = await qs.count()
    data = await qs.limit(query.limit).offset(query.offset).order_by(*query.orders)
    return dict(total=total, data=data)


class Body(CheckBody):
    label: str


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    dependencies=[Depends(check_source)],
    summary="创建数据源",
    description="会检查数据源是否可用，如果不可用则返回`412`",
)
async def create(
    body: Body,
):
    await Source.create(**body.dict())


class UpdateBody(BaseModel):
    label: Optional[str]
    type: Optional[SourceType]
    connection: Optional[Dict]


@router.put(
    "/{pk}",
    status_code=HTTP_204_NO_CONTENT,
    summary="更新数据源",
    description="会检查数据源是否可用，如果不可用则返回`412`",
    dependencies=[Depends(check_source)],
)
async def update(
    pk: int,
    body: Body,
):
    source = await Source.get(pk=pk)
    check_body = CheckBody(type=body.type, connection=body.connection)
    await check_source(check_body)
    await source.update_from_dict(body.dict()).save()


@router.delete("/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除数据源")
async def delete(pks: str):
    for pk in pks.split(","):
        source = await Source.get(pk=pk)
        await source.delete()
