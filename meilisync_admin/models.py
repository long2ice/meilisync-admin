from typing import Any, Dict, List, Optional

from meilisearch_python_async.errors import MeilisearchApiError
from meilisync.discover import get_source
from meilisync.enums import EventType, SourceType
from meilisync.meili import Meili
from meilisync.settings import Sync as SyncConfig
from tortoise import Model, fields

from meilisync_admin.validators import EmailValidator


class BaseModel(Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class Source(BaseModel):
    label = fields.CharField(max_length=255)
    type = fields.CharEnumField(enum_type=SourceType)
    connection = fields.JSONField()

    def get_source(
        self,
        progress: Optional[Dict[str, Any]] = None,
        tables: Optional[List[str]] = None,
    ):
        source_cls = get_source(self.type)
        source_obj = source_cls(
            progress=progress,
            tables=tables,
            **self.connection,
        )
        return source_obj


class Sync(BaseModel):
    label = fields.CharField(max_length=255)
    source: fields.ForeignKeyRelation[Source] = fields.ForeignKeyField("models.Source")
    full_sync = fields.BooleanField(default=False)
    table = fields.CharField(max_length=255)
    index = fields.CharField(max_length=255)
    primary_key = fields.CharField(max_length=255, default="id")
    enabled = fields.BooleanField(default=True)
    meilisearch: fields.ForeignKeyRelation["Meilisearch"] = fields.ForeignKeyField(
        "models.Meilisearch"
    )
    fields = fields.JSONField(null=True)
    source_count: int
    meilisearch_count: int

    class Meta:
        unique_together = [("meilisearch", "source", "table")]

    @property
    def meili_client(self):
        return Meili(
            self.meilisearch.api_url,
            self.meilisearch.api_key,
        )

    @property
    def sync_config(self):
        return SyncConfig(
            table=self.table,
            fields=self.fields,
            pk=self.primary_key,
            full=self.full_sync,
            index=self.index,
        )

    async def get_count(self):
        self.source_count = await self.source.get_source().get_count(self)
        try:
            self.meilisearch_count = await self.meili_client.get_count(self.index)
        except MeilisearchApiError as e:
            if e.code != "MeilisearchApiError.index_not_found":
                raise e
            self.meilisearch_count = 0


class Meilisearch(BaseModel):
    label = fields.CharField(max_length=255)
    api_url = fields.CharField(max_length=255, unique=True)
    api_key = fields.CharField(max_length=255, null=True)
    insert_size = fields.IntField(null=True)
    insert_interval = fields.IntField(null=True)


class SyncLog(BaseModel):
    sync: fields.ForeignKeyRelation[Sync] = fields.ForeignKeyField("models.Sync")
    type = fields.CharEnumField(enum_type=EventType, default=EventType.create)
    count = fields.IntField(default=0)


class Admin(BaseModel):
    nickname = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True, validators=[EmailValidator()])
    last_login_at = fields.DatetimeField(null=True)
    password = fields.CharField(max_length=255)
    is_superuser = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)


class ActionLog(BaseModel):
    admin: fields.ForeignKeyRelation[Admin] = fields.ForeignKeyField("models.Admin")
    ip = fields.CharField(max_length=255)
    content = fields.JSONField()
    path = fields.CharField(max_length=255)
    method = fields.CharField(max_length=10)
