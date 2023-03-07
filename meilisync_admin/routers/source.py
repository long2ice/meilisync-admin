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
from tortoise.contrib.pydantic import pydantic_queryset_creator

from meilisync_admin.models import Source

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


@router.get("", response_model=pydantic_queryset_creator(Source), summary="获取数据源列表")
async def get_list(
    limit: int = 10,
    offset: int = 0,
):
    return await Source.all().limit(limit).offset(offset).order_by("-id")


class CreateBody(CheckBody):
    label: str


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    dependencies=[Depends(check_source)],
    summary="创建数据源",
    description="会检查数据源是否可用，如果不可用则返回`412`",
)
async def create(
    body: CreateBody,
):
    await Source.create(**body.dict())


class UpdateBody(BaseModel):
    label: Optional[str]
    type: Optional[SourceType]
    connection: Optional[Dict]


@router.patch(
    "/{pk}",
    status_code=HTTP_204_NO_CONTENT,
    summary="更新数据源",
    description="会检查数据源是否可用，如果不可用则返回`412`",
    dependencies=[Depends(check_source)],
)
async def update(
    pk: int,
    body: UpdateBody,
):
    source = await Source.get(pk=pk)
    check_body = CheckBody(
        type=body.type or source.type,
        connection=body.connection or source.connection,
    )
    await check_source(check_body)
    await source.update_from_dict(body.dict(exclude_none=True)).save()


@router.delete("/{pk}", status_code=HTTP_204_NO_CONTENT, summary="删除数据源")
async def delete(pk: int):
    source = await Source.get(pk=pk)
    await source.delete()
