from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.models import Meilisearch
from meilisync_admin.schema.request import Query

router = APIRouter()


class ListResponse(BaseModel):
    total: int
    data: List[pydantic_model_creator(Meilisearch)]  # type: ignore


@router.get("", response_model=ListResponse, summary="获取meilisearch列表")
async def get_list(
    query: Query = Depends(Query),
    label: str | None = None,
):
    qs = Meilisearch.all()
    if label:
        qs = qs.filter(label__icontains=label)
    total = await qs.count()
    data = await qs.limit(query.limit).offset(query.offset).order_by(*query.orders)
    return ListResponse(total=total, data=data)


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
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="Meilisearch already exists"
        )


@router.delete("/{pks}", status_code=HTTP_204_NO_CONTENT, summary="删除meilisearch")
async def delete(pks: str):
    for pk in pks.split(","):
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
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail="Meilisearch already exists"
        )
