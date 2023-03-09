from tortoise.signals import post_delete, post_save

from meilisync_admin.models import Meilisearch, Source, Sync
from meilisync_admin.scheduler import Scheduler


@post_save(Source)
async def post_save_source(
    sender: Source, instance: Source, created: bool, using_db: bool, update_fields: list
):
    await Scheduler.restart_source(instance)


@post_delete(Source)
async def post_delete_source(sender: Source, instance: Source, using_db: bool):
    Scheduler.remove_source(instance.pk)


@post_save(Sync)
async def post_save_sync(
    sender: Sync, instance: Sync, created: bool, using_db: bool, update_fields: list
):
    await Scheduler.restart_source(await instance.source)


@post_delete(Sync)
async def post_delete_sync(sender: Sync, instance: Sync, using_db: bool):
    await Scheduler.restart_source(await instance.source)


@post_save(Meilisearch)
async def post_save_meili(
    sender: Meilisearch,
    instance: Meilisearch,
    created: bool,
    using_db: bool,
    update_fields: list,
):
    if created:
        return
    syncs = await Sync.filter(meilisearch=instance).all().select_related("source")
    for sync in syncs:
        await Scheduler.restart_source(sync.source)


@post_delete(Meilisearch)
async def post_delete_meili(sender: Meilisearch, instance: Meilisearch, using_db: bool):
    syncs = await Sync.filter(meilisearch=instance).all().select_related("source")
    for sync in syncs:
        await Scheduler.restart_source(sync.source)
