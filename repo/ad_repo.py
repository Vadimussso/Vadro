from fastapi import Depends
from db import get_db
from entities.ad import Ad
from datetime import datetime


class AdRepo:
    def __init__(self, db=Depends(get_db)):
        self.db = db

    def insert_ad(self, user_id: int, ad: Ad) -> int:
        # if id exist, ad applying is carry on
        with self.db.cursor() as cursor:
            # attempt to apply the ad:
            cursor.execute(
                """
                INSERT INTO ads (
                    created_at, vin, vrc, license_plate, brand, model, mileage, 
                    engine_capacity, price, description, city, phone, posted_at, author_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """,
                (
                    datetime.now(), ad.vin, ad.vrc, ad.license_plate, ad.brand,
                    ad.model, ad.mileage, ad.engine_capacity, ad.price,
                    ad.description, ad.city, ad.phone, datetime.now(), user_id
                )
            )
            self.db.commit()

            return cursor.fetchone()['id']

    def fetch_ad_data(self, ad_id: int | None = None, only_moderated: bool = False) -> list | dict:
        query = """
            SELECT id, vin, vrc, license_plate, brand, model, mileage, engine_capacity, price, description, city, phone, posted_at
                 FROM ads 
            """

        params = []
        conditions = []

        if ad_id is not None:
            conditions.append("id = %s")
            params.append(ad_id)

        if only_moderated:
            conditions.append("is_moderated = true")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with self.db.cursor() as cursor:
            cursor.execute(query, params)

            if ad_id:
                item = cursor.fetchone()
            else:
                item = cursor.fetchall()

        return item

    def moderate(self, item_id: int) -> None:
        with self.db.cursor() as cursor:
            cursor.execute(
                """
                UPDATE ads SET is_moderated = true
                WHERE id = %s 
                """,
                [item_id]
            )

            self.db.commit()