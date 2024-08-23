WITH emails AS (
    SELECT email
    FROM tkl_user
),
post_counts AS (
    SELECT writer AS email, COUNT(*) AS total_posts
    FROM tkl_board_union
    WHERE writer IN (SELECT email FROM emails)
    GROUP BY writer
),
comment_counts AS (
    SELECT user_email AS email, COUNT(DISTINCT tkl_board_union.id) AS total_comments
    FROM tkl_comments
    JOIN tkl_board_union
    ON tkl_comments.board_id = tkl_board_union.id
    WHERE tkl_comments.user_email IN (SELECT email FROM emails)
      AND tkl_comments.is_delete_by_user = FALSE
      AND tkl_comments.is_delete_by_admin = FALSE
    GROUP BY user_email
)
INSERT INTO tkl_user_post_statistics (user_email, post_count, comment_count)
SELECT e.email,
       COALESCE(p.total_posts, 0) AS post_count,
       COALESCE(c.total_comments, 0) AS comment_count
FROM emails e
LEFT JOIN post_counts p ON e.email = p.email
LEFT JOIN comment_counts c ON e.email = c.email
ON CONFLICT (user_email)
DO UPDATE SET
    post_count = EXCLUDED.post_count,
    comment_count = EXCLUDED.comment_count;
