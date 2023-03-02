import asyncio

from loguru import logger
from meilisync.discover import get_progress, get_source
from meilisync.enums import ProgressType
from meilisync.meili import Meili
from meilisync.schemas import Event
from meilisync.settings import MeiliSearch
from meilisync.settings import Sync as SyncSettings

from meilisync_admin.models import Source, Sync
from meilisync_admin.settings import settings

_tasks = {}


async def start_source(source: Source):
    progress_cls = get_progress(ProgressType.redis)
    syncs = await Sync.filter(enabled=True, source=source).all()
    progress = progress_cls(dsn=settings.REDIS_URL, key=f"meilisync:progress:{source.pk}")
    source_cls = get_source(source.type)
    current_progress = await progress.get()
    tables = [sync.table for sync in syncs]
    source_obj = source_cls(
        progress=current_progress,
        tables=tables,
        **source.connection,
    )
    sync_settings = [
        SyncSettings(
            table=sync.table,
            pk=sync.primary_key,
            full=sync.full_sync,
            index=sync.index,
            fields=sync.fields,
        )
        for sync in syncs
    ]
    meili = Meili(
        debug=settings.DEBUG,
        meilisearch=MeiliSearch(api_url=settings.MEILI_API_URL, api_key=settings.MEILI_API_KEY),
        sync=sync_settings,
    )
    if not current_progress:
        for sync in sync_settings:
            if sync.full:
                data = await source_obj.get_full_data(sync)
                if data:
                    await meili.add_full_data(sync.index_name, sync.pk, data)
                    logger.info(
                        f'Full data sync for table "{source.label}.{sync.table}" '
                        f"done! {len(data)} documents added."
                    )
                else:
                    logger.info(
                        f'Full data sync for table "{source.label}.{sync.table}" '
                        f"done! No data found."
                    )

    async def _():
        logger.info(
            f'Start increment sync data from "{source.label}" to MeiliSearch, tables: {tables}...'
        )
        async for event in source_obj:
            if isinstance(event, Event):
                await meili.handle_event(event)
            await progress.set(**event.progress)

    _tasks[source.pk] = {
        "task": asyncio.ensure_future(_()),
        "meili": meili,
    }


async def startup():
    sources = await Source.all()
    for source in sources:
        await start_source(source)


def shutdown():
    for task in _tasks.values():
        task["task"].cancel()


def remove_source(source_id: int):
    if source_id in _tasks:
        _tasks[source_id]["task"].cancel()
        del _tasks[source_id]


async def restart_source(source: Source):
    logger.info(f'Restart source "{source.label}"...')
    source_id = source.pk
    remove_source(source_id)
    await start_source(source)
