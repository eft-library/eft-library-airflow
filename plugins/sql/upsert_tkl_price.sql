INSERT INTO tkl_item_price (
    id,
    item_name_en,
    item_image,
    trader,
    update_time
) VALUES (
    %s, %s, %s, %s, %s
)
ON CONFLICT (id) DO UPDATE SET
    item_name_en = EXCLUDED.item_name_en,
    item_image = EXCLUDED.item_image,
    trader = EXCLUDED.trader,
    update_time = EXCLUDED.update_time;
