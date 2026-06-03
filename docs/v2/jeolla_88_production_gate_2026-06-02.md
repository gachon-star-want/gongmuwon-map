# 전라도권 표적 Production Gate Report

주의: 이 리포트는 전라도권 88/88 목표 중 2026-06-02에 신규 production 적재 가능한
기관만 대상으로 한 표적 gate report이며, 원문 행·개인정보·연결 문자열을 포함하지 않는다.

## 승인

- 사용자 명시 승인: 전라도권 dry-run 성공 및 normalized visits > 0 기관 production DB write.
- 원본 파일 재배포: 하지 않음. `--allow-missing-r2`로 factual row만 DB에 적재.
- 개인정보 처리: `docs/LEGAL_PRIVACY.md` 기준에 따라 적재 전 마스킹.

## Dry Run Evidence

| 기관 | source | posts_fetched | raw_parsed_rows | parsed_rows | normalized_visits | places_seen | 결과 |
|---|---|---:|---:|---:|---:|---:|---|
| 전라남도청 | 공식 HWP attachment board | 10 | 107 | 105 | 103 | 86 | success |
| 나주시청 | 공식 PDF attachment board | 10 | 380 | 380 | 378 | 239 | success |

## Technical Gate

| 게이트 | 상태 |
|---|---|
| 공식 출처 확인 | 완료 |
| 명시적 강한 재이용 제한 없음 | 완료 |
| parser dry-run success | 완료 |
| normalized visits > 0 | 완료 |
| production write 사용자 승인 | 완료 |
| 원본 파일 재배포 방지 | 완료 |
| privacy validation 통과 | 완료 |

서비스 주입 판정: production 주입 검토 가능
