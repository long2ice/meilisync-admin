from meilisync.enums import SourceType
from tortoise import Model, fields


class BaseModel(Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class Source(BaseModel):
    label = fields.CharField(max_length=255)
    type = fields.CharEnumField(enum_type=SourceType)
    connection = fields.JSONField()


class MeiliSearch(BaseModel):
    label = fields.CharField(max_length=255)
    api_url = fields.CharField(max_length=255)
    api_key = fields.CharField(max_length=255)


class Sync(BaseModel):
    source: fields.ForeignKeyRelation[Source] = fields.ForeignKeyField("models.Source")
    meilisearch: fields.ForeignKeyRelation[MeiliSearch] = fields.ForeignKeyField(
        "models.MeiliSearch"
    )
    full_sync = fields.BooleanField(default=False)
    table = fields.CharField(max_length=255)
    index = fields.CharField(max_length=255)
    primary_key = fields.CharField(max_length=255, default="id")
    enabled = fields.BooleanField(default=True)
    fields = fields.JSONField(null=True)


class Config(BaseModel):
    key = fields.CharField(max_length=255, unique=True)
    value = fields.JSONField(null=True)
