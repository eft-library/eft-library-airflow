delete from tkl_board_issue
where board_id in (
    select id from tkl_board_forum where like_count < 10
    union all
    select id from tkl_board_tip where like_count < 10
    union all
    select id from tkl_board_arena where like_count < 10
    union all
    select id from tkl_board_question where like_count < 10
    union all
    select id from tkl_board_pve where like_count < 10
    union all
    select id from tkl_board_pvp where like_count < 10
);