DELETE FROM item_price_history_i18n
WHERE price_time < NOW() - INTERVAL '14 days'