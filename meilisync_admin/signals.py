from tortoise.signals import post_delete, post_save

from meilisync_admin.models import Source, Sync
from meilisync_admin.scheduler import remove_source, restart_source


@post_save(Source)
async def post_save_source(
    sender: Source, instance: Source, created: bool, using_db: bool, update_fields: list
):
    await restart_source(instance)


@post_delete(Source)
async def post_delete_source(sender: Source, instance: Source, using_db: bool):
    remove_source(instance.pk)


@post_save(Sync)
async def post_save_sync(
    sender: Sync, instance: Sync, created: bool, using_db: bool, update_fields: list
):
    await restart_source(await instance.source)


@post_delete(Sync)
async def post_delete_sync(sender: Sync, instance: Sync, using_db: bool):
    await restart_source(await instance.source)
