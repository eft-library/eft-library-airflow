DELETE FROM community_posts_hot_issue h
USING community_posts cp
LEFT JOIN (
    SELECT cpr.post_id,
           SUM(CASE WHEN cpr.reaction_type = 1 THEN 1 ELSE 0 END) -
           SUM(CASE WHEN cpr.reaction_type = 0 THEN 1 ELSE 0 END) AS reaction_diff
    FROM community_posts_reactions cpr
    GROUP BY cpr.post_id
) t ON h.post_id = t.post_id
WHERE h.post_id = cp.id
  AND (
        cp.delete_by_user = true
        OR cp.delete_by_admin = true
        OR (cp.delete_by_user = false AND cp.delete_by_admin = false AND t.reaction_diff < 10)
      );
