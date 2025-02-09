DELETE FROM tkl_item_price_history
WHERE price_time < NOW() - INTERVAL '30 days'