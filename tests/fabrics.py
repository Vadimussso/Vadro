from faker import Faker
from faker_vehicle import VehicleProvider

fake = Faker()
fake.add_provider(VehicleProvider)


def ad_fabric():
    return {
        "vin": fake.unique.vin(),
        "vrc": fake.bothify(text='##??######').upper(),
        "license_plate": fake.unique.license_plate(),
        "brand": fake.vehicle_make(),
        "model": fake.vehicle_model(),
        "mileage": fake.random_int(min=0, max=200000),
        "engine_capacity": fake.random_int(min=0, max=5000),
        "price": fake.random_int(min=1000, max=50000),
        "description": fake.sentence(nb_words=5),
        "city": fake.city(),
        "phone": fake.phone_number()
    }


def user_fabric(is_admin=False):
    return {
            "email": fake.ascii_email(),
            "name": fake.first_name(),
            "surname": fake.last_name(),
            "password": fake.password(length=10),
            "is_admin": is_admin
        }