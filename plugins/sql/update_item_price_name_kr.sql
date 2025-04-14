update tkl_item_price tip
set item_name_kr = ti.name_kr
from tkl_item ti
where tip.id = ti.id;