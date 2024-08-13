DELETE
FROM tkl_board_issue
WHERE NOT EXISTS (SELECT 1
                  FROM tkl_board_forum
                  WHERE tkl_board_forum.id = tkl_board_issue.board_id
                  union all
                  SELECT 1
                  FROM tkl_board_tip
                  WHERE tkl_board_tip.id = tkl_board_issue.board_id
                  union all
                  SELECT 1
                  FROM tkl_board_arena
                  WHERE tkl_board_arena.id = tkl_board_issue.board_id
                  union all
                  SELECT 1
                  FROM tkl_board_pvp
                  WHERE tkl_board_pvp.id = tkl_board_issue.board_id
                  union all
                  SELECT 1
                  FROM tkl_board_pve
                  WHERE tkl_board_pve.id = tkl_board_issue.board_id
                  union all
                  SELECT 1
                  FROM tkl_board_question
                  WHERE tkl_board_question.id = tkl_board_issue.board_id);