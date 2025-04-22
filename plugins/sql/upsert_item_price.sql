INSERT INTO item_price_i18n (
    id,
    name,
    image,
    trader,
    category,
    width,
    height,
    update_time
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    image = EXCLUDED.image,
    trader = EXCLUDED.trader,
    category = EXCLUDED.category,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    update_time = EXCLUDED.update_time;
