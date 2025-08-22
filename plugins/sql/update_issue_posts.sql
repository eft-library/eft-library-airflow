INSERT INTO community_posts_hot_issue (post_id, issue_time)
SELECT cpr.post_id, now()
FROM community_posts_reactions cpr
JOIN community_posts cp
  ON cpr.post_id = cp.id
WHERE cp.delete_by_user = false
  AND cp.delete_by_admin = false
GROUP BY cpr.post_id
HAVING
    SUM(CASE WHEN cpr.reaction_type = 1 THEN 1 ELSE 0 END) -
    SUM(CASE WHEN cpr.reaction_type = 0 THEN 1 ELSE 0 END) >= 10
ON CONFLICT (post_id) DO NOTHING;
