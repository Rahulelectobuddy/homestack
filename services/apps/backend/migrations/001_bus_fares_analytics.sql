-- Migration: Create bus_fares_analytics table
CREATE TABLE IF NOT EXISTS bus_fares_analytics (
    id SERIAL PRIMARY KEY,
    scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
    scrape_date DATE NOT NULL,
    travel_date DATE NOT NULL,
    days_until_travel INT NOT NULL,
    operator_name VARCHAR(100) NOT NULL,
    bus_type VARCHAR(100),
    seat_type VARCHAR(50) NOT NULL,
    price NUMERIC(10, 2) NOT NULL,
    available_seats INT DEFAULT 0,
    has_toilet BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bus_fares_dates ON bus_fares_analytics (scrape_date, travel_date);
CREATE INDEX IF NOT EXISTS idx_bus_fares_seat_type ON bus_fares_analytics (seat_type);
