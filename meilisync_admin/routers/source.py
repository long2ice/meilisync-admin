from typing import Optional

from fastapi import APIRouter, HTTPException
from meilisync.enums import SourceType
from pydantic import BaseModel, Json
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_409_CONFLICT
from tortoise.contrib.pydantic import pydantic_queryset_creator
from tortoise.exceptions import IntegrityError

from meilisync_admin.models import Source

router = APIRouter()


@router.get("", response_model=pydantic_queryset_creator(Source))
async def get_list(
    limit: int = 10,
    offset: int = 0,
):
    await Source.all().limit(limit).offset(offset).order_by("-id")


class CreateBody(BaseModel):
    label: str
    type: SourceType
    connection: Json


@router.post("", status_code=HTTP_201_CREATED)
async def create(
    body: CreateBody,
):
    try:
        await Source.create(**body.dict())
    except IntegrityError:
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail="Source already exists")


class UpdateBody(BaseModel):
    label: Optional[str]
    type: Optional[SourceType]
    connection: Optional[Json]


@router.patch("/{pk}", status_code=HTTP_204_NO_CONTENT)
async def update(
    pk: int,
    body: UpdateBody,
):
    source = await Source.get(pk=pk)
    await source.update_from_dict(body.dict(exclude_none=True)).save()


@router.delete("/{pk}", status_code=HTTP_204_NO_CONTENT)
async def delete(pk: int):
    source = await Source.get(pk=pk)
    await source.delete()
