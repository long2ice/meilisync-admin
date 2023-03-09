from meilisync.meili import Meili

from meilisync_admin.settings import settings

meili = Meili(
    api_url=settings.MEILI_API_URL,
    api_key=settings.MEILI_API_KEY,
)
