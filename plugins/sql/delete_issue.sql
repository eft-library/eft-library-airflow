delete from tkl_board_issue
where board_id in (
    select id from tkl_board_union where like_count < 10
);