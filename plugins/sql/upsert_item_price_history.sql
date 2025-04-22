INSERT INTO item_price_history_i18n (
   id,
   price,
   price_type,
   price_time,
   execute_time
)
VALUES (%s, %s, %s, %s, %s)
ON CONFLICT (id, price_type, price_time) DO UPDATE SET
    price = EXCLUDED.price,
    execute_time = EXCLUDED.execute_time