DELETE
FROM tkl_board_issue
WHERE NOT EXISTS (SELECT 1
                  FROM tkl_board_union
                  WHERE tkl_board_union.id = tkl_board_issue.board_id);