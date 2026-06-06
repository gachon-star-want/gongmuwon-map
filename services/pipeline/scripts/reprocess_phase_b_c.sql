-- Phase D: 전수 재처리 SQL
-- Phase B~C 변경사항을 기존 DB에 적용

-- 1. is_large_chain 리셋 (Phase B - 확장된 체인 목록이 다음 파이프라인 실행 시 재검출됨)
UPDATE places
SET is_large_chain = FALSE,
    chain_brand = NULL,
    chain_scale = NULL
WHERE is_large_chain = TRUE;

-- 2. matched = FALSE로 리셋 (Phase C-1 - 거리 제약 변경으로 재평가 필요)
-- Kakao placeId가 있는 place는 유지하되, 없거나 의심스러운 것은 재매칭
UPDATE places
SET valid_place = FALSE
WHERE is_large_chain = FALSE
  AND kakao_place_id IS NULL;

-- 3. 재처리 후 실행할 검증 쿼리 (0건이 목표)
-- SELECT COUNT(*) AS region_mismatch_count
-- FROM place_visits pv
-- JOIN agencies a ON a.id = pv.agency_id
-- JOIN places p ON p.id = pv.place_id
-- WHERE a.parent_region IS NOT NULL
--   AND p.road_address_part IS NOT NULL
--   AND a.parent_region NOT IN ('문화체육관광부','기후에너지환경부','대통령실','교육부',
--     '행정안전부','국토교통부','산업통상자원부','보건복지부','고용노동부','법무부',
--     '기획재정부','외교부','과학기술정보통신부','농림축산식품부','중소벤처기업부',
--     '해양수산부','환경부','통일부','국방부','여성가족부','국가보훈부','대한민국');
