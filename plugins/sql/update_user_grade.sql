WITH total_scores AS (
    SELECT
        tkl_user.email,
        (tkl_user.attendance_count * 5) +
        COALESCE(tkl_user_post_statistics.post_count, 0) * 10 +
        COALESCE(tkl_user_post_statistics.comment_count, 0) * 5 AS total_score
    FROM
        tkl_user
    LEFT JOIN
        tkl_user_post_statistics
    ON
        tkl_user.email = tkl_user_post_statistics.user_email
),
graded_users AS (
    SELECT
        ts.email,
        ts.total_score,
        g.id AS grade_id,
        ROW_NUMBER() OVER (PARTITION BY ts.email ORDER BY g.score DESC) as rn
    FROM
        total_scores ts
    JOIN
        tkl_user_grade g
    ON
        ts.total_score >= g.score
)
UPDATE tkl_user
SET grade = gu.grade_id
FROM (
    SELECT
        email, grade_id
    FROM
        graded_users
    WHERE
        rn = 1
) gu
WHERE
    tkl_user.email = gu.email;