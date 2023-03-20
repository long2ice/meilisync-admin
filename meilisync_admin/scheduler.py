import asyncio
from asyncio import Task
from typing import Dict

from loguru import logger
from meilisync.discover import get_progress
from meilisync.enums import EventType, ProgressType
from meilisync.event import EventCollection
from meilisync.meili import Meili
from meilisync.schemas import Event
from meilisync.settings import Sync as SyncSettings

from meilisync_admin.models import Source, Sync, SyncLog
from meilisync_admin.settings import settings


class Scheduler:
    _tasks: Dict[int, Task] = {}

    @classmethod
    async def startup(cls):
        sources = await Source.all()
        for source in sources:
            await cls._start_source(source)

    @classmethod
    async def _start_source(cls, source: Source):
        stats: Dict[str, Dict[EventType, int]] = {}
        lock = asyncio.Lock()
        progress = get_progress(ProgressType.redis)(
            dsn=settings.REDIS_URL, key=f"meilisync:progress:{source.pk}"
        )
        current_progress = await progress.get()
        collections_map = {}
        tables_sync_settings_map = {}
        tables_sync_map = {}
        tables_map_reverse = {}
        meili_map: Dict[Sync, Meili] = {}
        sync_settings = []
        syncs = await Sync.filter(enabled=True, source=source).all().select_related("meilisearch")
        for sync in syncs:
            tables_map_reverse[sync.pk] = sync.table
            sync_setting = SyncSettings(
                table=sync.table,
                pk=sync.primary_key,
                full=sync.full_sync,
                index=sync.index,
                fields=sync.fields,
            )
            tables_sync_settings_map[sync.table] = sync_setting
            tables_sync_map[sync.table] = sync
            collections_map[sync_setting] = EventCollection()
            meili_map[sync_setting] = sync.meili_client
            sync_settings.append(
                sync_setting,
            )
        source_obj = source.get_source(current_progress, list(tables_sync_settings_map.keys()))
        if not current_progress:
            for ss in sync_settings:
                meili = meili_map[ss]
                if ss.full:
                    data = await source_obj.get_full_data(ss)
                    if data:
                        await meili.add_full_data(ss.index_name, ss.pk, data)
                        logger.info(
                            f'Full data sync for table "{source.label}.{ss.table}" '
                            f"done! {len(data)} documents added."
                        )
                    else:
                        logger.info(
                            f'Full data sync for table "{source.label}.{ss.table}" '
                            f"done! No data found."
                        )

        async def start_interval():
            async def _(m: Meili, c: EventCollection, interval: int):
                while True:
                    await asyncio.sleep(interval)
                    try:
                        async with lock:
                            await m.handle_events(c)
                            await progress.set(**current_progress)
                    except Exception as e:
                        logger.exception(e)
                        logger.error(f"Error when insert data to MeiliSearch: {e}")

            for s in syncs:
                meilisync = s.meilisearch
                insert_interval = meilisync.insert_interval
                if not insert_interval:
                    continue
                asyncio.ensure_future(_(meili_map[s], collections_map[s], insert_interval))

        asyncio.ensure_future(start_interval())

        async def sync_data():
            logger.info(
                f'Start increment sync data from "{source.label}" to'
                f" MeiliSearch, tables: {', '.join(tables_sync_settings_map.keys())}..."
            )
            async for event in source_obj:
                if settings.DEBUG:
                    logger.debug(event)
                if not isinstance(event, Event):
                    continue
                ss_ = tables_sync_settings_map[event.table]
                if not ss_:
                    continue
                m = meili_map[ss_]
                s = tables_sync_map[event.table]
                meilisearch = s.meilisearch
                if not meilisearch.insert_size and not meilisearch.insert_interval:
                    async with lock:
                        stats.setdefault(s.pk, {}).setdefault(event.type, 0)
                        stats[s.pk][event.type] += 1
                        await m.handle_event(event, ss_)
                        await progress.set(**event.progress)
                else:
                    collection = collections_map[ss_]
                    collection.add_event(ss_, event)
                    if collection.size >= meilisearch.insert_size:
                        async with lock:
                            await m.handle_events(collection)
                            await progress.set(**current_progress)

        async def save_stats():
            while True:
                await asyncio.sleep(60)
                async with lock:
                    objs = []
                    for sync_id, events in stats.items():
                        total = 0
                        for event_type, count in events.items():
                            total += count
                            objs.append(SyncLog(sync_id=sync_id, count=count, type=event_type))
                        stats_str = ", ".join(
                            f"{event_type.name}: {count}" for event_type, count in events.items()
                        )
                        logger.info(
                            f'Save {total} sync logs for table "{source.label}'
                            f'.{tables_map_reverse[sync_id]}", {stats_str}'
                        )
                    if not objs:
                        continue
                    await SyncLog.bulk_create(objs)
                    stats.clear()

        cls._tasks[source.pk] = asyncio.ensure_future(sync_data())
        asyncio.ensure_future(save_stats())

    @classmethod
    def shutdown(cls):
        for task in cls._tasks.values():
            task.cancel()

    @classmethod
    def remove_source(cls, source_id: int):
        if source_id in cls._tasks:
            cls._tasks[source_id].cancel()
            del cls._tasks[source_id]

    @classmethod
    async def restart_source(cls, source: Source):
        logger.info(f'Restart source "{source.label}"...')
        source_id = source.pk
        cls.remove_source(source_id)
        await cls._start_source(source)
