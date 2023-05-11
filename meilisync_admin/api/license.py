from fastapi import APIRouter

from meilisync_admin import license

router = APIRouter()


@router.get("", response_model=license.License)
async def get_license():
    return license.LICENSE
