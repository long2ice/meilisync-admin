from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Json
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.models import Sync

router = APIRouter()


@router.get("", response_model=pydantic_queryset_creator(Sync))
async def get_list(
    limit: int = 10,
    offset: int = 0,
):
    await Sync.all().limit(limit).offset(offset).order_by("-id")


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


@router.post("", status_code=HTTP_201_CREATED)
async def create(
    body: CreateBody,
):
    try:
        await Sync.create(**body.dict())
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Sync already exists")


@router.delete("/{pk}", status_code=HTTP_204_NO_CONTENT)
async def delete(pk: int):
    sync = await Sync.get(pk=pk)
    await sync.delete()


class UpdateBody(BaseModel):
    source_id: Optional[int]
    meilisearch_id: Optional[int]
    full_sync: Optional[bool]
    table: Optional[str]
    index: Optional[str]
    primary_key: Optional[str]
    enabled: Optional[bool]
    fields: Optional[Json]


@router.patch("/{pk}", status_code=HTTP_204_NO_CONTENT)
async def update(
    pk: int,
    body: UpdateBody,
):
    sync = await Sync.get(pk=pk)
    await sync.update_from_dict(body.dict(exclude_none=True)).save()
