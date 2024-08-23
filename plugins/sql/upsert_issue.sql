insert into tkl_board_issue (board_id, board_type, create_time)
select id, type, create_time
from tkl_board_union
where like_count >= 10
ON CONFLICT (board_id) DO UPDATE SET
    board_type  = EXCLUDED.board_type,
    create_time = EXCLUDED.create_time;