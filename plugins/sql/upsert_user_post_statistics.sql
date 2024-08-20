WITH emails AS (SELECT email
                FROM tkl_user),
     post_counts AS (SELECT writer     AS email,
                            SUM(count) AS total_posts
                     FROM (SELECT writer, COUNT(*) AS count
                           FROM tkl_board_forum
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer
                           UNION ALL
                           SELECT writer, COUNT(*) AS count
                           FROM tkl_board_tip
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer
                           UNION ALL
                           SELECT writer, COUNT(*) AS count
                           FROM tkl_board_pvp
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer
                           UNION ALL
                           SELECT writer, COUNT(*) AS count
                           FROM tkl_board_pve
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer
                           UNION ALL
                           SELECT writer, COUNT(*) AS count
                           FROM tkl_board_question
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer
                           UNION ALL
                           SELECT writer, COUNT(*) AS count
                           FROM tkl_board_arena
                           WHERE writer IN (SELECT email FROM emails)
                           GROUP BY writer) AS combined_counts
                     GROUP BY writer),
     comment_counts AS (select email, count(*) as total_comments
                        from (SELECT user_email AS email,
                                     CASE
                                         WHEN tkl_comments.board_type = 'forum' THEN tkl_board_forum.id
                                         WHEN tkl_comments.board_type = 'arena' THEN tkl_board_arena.id
                                         WHEN tkl_comments.board_type = 'tip' THEN tkl_board_tip.id
                                         WHEN tkl_comments.board_type = 'pvp' THEN tkl_board_pvp.id
                                         WHEN tkl_comments.board_type = 'pve' THEN tkl_board_pve.id
                                         WHEN tkl_comments.board_type = 'question' THEN tkl_board_question.id
                                         END    AS post_id
                              FROM tkl_comments
                                       left join tkl_board_tip on tkl_comments.board_id = tkl_board_tip.id
                                       left join tkl_board_arena on tkl_comments.board_id = tkl_board_arena.id
                                       left join tkl_board_pvp on tkl_comments.board_id = tkl_board_pvp.id
                                       left join tkl_board_pve on tkl_comments.board_id = tkl_board_pve.id
                                       left join tkl_board_forum on tkl_comments.board_id = tkl_board_forum.id
                                       left join tkl_board_question on tkl_comments.board_id = tkl_board_question.id
                              WHERE user_email IN (SELECT email FROM emails)
                                and is_delete_by_user = false
                                and is_delete_by_admin = false) as a
                        where post_id is not null
                        group by email)
INSERT
INTO tkl_user_post_statistics (user_email, post_count, comment_count)
SELECT emails.email,
       COALESCE(post_counts.total_posts, 0),
       COALESCE(comment_counts.total_comments, 0)
FROM emails
         LEFT JOIN post_counts ON emails.email = post_counts.email
         LEFT JOIN comment_counts ON emails.email = comment_counts.email
ON CONFLICT (user_email) DO UPDATE SET post_count    = EXCLUDED.post_count,
                                       comment_count = EXCLUDED.comment_count;