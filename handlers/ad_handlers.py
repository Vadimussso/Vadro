from fastapi import Depends, HTTPException, Request
from typing import Protocol
from entities.ad import Ad
from entities.user import User
from services.ad_service import AdService
from errors import UserRequiredError, ItemRequiredError


class AdServiceProtocol(Protocol):
    def add_ad(self, user_id: int | None, ad: Ad) -> int:
        pass

    def moderate(self, user: User | None, item_id: int | None) -> None:
        pass

    def read_ads(self, ad_id: int | None = None, only_moderated: bool = False) -> dict | list:
        pass


# @app.post("/ads")
def add_ad(ad: Ad, request: Request, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    user_id = getattr(request.state.user, 'id', None)

    try:
        ad_id = ad_service.add_ad(user_id, ad)
    except UserRequiredError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {"message": "Ad applied successfully", "id": ad_id}


def read_ads(ad_service: AdServiceProtocol = Depends(AdService)) -> list:
    items = ad_service.read_ads(only_moderated=True)

    return items


# @app.get("/ads/{item_id}")
def read_ad(item_id, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    try:
        item = ad_service.read_ads(item_id, only_moderated=True)
    except ItemRequiredError:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


# @app.post("/ads/{item_id}/moderate")
def moderate(item_id: int, request: Request, ad_service: AdServiceProtocol = Depends(AdService)) -> dict:
    user = getattr(request.state, 'user', None)

    try:
        ad_service.moderate(user, item_id)
    except UserRequiredError:
        raise HTTPException(status_code=401, detail="Unauthorized")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
    except ItemRequiredError:
        raise HTTPException(status_code=404, detail="Item not found")
    else:
        return {"message": "moderation_completed"}