BEGIN;

CREATE TEMP TABLE removed_quest_objectives (
    objective_id text NOT NULL,
    quest_id text NOT NULL,
    PRIMARY KEY (objective_id, quest_id)
) ON COMMIT DROP;

INSERT INTO removed_quest_objectives (objective_id, quest_id)
VALUES
    ('5ac5e18c86f7743ebd6c9575', '5ac3467986f7741d651d6877'),
    ('5ac5ea0586f774609f36280c', '5ac346a886f7744e1b083d67'),
    ('5cb6f9c586f7740ace254c44', '5ac346a886f7744e1b083d67'),
    ('5ac5eee986f77401fd341c9e', '5ac3475486f7741d6224abd3'),
    ('5ac5ef2a86f7741c5804f9f5', '5ac3475486f7741d6224abd3'),
    ('5ac5ef5686f77416ca60f644', '5ac3475486f7741d6224abd3'),
    ('5ac5ef9886f7746e7a509a2d', '5ac3475486f7741d6224abd3'),
    ('5ae4514986f7740e915d218c', '5ae448e586f7744dcf0c2a67'),
    ('5ae9e58886f77423572433f5', '5ae449d986f774453a54a7e1'),
    ('5b47899386f77470315db7f3', '5b47891f86f7744d1b23c571'),
    ('5b4789df86f77468074619d7', '5b47891f86f7744d1b23c571'),
    ('5b478a2186f77468074619da', '5b47891f86f7744d1b23c571'),
    ('5b478a6c86f7744d190d8f4d', '5b47891f86f7744d1b23c571'),
    ('62a7004c1c307729c3264f9a', '5b47891f86f7744d1b23c571'),
    ('5c0bdf2c86f7746f016734a8', '5c0bde0986f77479cf22c2f8'),
    ('5c137b8886f7747ae3220ff4', '5c0bde0986f77479cf22c2f8'),
    ('5c137ef386f7747ae10a821e', '5c0bde0986f77479cf22c2f8'),
    ('65e0812209dffc3fd97b99e8', '5c0bde0986f77479cf22c2f8'),
    ('5c0be2b486f7747bcb347d58', '5c0be13186f7746f016734aa'),
    ('5c112dc486f77465686bff38', '5c112d7e86f7740d6f647486'),
    ('5ca7254e86f7740d424a2043', '5c1141f386f77430ff393792'),
    ('5ca7258986f7740d424a2044', '5c1141f386f77430ff393792'),
    ('62a700893e015d7ce1151d90', '5c1141f386f77430ff393792'),
    ('62a700a37230237f257cac2d', '5c1141f386f77430ff393792'),
    ('5d66741c86f7744a2e70f039', '5d25e2c386f77443e7549029'),
    ('608c187853b9dd01a116f480', '608974af4b05530f55550c21'),
    ('60e84ba726b88043510e0ad8', '60e71d6d7fcf9c556f325055'),
    ('63a9b52b009ffc6a551631a7', '63a9b36cc31b00242d28a99f'),
    ('63a9b591da7999196148ba63', '63a9b36cc31b00242d28a99f'),
    ('63a9b5b2813bba58a50c9eeb', '63a9b36cc31b00242d28a99f'),
    ('64e7ba4a6393886f74119f3d', '64e7b971f9d6fa49d6769b44'),
    ('65bb698050fd7c32f5d666d1', '64e7b971f9d6fa49d6769b44'),
    ('65bb6a61a845e4eb51390b4e', '64e7b971f9d6fa49d6769b44'),
    ('6580130847df99b0741919f0', '6578eb36e5020875d64645cd'),
    ('6578ec473dbd035d04531a93', '6578ec473dbd035d04531a8d'),
    ('6578ec473dbd035d04531a94', '6578ec473dbd035d04531a8d'),
    ('6578ed62da32cab3f79bb022', '6578ec473dbd035d04531a8d'),
    ('6578ed7792685671c65edf07', '6578ec473dbd035d04531a8d'),
    ('669fb64aa7e974b27a9c7e1f', '669fa39b91b0a8c9680fc467'),
    ('669fb64b5150ba5196dae347', '669fa39b91b0a8c9680fc467'),
    ('66aa74571e5e199ecd094f1e', '66aa74571e5e199ecd094f18');

-- 실제 삭제될 목표 41개를 먼저 확인한다.
SELECT qo.*
FROM quest_objectives qo
JOIN removed_quest_objectives r
  ON r.objective_id = qo.objective_id
 AND r.quest_id = qo.quest_id
ORDER BY qo.quest_id, qo.sort_order, qo.objective_id;

DO $$
DECLARE
    matched_count integer;
BEGIN
    SELECT count(*)
    INTO matched_count
    FROM quest_objectives qo
    JOIN removed_quest_objectives r
      ON r.objective_id = qo.objective_id
     AND r.quest_id = qo.quest_id;

    IF matched_count <> 41 THEN
        RAISE EXCEPTION 'Expected 41 quest objectives, but matched %', matched_count;
    END IF;
END
$$;

-- 라이브맵 상세는 point보다 먼저 삭제해야 한다.
DELETE FROM live_map_point_details d
USING live_map_points p, removed_quest_objectives r
WHERE d.point_id = p.id
  AND p.objective_id = r.objective_id
  AND p.quest_id = r.quest_id;

DELETE FROM live_map_points p
USING removed_quest_objectives r
WHERE p.objective_id = r.objective_id
  AND p.quest_id = r.quest_id;

DELETE FROM quest_objective_items i
USING removed_quest_objectives r
WHERE i.objective_id = r.objective_id;

DELETE FROM quest_objective_required_keys k
USING removed_quest_objectives r
WHERE k.objective_id = r.objective_id;

DELETE FROM quest_objective_maps m
USING removed_quest_objectives r
WHERE m.objective_id = r.objective_id;

DELETE FROM quest_objectives qo
USING removed_quest_objectives r
WHERE qo.objective_id = r.objective_id
  AND qo.quest_id = r.quest_id;

COMMIT;
