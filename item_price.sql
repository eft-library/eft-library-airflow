create table if not exists item_prices
(
    item_id text,
    game_mode text, -- 'pve' | 'pvp'
    highest_trader_price numeric,
    highest_trader_id text,
    flea_market_price numeric,
    trader_count integer,
    has_flea boolean,
    update_time timestamptz default now(),
    primary key (item_id, game_mode)
);

create table if not exists item_trader_prices
(
    id text primary key,
    item_id text,
    game_mode text, -- 'pve' | 'pvp'
    trader_id text,
    price numeric
);
create index idx_item_trader_prices_item_id on item_trader_prices(item_id);
create index idx_item_trader_prices_trader_id on item_trader_prices(trader_id);
create index idx_item_trader_prices_item_mode on item_trader_prices(item_id, game_mode);

create table if not exists item_price_history
(
    item_id text,
    price integer,
    game_mode text,
    price_time timestamptz default now(),
    PRIMARY KEY (item_id, game_mode, price_time)
);
create index idx_item_price_history_time on item_price_history(price_time desc);