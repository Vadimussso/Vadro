from pydantic import BaseModel


class Ad(BaseModel):
    vin: str
    vrc: str
    license_plate: str
    brand: str
    model: str
    mileage: int
    engine_capacity: int
    price: int
    description: str
    city: str
    phone: str