UPDATE boss_i18n
SET spawn_chance = (
  SELECT spawn_chance
  FROM boss_i18n
  WHERE id = 'bossKnight'
)
WHERE id in ('followerBigPipe', 'followerBirdEye');
