# Bus Scraper Migrations

This directory contains database schema migrations specific to the `bus-scraper` service.

## Usage
If `bus-scraper` uses its own relational table (e.g. tracking scrape jobs or raw results staging), schema migration scripts (Alembic / SQL) should be stored here and applied during service initialization.
