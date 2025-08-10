DELETE FROM community_posts_hot_issue h
USING (
    SELECT cpr.post_id
    FROM community_posts_reactions cpr
    GROUP BY cpr.post_id
    HAVING
        SUM(CASE WHEN cpr.reaction_type = 1 THEN 1 ELSE 0 END) -
        SUM(CASE WHEN cpr.reaction_type = 0 THEN 1 ELSE 0 END) < 10
) t
WHERE h.post_id = t.post_id;
