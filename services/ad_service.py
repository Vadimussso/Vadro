from fastapi import Depends
from repo.ad_repo import AdRepo
from entities.ad import Ad
from errors import UserRequiredError, ItemRequiredError
from typing import Protocol
from entities.user import User


class AdRepoProtocol(Protocol):
    def insert_ad(self, user_id: int, ad: Ad) -> int:
        pass

    def fetch_ad_data(self, ad_id: int | None, only_moderated: bool = False) -> list | dict:
        pass

    def moderate(self, item_id: int) -> None:
        pass


class AdService:

    def __init__(self, ad_repo: AdRepoProtocol = Depends(AdRepo)):
        self.ad_repo = ad_repo

    def add_ad(self, user_id: int | None, ad: Ad) -> int:

        if user_id is None:
            raise UserRequiredError()

        return self.ad_repo.insert_ad(user_id, ad)

    def read_ads(self, ad_id: int | None = None, only_moderated: bool = False) -> list | dict:

        items = self.ad_repo.fetch_ad_data(ad_id, only_moderated)

        if items is None:
            raise ItemRequiredError()

        return items

    def moderate(self, user: User | None, item_id: int) -> None:

        if not user:
            raise UserRequiredError("User is required")

        if not user.is_admin:
            raise PermissionError("Insufficient access rights")

        # fetching the item from db according item_id ID
        item = self.ad_repo.fetch_ad_data(item_id)

        if item is None:
            raise ItemRequiredError()

        # getting ID from item which was received according ID for moderation
        ad_id = item["id"]

        self.ad_repo.moderate(ad_id)