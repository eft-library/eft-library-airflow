WITH emails AS (
    SELECT email FROM tkl_user
),
post_counts AS (
    SELECT
        writer AS email,
        SUM(count) AS total_posts
    FROM (
        SELECT writer, COUNT(*) AS count FROM tkl_board_forum WHERE writer IN (SELECT email FROM emails) GROUP BY writer
        UNION ALL
        SELECT writer, COUNT(*) AS count FROM tkl_board_tip WHERE writer IN (SELECT email FROM emails) GROUP BY writer
        UNION ALL
        SELECT writer, COUNT(*) AS count FROM tkl_board_pvp WHERE writer IN (SELECT email FROM emails) GROUP BY writer
        UNION ALL
        SELECT writer, COUNT(*) AS count FROM tkl_board_pve WHERE writer IN (SELECT email FROM emails) GROUP BY writer
        UNION ALL
        SELECT writer, COUNT(*) AS count FROM tkl_board_question WHERE writer IN (SELECT email FROM emails) GROUP BY writer
        UNION ALL
        SELECT writer, COUNT(*) AS count FROM tkl_board_arena WHERE writer IN (SELECT email FROM emails) GROUP BY writer
    ) AS combined_counts
    GROUP BY writer
),
comment_counts AS (
    SELECT user_email AS email, COUNT(*) AS total_comments
    FROM tkl_comments
    WHERE user_email IN (SELECT email FROM emails)
    GROUP BY user_email
)
INSERT INTO tkl_user_post_statistics (user_email, post_count, comment_count)
SELECT
    emails.email,
    COALESCE(post_counts.total_posts, 0),
    COALESCE(comment_counts.total_comments, 0)
FROM emails
LEFT JOIN post_counts ON emails.email = post_counts.email
LEFT JOIN comment_counts ON emails.email = comment_counts.email
ON CONFLICT (user_email) DO UPDATE SET
    post_count = EXCLUDED.post_count,
    comment_count = EXCLUDED.comment_count;