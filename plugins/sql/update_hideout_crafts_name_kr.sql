update tkl_hideout_crafts thc
set name_kr = ti.name_kr
from tkl_item ti
where thc.reward_item_id = ti.id;