-- SELECT * FROM user_master;


-- SELECT
--     um.zone,
--     um.region,
--     r.rm_id,
--     AVG(
--         CASE
--             -- Handle values like "13/20"
--             WHEN r.score_json::jsonb
--                  -> 'summery_score'
--                  -> 'data'
--                  ->> 'final_score' LIKE '%/%'
--             THEN
--                 split_part(
--                     r.score_json::jsonb
--                     -> 'summery_score'
--                     -> 'data'
--                     ->> 'final_score',
--                     '/',
--                     1
--                 )::numeric
--                 /
--                 split_part(
--                     r.score_json::jsonb
--                     -> 'summery_score'
--                     -> 'data'
--                     ->> 'final_score',
--                     '/',
--                     2
--                 )::numeric

--             -- Handle normal numeric values like "0.65", "78", etc.
--             ELSE
--                 (r.score_json::jsonb
--                  -> 'summery_score'
--                  -> 'data'
--                  ->> 'final_score')::numeric
--         END
--     ) AS avg_rm_score
-- FROM investigen.recorded_info r
-- JOIN investigen.user_master um
--     ON r.rm_id = um.rm_id
-- WHERE r.score_json IS NOT NULL
--   AND um.zone IS NOT NULL
--   AND um.region IS NOT NULL
-- GROUP BY
--     um.zone,
--     um.region,
--     r.rm_id
-- ORDER BY avg_rm_score DESC;


-- SELECT DISTINCT superadminid
-- FROM investigen.user_master;


-- SELECT DISTINCT region FROM investigen.user_master;

-- SELECT rm_id, region, superadminid
-- FROM investigen.user_master
-- WHERE superadminid = 'SAB001';






-- SELECT
--     um.rm_id,
--     um.name,
--     ri.score_json
-- FROM investigen.transaction_info ti
-- JOIN investigen.user_master um
--     ON ti.rm_id = um.rm_id
-- JOIN investigen.recorded_info ri
--     ON ti.record_id = ri.record_id
-- WHERE um.region = 'Mumbai'
--   AND um.rm_id <> 'SAB001'
--   AND um.superadminid = 'SAB001'
--   AND ri.score_json IS NOT NULL;



-- SELECT
--         r.rm_id,
--         r.score_json,
--         um.zone,
--         um.region
--     FROM investigen.recorded_info r
--     JOIN investigen.user_master um
--         ON r.rm_id = um.rm_id
--     WHERE r.score_json IS NOT NULL
--       AND um.zone IS NOT NULL
--       AND um.region IS NOT NULL;





-- Best, Worst and Average Score Based on the RM_id -->

-- WITH rm_scores AS (
--     SELECT
--         um.rm_id,
--         um.name,
--         CASE
--             WHEN ri.score_json::jsonb
--                  -> 'summery_score'
--                  -> 'data'
--                  ->> 'final_score' LIKE '%/%'
--             THEN
--                 split_part(
--                     ri.score_json::jsonb
--                     -> 'summery_score'
--                     -> 'data'
--                     ->> 'final_score',
--                     '/',
--                     1
--                 )::numeric
--                 /
--                 split_part(
--                     ri.score_json::jsonb
--                     -> 'summery_score'
--                     -> 'data'
--                     ->> 'final_score',
--                     '/',
--                     2
--                 )::numeric
--             ELSE
--                 (ri.score_json::jsonb
--                  -> 'summery_score'
--                  -> 'data'
--                  ->> 'final_score')::numeric
--         END AS score
--     FROM investigen.transaction_info ti
--     JOIN investigen.user_master um
--         ON ti.rm_id = um.rm_id
--     JOIN investigen.recorded_info ri
--         ON ti.record_id = ri.record_id
--     WHERE um.region = 'Mumbai'
--       AND um.rm_id <> 'SAB001'
--       AND um.superadminid = 'SAB001'
--       AND ri.score_json IS NOT NULL
-- )

-- SELECT
--     AVG(score)     AS average_score,
--     MAX(score)     AS best_score,
--     MIN(score)     AS worst_score
-- FROM rm_scores;




-- SELECT
--     um.rm_id,
--     um.name,
--     ri.score_json
-- FROM investigen.transaction_info ti
-- JOIN investigen.user_master um ON ti.rm_id = um.rm_id
-- JOIN investigen.recorded_info ri ON ti.record_id = ri.record_id
-- WHERE um.region = 'Mumbai'
--   AND um.rm_id <> 'SAB001'
--   AND um.superadminid = 'SAB001'
--   AND ri.score_json IS NOT NULL;

-- SELECT
--         r.rm_id,
--         r.score_json,
--         um.zone,
--         um.region
--     FROM investigen.recorded_info r
--     JOIN investigen.user_master um
--         ON r.rm_id = um.rm_id
--     WHERE r.score_json IS NOT NULL
--       AND um.zone IS NOT NULL
--       AND um.region IS NOT NULL;




-- SELECT
--             ri.score_json
--         FROM investigen.transaction_info ti
--         JOIN investigen.user_master um ON ti.rm_id = um.rm_id
--         JOIN investigen.recorded_info ri ON ti.record_id = ri.record_id
--         WHERE um.region = 'Mumbai'
--           AND um.rm_id <> 'SAB001'
--           AND um.superadminid = 'SAB001' 
--           AND ri.score_json IS NOT NULL;



-- SELECT 
--     um.rm_id, 
--     ri.score_json
-- FROM investigen.user_master um
-- LEFT JOIN investigen.transaction_info ti 
--     ON ti.rm_id = um.rm_id
-- LEFT JOIN investigen.recorded_info ri 
--     ON ti.record_id = ri.record_id
-- WHERE um.region = %s
--   AND um.superadminid = %s;






-- SELECT rm_id, COUNT(*) 
-- FROM investigen.transaction_info
-- GROUP BY rm_id
-- ORDER BY count DESC;





-- SELECT rm_id, COUNT(DISTINCT record_id)
-- FROM investigen.transaction_info
-- GROUP BY rm_id;










  







