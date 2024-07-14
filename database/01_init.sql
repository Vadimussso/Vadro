CREATE TABLE ads (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE,
    vin TEXT UNIQUE NOT NULL,
    vrc TEXT NOT NULL,
    license_plate TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    mileage INTEGER NOT NULL,
    engine_capacity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    description TEXT,
    city TEXT NOT NULL,
    phone TEXT NOT NULL,
    posted_at TIMESTAMP WITH TIME ZONE
);