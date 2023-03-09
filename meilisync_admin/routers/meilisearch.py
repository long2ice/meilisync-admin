from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.models import Meilisearch

router = APIRouter()


@router.get("", response_model=pydantic_queryset_creator(Meilisearch), summary="获取meilisearch列表")
async def get_list(
    limit: int = 10,
    offset: int = 0,
):
    return await Meilisearch.all().limit(limit).offset(offset).order_by("-id")


class CreateBody(BaseModel):
    label: str
    api_key: str
    api_url: str
    insert_size: Optional[int]
    insert_interval: Optional[int]


@router.post(
    "",
    status_code=HTTP_201_CREATED,
    summary="创建meilisearch",
    description="如果同步记录已存在则返回`409`",
)
async def create(
    body: CreateBody,
):
    try:
        await Meilisearch.create(**body.dict())
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Meilisearch already exists")


@router.delete("/{pk}", status_code=HTTP_204_NO_CONTENT, summary="删除meilisearch")
async def delete(pk: int):
    m = await Meilisearch.get(pk=pk)
    await m.delete()


class UpdateBody(BaseModel):
    label: Optional[str]
    api_key: Optional[str]
    api_url: Optional[str]
    insert_size: Optional[int]
    insert_interval: Optional[int]


@router.patch(
    "/{pk}",
    status_code=HTTP_204_NO_CONTENT,
    summary="更新meilisearch",
    description="如果同步记录已存在则返回`409`",
)
async def update(
    pk: int,
    body: UpdateBody,
):
    m = await Meilisearch.get(pk=pk)
    try:
        await m.update_from_dict(body.dict(exclude_none=True)).save()
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Meilisearch already exists")
