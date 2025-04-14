update tkl_hideout_item_require thi
set name_kr = ti.name_kr
from tkl_item ti
where thi.item_id = ti.id;