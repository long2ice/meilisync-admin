import asyncio
import functools
from typing import Any, Dict

from loguru import logger
from meilisync.discover import get_progress, get_source
from meilisync.enums import ProgressType
from meilisync.meili import Meili
from meilisync.schemas import Event
from meilisync.settings import Sync as SyncSettings

from meilisync_admin.models import Source, Sync, SyncLog
from meilisync_admin.settings import settings


class Scheduler:
    _tasks: Dict[int, Dict[str, Any]] = {}

    @classmethod
    async def startup(cls):
        sources = await Source.all()
        for source in sources:
            await cls._start_source(source)

    @classmethod
    async def _start_source(cls, source: Source):
        stats: Dict[str, int] = {}
        lock = asyncio.Lock()
        progress_cls = get_progress(ProgressType.redis)
        syncs = await Sync.filter(enabled=True, source=source).all()
        progress = progress_cls(dsn=settings.REDIS_URL, key=f"meilisync:progress:{source.pk}")
        source_cls = get_source(source.type)
        current_progress = await progress.get()
        tables_map = {sync.table: sync.pk for sync in syncs}
        source_obj = source_cls(
            progress=current_progress,
            tables=list(tables_map.keys()),
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
            api_url=settings.MEILI_API_URL,
            api_key=settings.MEILI_API_KEY,
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

        @functools.lru_cache()
        def get_sync(table):
            for sync in sync_settings:
                if sync.table == table:
                    return sync

        async def sync_data():
            logger.info(
                f'Start increment sync data from "{source.label}" to'
                f" MeiliSearch, tables: {list(tables_map.keys())}..."
            )
            async for event in source_obj:
                if isinstance(event, Event):
                    sync = get_sync(event.table)
                    if sync:
                        await meili.handle_event(event, sync)
                        async with lock:
                            stats.setdefault(tables_map[sync.table], 0)
                            stats[tables_map[sync.table]] += 1
                await progress.set(**event.progress)

        async def save_stats():
            while True:
                await asyncio.sleep(60)
                async with lock:
                    objs = []
                    for sync_id, count in stats.items():
                        objs.append(SyncLog(sync_id=sync_id, count=count))
                    if objs:
                        await SyncLog.bulk_create(objs)
                        stats.clear()

        cls._tasks[source.pk] = {
            "task": asyncio.ensure_future(sync_data()),
            "meili": meili,
        }
        asyncio.ensure_future(save_stats())

    @classmethod
    def shutdown(cls):
        for task in cls._tasks.values():
            task["task"].cancel()

    @classmethod
    def remove_source(cls, source_id: int):
        if source_id in cls._tasks:
            cls._tasks[source_id]["task"].cancel()
            del cls._tasks[source_id]

    @classmethod
    async def restart_source(cls, source: Source):
        logger.info(f'Restart source "{source.label}"...')
        source_id = source.pk
        cls.remove_source(source_id)
        await cls._start_source(source)
