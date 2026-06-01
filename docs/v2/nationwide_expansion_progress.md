# 전국 확장 진행 기록

- 최종 업데이트: 2026-06-01
- 원칙: 운영·공개 데이터는 한국어 원문과 한국어 라벨을 기준으로 저장·표시한다. 내부 정렬·호환용 enum 코드는 공개 라벨(`gov_tier_label`, `branch_label`, `jurisdiction_type_label`, `verification_status_label`)과 함께만 노출한다.
- 금지선: 운영 DB 쓰기, 배포, 원본 삭제, irreversible cleanup은 명시 승인 전까지 하지 않는다.

## 현재 범위

전국 확장 작업은 아직 완료되지 않았다. 현재 코드에는 P1 지방자치단체·의회 486개, P2 중앙행정기관·독립기관 60개, P3 지정 공공기관 342개, P4 지방공공기관 1,312개를 합친 **2,200개 기관**의 taxonomy 스텁과 출처 등록부가 반영돼 있다. 실제 크롤·적재 대상은 공식 업무추진비 원문 URL, 공공누리 제1유형 또는 동등한 자유이용 근거, 첨부/상세 수집 접근성이 검증된 기관으로만 제한한다.

P1 지방자치단체·의회 범위는 행정안전부 공공데이터포털의 17개 시도 + 226개 시·군·자치구 기준을 따른다(`https://www.data.go.kr/data/15059715/fileData.do`). 집행기관과 의회를 각각 별도 기관으로 본 **486개 기관**이다. 제주 제주시·서귀포시는 기초지자체가 아닌 행정시이므로 별도 agency/council로 만들지 않는다. 현재 P1 공식 출처 검증이 남은 비수도권 기관은 **282개**이고, 비수도권 법적 보류는 **60개**다.

P2 기준은 정부조직관리정보시스템의 2026 정부기구도·조직도(`https://www.org.go.kr/orgnzt/chart/viewEng.do`, `https://www.org.go.kr/cop/bbs/selectArticleList.do?bbsId=BBSMSTR_400000010000`)에서 확인한 중앙행정기관 49개 + 헌법기관 4개 + 독립국가기관 7개, 총 **60개**다. P3 기준은 잡알리오 2026 공공기관 지정현황과 재정경제부 2026년도 공공기관 지정 보도자료(`https://job.alio.go.kr/mobile2021/info/info02.do`, `https://www.moef.go.kr/nw/nes/detailNesDtaView.do?menuNo=4010100&searchBbsId1=MOSFBBS_000000000028&searchNttId1=MOSF_000000000076666`)의 공기업 30개 + 준정부기관 58개 + 기타공공기관 254개, 총 **342개**다. P4 기준은 클린아이 정책자료 2026.3.31 기준 첨부(`https://www.cleaneye.go.kr/user/referenceRoomList.do?num=313`)의 지방공기업 423개 + 지방자치단체 출자·출연기관 889개, 총 **1,312개**다. 공공데이터포털 `15114862`는 페이지 표기 1,284개와 실제 CSV 1,293개가 불일치하므로 P4 단일 기준으로 쓰지 않고 보조 근거로만 둔다.

| 범위 | 전체 | 공식 출처 검증 완료 | 검증 대기 | 법적 보류 | 출처 패턴 오류 |
|---|---:|---:|---:|---:|---:|
| 전국 목표(P1-P4) | 2200 | 139 | 1994 | 67 | 0 |
| P1 지방자치단체·의회 | 486 | 139 | 280 | 67 | 0 |
| P2 중앙행정기관·독립기관 | 60 | 0 | 60 | 0 | 0 |
| P3 지정 공공기관 | 342 | 0 | 342 | 0 | 0 |
| P4 지방공공기관 | 1312 | 0 | 1312 | 0 | 0 |
| 서울 + 경기 + 인천 | 138 | 131 | 0 | 7 | 0 |
| 서울 | 52 | 52 | 0 | 0 | 0 |
| 경기 + 인천 신규분 | 86 | 79 | 0 | 7 | 0 |
| 비수도권 | 348 | 8 | 280 | 60 | 0 |

## 이번 반영

### 실행/검증 오케스트레이션 보강

- `run-agencies` 배치 실행 결과를 리포트 입력으로 바로 쓸 수 있는 단일 JSON으로 정리했다.
- 기관별 `attempt_count`, `max_attempts`, `attempts[]`, 최종 `failure_reason`을 기록한다.
- retry 가능한 실패는 `--max-attempts 5` 기준으로 최대 5회까지 시도하고, 최종 사유를 `summary.failure_reasons`에 집계한다.
- 집계 사유는 `source_not_found`, `legal_hold`, `auth_js_download`, `parser_missing`, `llm_extraction_failure`, `kakao_resolution`, `db_constraint`, `storage_failure`를 기준으로 한다.
- 검증 리포트 생성기는 dry-run/staging load의 retry policy 게이트와 parsed/normalized/loaded/Kakao/storage 관련 집계값을 표시한다.
- `--fail-on-blockers` 검증 모드를 추가해 staging baseline, dry-run, staging load, public contract, production 승인 누락 시 nonzero 종료하게 했다.
- `daily-crawl.yml`의 기존 Seoul-only production write loop를 제거하고, 스케줄 실행을 `mode=staging-load`, `scope=nationwide`로 고정했다.
- 스케줄 경로는 production service `DATABASE_URL`을 주입하지 않고, `DATABASE_URL_READONLY` 기준선 + staging schema/seed/load/refresh + verification artifact만 생성한다.
- `daily-crawl.yml`에서 production load 모드를 제거했다. production 주입은 별도 승인 뒤 CLI에서 `--write-target production --confirm-production-write --allow-production-write --production-gate-report <검증리포트>`를 명시해야 한다.
- 운영 DB에서 복제한 staging branch용 forward migration `20260601030000_migrate_live_agency_kind_to_taxonomy.sql`을 추가했다. 기존 `kind` 기반 52개 agency를 `gov_tier`/`branch`/`jurisdiction_type`/`expansion_phase`로 승격하고, legacy `kind` 제약을 제거해 전국 seed가 가능하게 한다.

### 2026-06-01 기준선·서비스 주입 경로 확인

- production read-only baseline을 재생성했다. 현재 production은 agencies 52, sources 227, places 5,018, place_visits 11,327, 방문일 2024-01-02~2026-05-22다.
- production 기준 Kakao placeId 매칭은 3,555/5,018, 좌표 보유는 3,780/5,018, representative 저장은 0/11,327, 평균 extractor confidence는 0.82다.
- Neon staging branch `nationwide-staging-20260601`에서 read-only before baseline을 생성했고, forward migration + 전국 agency seed + view refresh 뒤 after baseline을 생성했다. staging은 agencies 52 → 2,200, sources 227, places 5,018, place_visits 11,327 상태다.
- exposure-policy migration 후 staging 공개 뷰는 places_public 4,785, place_visits_public 10,842로 줄었다. 대형 체인·비식당·무효 장소 제외 정책이 반영된 결과다.
- bounded 전국 dry-run(`since=2026-05-01`, `limit-pages=1`, `max-posts=1`, `max-attempts=5`, `agency_timeout_seconds=60`)을 실행해 artifact를 생성했다. 결과는 total 2,200, success 47, adapter_required 2,061, config_error 2, failed 90, posts_seen 142, posts_fetched 16, raw_parsed_rows 170, parsed_rows 52로 production 주입 게이트는 차단 상태다.
- 로컬/GitHub secret에는 아직 `DATABASE_URL_STAGING`/`STAGING_DATABASE_URL` 및 staging R2 값이 확인되지 않아 R2 원본 저장을 동반한 staging load는 차단된다.
- `/api/v1/places`와 웹 기본 데이터 로더의 서울 bbox 강제 기본값을 제거했다. bbox를 생략하면 전국 좌표 보유 식당 목록을 조회하고, bbox를 명시한 경우에만 공간 필터를 적용한다.
- Kakao SDK 실패 시 사용하는 fallback map도 현재 데이터 좌표 bounds를 사용하게 변경해 전국 마커가 서울 좌표계에 눌려 보이지 않도록 했다.

전국 2,200개 기관 taxonomy 스텁을 `agencies.py`에 추가했다. P2-P4 기관은 공식 기준 명부까지만 확인된 상태이므로 모두 `adapter_required`와 `pending`으로 둔다. 추가된 비수도권 P1 348개 기관은 모두 한국어 기관명·검색어를 가지며, 공식 출처 URL 검증 전까지 `homepage=None`, `source_url=None`, `adapter_required` 상태로 둔다. 단, 대전시청·대전시의회·전라남도청·서산시청·곡성군청·곡성군의회는 공식 업무추진비 목록·상세·다운로드 패턴과 공공누리 마크를 확인해 검증 등록했고, 광주시청·광주시의회·부산시청·부산시의회·대구시청·대구시의회·세종시청·세종시의회·강원특별자치도청·강원특별자치도의회·전북특별자치도청·전북특별자치도의회·전라남도의회·충청남도청·충청남도의회·충청북도청·충청북도의회·경상북도청·경상북도의회·경상남도청·경상남도의회·제주특별자치도청·제주특별자치도의회·울산시청·울산시의회와 대전 기초단체 9개, 충남 기초단체 8개, 울산 기초단체 2개, 전남 기초단체 10개, 전북 기초단체 2개, 경북 기초단체 2개, 경남 기초단체 2개는 공식 업무추진비 목록과 첨부 구조만 확인된 상태라 제1유형 또는 수집 접근성 확인 전까지 `legal_hold`로 둔다.

특별자치시·특별자치도 표기를 정확히 하기 위해 [ADR-013](../adr/ADR-013-special-self-governing-jurisdiction-types.md)을 추가했다. 세종은 `특별자치시`, 강원·전북·제주는 `특별자치도` 라벨로 노출한다.

공식 도메인에서 업무추진비 목록과 첨부/상세 구조를 확인한 28개 출처를 `agencies.py`에 추가했다.

| 기관 | 출처 URL | 어댑터 |
|---|---|---|
| 의정부시청 | `https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25` | `attachment_board` |
| 성남시청 | `https://www.seongnam.go.kr/city/1000199/30218/bbsList.do` | `attachment_board` |
| 평택시청 | `https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000` | `attachment_board` |
| 동두천시청 | `https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122` | `attachment_board` |
| 안산시청 | `https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471` | `attachment_board` |
| 부천시청 | `https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002` | `attachment_board` |
| 고양시청 | `https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84` | `attachment_board` |
| 오산시청 | `https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000` | `attachment_board` |
| 의왕시청 | `https://www.uiwang.go.kr/UWKOROPEN0210` | `attachment_board` |
| 안성시청 | `https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000` | `attachment_board` |
| 과천시청 | `https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000` | `attachment_board` |
| 광주시청 | `https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53` | `attachment_board` |
| 가평군청 | `https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454` | `attachment_board` |
| 경기도의회 | `https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list` | `council_attachment_board` |
| 평택시의회 | `https://www.ptcouncil.go.kr/coun/cost/reportList.do` | `council_attachment_board` |
| 동두천시의회 | `https://council.ddc.go.kr/kr/news/bbsCost.do` | `council_attachment_board` |
| 안성시의회 | `https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=` | `council_attachment_board` |
| 김포시의회 | `https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702` | `council_attachment_board` |
| 화성시의회 | `https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08` | `council_attachment_board` |
| 여주시의회 | `https://www.yeojucouncil.go.kr/kr/costBBS.do` | `council_attachment_board` |
| 중구의회 | `https://www.icjg.go.kr/council/cnac04b` | `council_attachment_board` |
| 동구청 | `https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84` | `attachment_board` |
| 미추홀구청 | `https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year=` | `attachment_board` |
| 연수구청 | `https://www.yeonsu.go.kr/main/administration/open_info/charge.asp` | `attachment_board` |
| 부평구청 | `https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost` | `attachment_board` |
| 남동구청 | `https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure` | `attachment_board` |
| 남동구의회 | `https://council.namdong.go.kr/kr/data/bbsBreakdown.do` | `council_attachment_board` |
| 옹진군청 | `https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1` | `attachment_board` |

비수도권에서 공식 도메인과 공공누리 마크를 직접 확인한 6개 출처를 추가했다.

| 기관 | 출처 URL | 어댑터 |
|---|---|---|
| 대전시청 | `https://www.daejeon.go.kr/drh/open/drhDataOpen/drhDataOpenBoardView.do?boardSeq=747&menuSeq=4804` | `attachment_board` |
| 대전시의회 | `https://council.daejeon.go.kr/svc/inf/OperatingExpenseList.do` | `council_attachment_board` |
| 전라남도청 | `https://www.jeonnam.go.kr/M1925005/boardList.do?menuId=jeonnam0302050100` | `attachment_board` |
| 서산시청 | `https://www.seosan.go.kr/www/selectBbsNttList.do?bbsNo=114&key=1278` | `attachment_board` |
| 곡성군청 | `https://www.gokseong.go.kr/kr/board/list.do?bbsId=BBS_000000000000540&menuNo=102006001000` | `attachment_board` |
| 곡성군의회 | `https://www.gokseong.go.kr/council/board/list.do?bbsId=BBS_000000000000380&menuNo=106005004000` | `council_attachment_board` |

## 데이터 품질·노출 정책

- 빈값·placeholder 장소명(`unknown`, `none`, `N/A`, `정보 없음`, `미상`, `해당없음`, `없음`, `장소 없음`, `불명`)은 식당 후보와 `places` 생성 대상에서 제외한다.
- 카카오 매칭 실패만으로 유효 상호를 삭제하지 않는다. 유효하지만 미매칭인 상호는 low-confidence/unmatched로 보존한다.
- 대형 전국 체인 방문은 원시/정규화 데이터에 보존하되 기본 지도·등급 공개에서는 제외한다.
- 기본 공개 조건은 `valid_place = true`, `is_restaurant_like = true`, `is_large_chain = false`다.
- 사용자 댓글·평점·후기 기능은 v1 범위에서 계속 금지한다.

## 남은 수도권 법적 보류

경기 6개:
경기도청, 안산시의회, 시흥시청, 이천시청, 화성시청, 여주시청.

인천 1개:
미추홀구의회.

보류 사유:

- 경기도청: 본청 업무추진비 목록 하단이 공공누리 3유형(출처명시+변경금지)으로 표시되어 법적 결정 전까지 보류한다.
- 안산시의회: 공식 업무추진비 목록과 XLSX 첨부 구조는 확인됐지만 목록 하단이 공공누리 3유형(출처표시+변경금지)으로 표시되어 보류한다.
- 시흥시청: 공식 업무추진비 목록과 XLSX 첨부 구조는 확인됐지만 상세 하단이 공공누리 4유형(출처표시+상업적 이용금지+변경금지)으로 표시되어 보류한다.
- 이천시청: 라이브 공식 업무추진비 공개 페이지(`https://www.icheon.go.kr/portal/contents.do?mid=0304080000` → `/portal/onnara/bpc/list.do?mid=0304080000`)와 XLSX 첨부 구조, 원문 HTML 표는 확인했다. 다만 개별 목록·상세에 공공누리 표시가 없고 저작권 정책에서 미표시 자료는 사전 협의가 필요하다고 안내하므로 보류한다.
- 화성시청: 공식 과거 업무추진비 목록(`https://www.hscity.go.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1062`)과 XLS/XLSX 첨부 구조는 확인됐지만, 최신 목록이 아니고 개별 페이지 공공누리 표시가 확인되지 않아 보류한다. 루트는 NetFunnel 게이트가 있어 수집 진입점도 추가 검증이 필요하다.
- 여주시청: 공식 역할별 업무추진비 목록(`bbsNo=32` 시장, `bbsNo=33` 부시장 등)과 PDF 첨부 구조는 확인됐지만 목록·상세 화면에서 공공누리 표기가 확인되지 않고 저작권 정책상 미표시 자료는 사전 협의가 필요하므로 보류한다.
- 미추홀구의회: 공식 의회 업무추진비 목록 후보는 확인했지만 첨부가 ZIP 중심이고 페이지 하단 공공누리 4유형(출처표시+상업적 이용금지+변경금지) 이미지가 표시되어 extractor/license 결정을 추가 검토해야 한다.

## 비수도권 법적 보류

부산 2개:
부산시청, 부산시의회.

대구 2개:
대구시청, 대구시의회.

대전 기초단체 9개:
동구청, 동구의회, 중구청, 중구의회, 서구청, 유성구청, 유성구의회, 대덕구청, 대덕구의회.

세종 2개:
세종시청, 세종시의회.

강원 2개:
강원특별자치도청, 강원특별자치도의회.

전북 2개:
전북특별자치도청, 전북특별자치도의회.

충남 2개:
충청남도청, 충청남도의회.

충남 기초단체 8개:
천안시청, 천안시의회, 공주시청, 공주시의회, 부여군청, 부여군의회, 논산시청, 논산시의회.

충북 2개:
충청북도청, 충청북도의회.

경북 2개:
경상북도청, 경상북도의회.

경남 4개:
경상남도청, 경상남도의회, 창원시청, 창원시의회.

제주 2개:
제주특별자치도청, 제주특별자치도의회.

울산 4개:
울산시청, 울산시의회, 남구청, 울주군의회.

전남 1개:
전라남도의회.

전남 기초단체 10개:
목포시청, 목포시의회, 나주시청, 광양시청, 구례군청, 구례군의회, 고흥군청, 고흥군의회, 여수시청, 순천시청.

전북 기초단체 2개:
전주시청, 군산시의회.

경북 기초단체 2개:
포항시청, 포항시의회.

보류 사유:

- 부산시청: 공식 업무추진비 목록(`https://www.busan.go.kr/ghopen12?curPage=1&schBizNo=46&schCommand=Expense`)은 확인했다. 다만 목록 페이지에서 공공누리 유형 표시가 확인되지 않았고, 현재 로컬 수집 환경은 부산광역시 보안 장비 차단 화면으로 전환되므로 제1유형과 수집 접근성 확인 전까지 수집하지 않는다.
- 부산시의회: 공식 업무추진비 목록(`https://council.busan.go.kr/council/infobbs0501`)과 XLSX 첨부 구조는 확인했다. 다만 업무추진비 목록·상세 페이지에서 공공누리 유형 표시가 확인되지 않고, 저작권 보호정책은 공공누리 표시가 부착된 저작물에 한해 자유이용 가능하다고 안내하므로 제1유형 확인 전까지 수집하지 않는다.
- 대구시청: 공식 업무추진비 목록(`https://www.daegu.go.kr/index.do?menu_id=00000084`)과 XLSX 첨부 구조는 확인했다. 다만 목록 페이지에서 공공누리 유형 표시가 확인되지 않고, 공공저작물 이용안내는 공공누리 표시가 부착되지 않은 자료는 담당자와 사전 협의가 필요하다고 안내하므로 제1유형 확인 전까지 수집하지 않는다.
- 대구시의회: 공식 업무추진비 목록(`https://council.daegu.go.kr/kr/bbs?bbs_id=business`)과 XLSX 첨부 구조는 확인했다. 다만 업무추진비 목록·상세 페이지에서 공공누리 유형 표시가 확인되지 않고, 저작권정책은 공공누리 표시가 부착된 공공저작물에 한해 자유이용 가능하다고 안내하므로 제1유형 확인 전까지 수집하지 않는다.
- 대전 동구청: 공식 5급 이상 업무추진비 목록(`https://www.donggu.go.kr/dg/kor/article/senior`)과 단체장 업무추진비 목록(`https://www.donggu.go.kr/dg/kor/article/secretBusiness`)을 확인했다. 다만 목록 화면에 공공누리 유형 표시가 직접 확인되지 않고, 공공누리 안내는 미부착 자료 이용 시 담당자 사전 협의를 요구하므로 보류한다.
- 대전 동구의회: 공식 업무추진비 현황 목록(`https://council.donggu.go.kr/kr/open/bbs?bbs_id=cost&filter=latest&flag=&keyword=&list_style=&page=1&reform=list&search_code=council`)과 XLSX 첨부 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 대전 중구청: 공식 부서별 업무추진비 목록(`https://www.djjunggu.go.kr/bbs/BBSMSTR_000000000105/list.do`)과 XLSX 직접 다운로드 구조를 확인했다. 다만 저작권정책은 공공누리가 부착되지 않은 자료의 사전 협의를 요구하므로 보류한다.
- 대전 중구의회: 공식 업무추진비 집행 현황 목록(`https://council.djjunggu.go.kr/kr/costBBS.do`)과 XLSX 직접 다운로드 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 대전 서구청: 공식 부서별 업무추진비 목록(`https://www.seogu.go.kr/bbs/BBSMSTR_000000000263/list.do`)과 XLSX 첨부 구조를 확인했다. 다만 공공저작물 개방 안내는 공공누리가 부착되지 않은 자료의 사전 협의를 요구하므로 보류한다.
- 대전 유성구청: 공식 단체장 업무추진비 목록(`https://www.yuseong.go.kr/bbs/BBSMSTR_000000000111/list.do`)과 부서별 업무추진비 목록(`https://www.yuseong.go.kr/bbs/BBSMSTR_000000000115/list.do`), PDF/XLSX 다운로드 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 대전 유성구의회: 공식 업무추진비 목록(`https://yuseonggucouncil.go.kr/bbs/board.php?bo_table=0603&page=1&sod=asc&sop=and&sst=wr_datetime`)과 XLS/XLSX 첨부 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 대전 대덕구청: 공식 단체장 업무추진비 목록(`https://www.daedeok.go.kr/dpt/dpt02/DPT02010401_cmmBoardList.do`)과 부서장 업무추진비 목록(`https://www.daedeok.go.kr/dpt/dpt02/DPT02010404_cmmBoardList.do`), PDF 첨부 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 대전 대덕구의회: 공식 업무추진비 현황 목록(`https://council.daedeok.go.kr/kr/costBBS.do`)과 XLSX 직접 다운로드 구조를 확인했다. 다만 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 세종시청: 공식 업무추진비 목록(`https://www.sejong.go.kr/bbs/R0091/list.do`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 세종시의회: 공식 업무추진비 목록(`https://council.sejong.go.kr/mnu/cap/businessExpenseList.do`)과 XLSX 직접 다운로드 구조는 확인했다. 다만 목록·상세 페이지에서 공공누리 유형 표시가 확인되지 않아 제1유형 또는 명확한 자유이용 표시 확인 전까지 수집하지 않는다.
- 전북특별자치도청: 공식 업무추진비공개 목록(`https://www.jeonbuk.go.kr/board/list.jeonbuk?boardId=BBS_0000029&listCel=1&listRow=10&menuCd=DOM_000000103005000000&paging=ok`)과 상세·HWP/HWPX/XLSX/PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 전북특별자치도의회: 공식 정보공개 목록(`https://jbstatecouncil.jeonbuk.kr/jbassem/board/39/4`)과 상세·XLSX/PDF/HWP 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 충청남도청: 공식 업무추진비 목록(`https://www.chungnam.go.kr/cnportal/bbs/B0000187/list.do?menuNo=500122`)과 상세·HWP/PDF 다운로드 구조를 확인했다. 다만 상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 충청남도의회: 공식 업무추진비 목록(`https://council.chungnam.go.kr/kr/costBBS.do?flag=all&list_style=&page=1&schwrd=`)과 상세·PDF/HWP/XLS/XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 천안시청: 현재 공식 업무추진비 공개 목록(`https://www.cheonan.go.kr/bbs/BBSMSTR_000000000050/list.do`)과 상세·XLSX/XLS/PDF/HWP/HWPX/ZIP 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다. 옛 `cop/bbs/BBSMSTR_000000000527/selectBoardList.do` URL은 404라 등록하지 않는다.
- 천안시의회: 공식 업무추진비 목록(`https://www.cheonancouncil.go.kr/svc/ctz/councilExpenseList.do`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 공주시청: 공식 업무추진비 공개 목록(`https://www.gongju.go.kr/bbs/BBSMSTR_000000000793/list.do`)과 상세·XLSX/XLS/HWP 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 공주시의회: 공식 업무추진비공개 목록(`https://council.gongju.go.kr/bbs/BBSMSTR_000000000882/list.do`)과 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 부여군청: 공식 업무추진비 공개 목록(`https://www.buyeo.go.kr/_prog/_board/?code=service_010211&site_dvs_cd=kr&menu_dvs_cd=010211`)과 상세·HWP 다운로드 링크 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 저작권정책 링크와 저작권 문구만 확인되어 보류한다.
- 부여군의회: 공식 업무추진비 집행내역 목록(`https://council.buyeo.go.kr/kr/open/bbsBusiness.do`)과 목록 ZIP 다운로드, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 저작권 문구만 확인되어 보류한다.
- 논산시청: 공식 업무추진비공개 목록(`https://www.nonsan.go.kr/kor/html/sub03/03080803.html?GotoPage=1&mode=L`)과 상세·PDF/HWP/엑셀 첨부 구조를 확인했다. 다만 목록 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 저작권정책 링크만 확인되어 보류한다.
- 논산시의회: 공식 업무추진비 목록(`https://www.nonsancl.go.kr/kr/activity/bbs?bbs_id=expense`)과 상세·XLSX 첨부 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 경상북도청: 공식 업무추진비 목록(`https://www.gb.go.kr/Main/page.do?mnu_uid=7406&BD_CODE=openhjinfo_deptmoney&cmd=1`)과 상세·XLSX/XLS/PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제3유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 경상북도의회: 공식 업무추진비 현황 목록(`https://council.gb.go.kr/kr/bbs?bbs_id=open`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 경상남도청: 공식 업무추진비 공개 목록(`https://www.gyeongnam.go.kr/board/list.gyeong?boardId=BBS_0000957&menuCd=DOM_000000138002012000&contentsSid=9918&cpath=`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 상세 화면이 해당 저작물의 자유이용을 불가한다고 표시해 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 경상남도의회: 공식 업무추진비 현황 목록(`https://council.gyeongnam.go.kr/kr/data/bbsExpense.do?flag=&keyword=&pageNum=1&reform=list`)과 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 제주특별자치도청: 감사위원회 공식 업무추진비 공개 목록(`https://audit.jeju.go.kr/news/notice/open.htm`)과 상세·XLSX/HWP 다운로드 구조를 확인했다. 다만 도청 전체 업무추진비 통합 출처로 확정할 수 없고, 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 제주특별자치도의회: 공식 업무추진비공개 목록(`https://www.council.jeju.kr/clicknews/openpromotion.do`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 전주시청: 공식 업무추진비 목록(`https://www.jeonju.go.kr/planweb/board/list.9is?boardUid=ff8080818bad9295018badaa04e2005f&contentUid=ff8080818990c349018b041a97883a1d&page=1`)과 상세·HWPX/PDF/XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 군산시의회: 공식 업무추진비공개 목록(`https://council.gunsan.go.kr/kr/open/bbsCost.do?flag=&keyword=&pageNum=1&reform=list`)과 상세·PDF/XLS/XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 포항시청: 공식 업무추진비 목록(`https://pohang.go.kr/portal/contents.do?mid=0301040300`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 포항시의회: 공식 업무추진비 현황 목록(`https://council.pohang.go.kr/content/data/operatingExpenseList.html`)과 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 창원시청: 공식 업무추진비 공개 목록(`https://www.changwon.go.kr/cwportal/10312/10620/10629.web?gcode=1036`)과 상세·PDF 다운로드 구조를 확인했다. 다만 상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 창원시의회: 공식 업무추진비 진행 현황 목록(`https://council.changwon.go.kr/svc/cns/OperatingExpenseList.do`)과 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 충청북도청: 공식 업무추진비 공개 목록(`https://www.chungbuk.go.kr/www/selectBbsNttList.do?bbsNo=2&key=211`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 충청북도의회: 공식 업무추진비 현황 목록(`https://council.chungbuk.kr/kr/memberCostBBS.do?flag=all&list_style=&page=1&publish=&schwrd=&th_sch=`)과 상세·XLS/XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 울산시청: 공식 부서장 업무추진비 목록(`https://www.ulsan.go.kr/u/rep/transfer/chief/list.ulsan?mId=001003002005000000`)과 HTML 상세 표 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 울산시의회: 공식 업무추진비 집행 현황 목록(`https://council.ulsan.kr/cop/bbs/selectBoardList.do?bbsId=bizExpStatus`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 울산 남구청: 공식 업무추진비 공개 목록(`https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=PrmtFee3`)과 구청장·부구청장·국장·부서장·동장·보건소 탭, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 울산 울주군의회: 공식 업무추진비 집행 현황 목록(`https://assembly.ulju.ulsan.kr/kr/bbs?bbs_id=business`)과 상세·XLSX 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 전라남도의회: 공식 업무추진비 목록(`https://www.jnassembly.go.kr/jnassem/board/412`)과 사전정보공표 업무추진비 목록(`https://www.jnassembly.go.kr/jnassem/board/51/1/category8`), 경로형 페이지네이션, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 목포시청: 공식 업무추진비 공개 목록(`https://www.mokpo.go.kr/www/open_data/open_operational_cost`)과 `page` 페이지네이션, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면의 공공누리 유형 표시가 비어 있어 제1유형 또는 명확한 자유이용 표시 확인 전까지 수집하지 않는다.
- 목포시의회: 공식 업무추진비 게시판(`https://council.mokpo.go.kr/kr/bbs?bbs_id=expenses`)과 `page` 페이지네이션, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 보류한다.
- 나주시청: 공식 예산살림 업무추진비 메뉴(`https://naju.go.kr/www/open_data/budget/expense`)와 단체장업무추진비사용내역 목록은 확인했다. 다만 현재 로컬 수집 환경에서는 본문이 0바이트로 내려오고 목록·상세 화면의 제1유형 표시가 확인되지 않아 제1유형과 수집 접근성 확인 전까지 수집하지 않는다.
- 광양시청: 공식 열린시장실 업무추진비 공개 화면(`https://gwangyang.go.kr/mayor/menu.es?mid=a20106014600`)에서 시장·부시장·국장·소장 역할별 분기 선택 목록과 HTML 표 구조를 확인했다. 다만 화면 하단 공공누리 표시가 출처표시+상업적이용금지+변경금지 조합으로 확인되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 구례군청: 공식 업무추진비 목록(`https://www.gurye.go.kr/board/list.do?bbsId=bbs_0000000000000055&menuNo=115002005000`)과 `pageIndex` 페이지네이션, 상세·XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 구례군의회: 공식 업무추진비 목록(`https://www.gurye.go.kr/board/list.do?bbsId=BBS_000000000000261&menuNo=162005000000`)과 `pageIndex` 페이지네이션, 상세·XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 고흥군청: 공식 업무추진비 공개 목록(`https://www.goheung.go.kr/boardList.do?boardId=BD_00107&pageId=www497`)과 `movePage` 페이지네이션, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 고흥군의회: 공식 업무추진비 목록(`https://council.goheung.go.kr/main/board/45/1/category7`)과 경로형 페이지네이션, 상세·PDF 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 여수시청: 공식 업무추진비 목록(`https://www.yeosu.go.kr/www/pubinfo/announce/operating_expense`)과 상세·PDF/ZIP 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.
- 순천시청: 공식 업무추진비 공개 목록(`https://sc.go.kr/kr/open/0001/0012?boardId=bbs_0000000000010158&mode=list&category=&pageIdx=`)과 상세·PDF/HWPX 다운로드 구조를 확인했다. 다만 목록·상세 화면이 공공누리 제4유형(출처표시-비상업적-변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않는다.

## 이번 dry-run

- 중구의회: 6개 첨부 참조 추출 성공. 예: `2026년 1분기 업무추진비 사용내역 공개`.
- 동구청: 9개 첨부 참조 추출 성공. 예: `2025년 4분기 화수2동 업무추진비 집행내역 공개`.
- 남동구의회: 10개 첨부 참조 추출 성공. 예: `2026년 4월 업무추진비 사용내역`.
- 옹진군청: 10개 첨부 참조 추출 성공. 예: `2026년 5월 업무추진비 집행내역(민원지적과)`.
- 오산시청: 10개 첨부 참조 추출 성공. 예: `2026년 4월 업무추진비 공개`.
- 의왕시청: 10개 첨부 참조 추출 성공. 예: `5월 시책추진업무추진비 사용내역(도시주택국, 도시정책과)`.
- 안성시청: 20개 첨부 참조 추출 성공. 예: `2026년 05월 문화관광과 업무추진비 공개내역`.
- 여주시의회: 공식 목록 HTML과 XLS 직접 다운로드 확인. `지출액` 헤더 alias 추가 후 샘플 XLS에서 3개 행 추출 성공. 파서 수정 전 `run-agency` dry-run은 3개 상세를 가져왔으나 0행이었고, 파서 수정 후 재시도는 공식 도메인 DNS 타임아웃으로 중단됐다.
- 성남시청: HWPX extractor와 성남식 `fileDownload(filePath, saveFileNm, oFileNm)` 링크 처리를 추가했다. 공식 HWPX 샘플 `업무추진비 정보공표(4월) 도시주택국.hwpx`에서 18개 행 추출 성공. `run-agency 성남시청 --dry-run --since 2026-04-01 --limit-pages 1 --max-posts 2`는 11개 첨부를 발견하고 2개 HWPX에서 21개 행을 파싱·정규화했다.
- 평택시청: 공식 업무추진비 게시판, `boardViewRenewal(...)` 상세 링크, `yhLib.file.download(atchFileId, fileSn)` 다운로드를 확인했다. 공식 XLS 샘플 `2026년 5월 업무추진비 집행내역(반도체AI과).xls` 다운로드와 공공누리 "출처표시" 조건을 확인했다. 현재 등록 파일 형식은 지원 가능한 `xls/xlsx/pdf`로 제한한다. 첫 글 PDF는 이 로컬 환경에 비전 추출용 LLM 키가 없어 건너뛰고, `run-agency 평택시청 --dry-run --since 2026-04-01 --limit-pages 1 --skip-posts 1 --max-posts 1`로 XLS 1개에서 3개 행을 파싱·정규화했다.
- 평택시의회: `fnActDetail(viewNo)` 상세 링크와 `fnActDownload(fileID)` XLS 다운로드 처리를 추가했다. 공식 XLS 샘플 `2026년 4월 의장단 업무추진비 집행내역.xls`에서 75개 행 추출 성공. `run-agency 평택시의회 --dry-run --since 2026-04-01 --limit-pages 1 --max-posts 2`는 2개 게시글에서 61개 행을 파싱·정규화했다.
- 이천시청: 라이브 공식 페이지에서 `data-req-action="/portal/onnara/bpc/view.do?mid=0304080000"` + `data-req-p-bid` 상세 링크와 `yhLib.file.download(atchFileId, fileSn)` XLSX 다운로드를 확인했다. 크롤러는 이 범용 inline-post 패턴을 해석할 수 있게 됐지만, 공공누리 미표시/사전협의 조건 때문에 등록은 보류한다.
- 미추홀구의회: 공식 목록은 확인했지만 첨부가 ZIP이고 페이지 하단 공공누리 4유형 이미지가 표시되어 extractor/license 결정을 추가 검토해야 하므로 등록 보류.
- 대전시청: 공식 목록에서 17개 게시글을 발견했고, `fileDownLoad(filePath, fileName)` XLSX 다운로드와 한국어 요일 포함 날짜(`2026. 5. 8.(금) 12:00`) 파싱을 보강했다. `run-agency 대전시청 --dry-run --since 2026-05-01 --limit-pages 1 --max-posts 1 --allow-deterministic-normalizer --allow-unmatched-places`는 XLSX 1개에서 8개 행을 파싱·정규화했다.
- 대전시의회: 공식 목록·상세·PDF 다운로드 구조는 확인했다. `run-agency 대전시의회 --dry-run --since 2026-05-01 --limit-pages 1 --max-posts 1 --allow-deterministic-normalizer --allow-unmatched-places`는 이 로컬 환경에 PDF 비전 추출용 LLM 키가 없어 `At least one LLM API key is required for scanned PDF vision extraction` 설정 오류로 중단됐다.
- 전라남도청: 공식 업무추진비 공개 목록과 `pageIndex` 페이지네이션, 상세 화면 HWP 다운로드 구조를 확인했다. 상세 하단에서 공공누리 제1유형 `출처표시` 조건을 직접 확인해 `attachment_board` 검증 출처로 등록했다. 운영 DB 적재나 dry-run 파싱은 실행하지 않았다.
- 곡성군청: 공식 군수·부군수·실과소원장/읍면장 업무추진비 목록과 `pageIndex` 페이지네이션, 상세 화면 PDF/XLSX 다운로드 구조를 확인했다. 화면 하단 공공누리 제1유형 `출처표시` 조건을 확인해 `attachment_board` 검증 출처로 등록했다.
- 곡성군의회: 공식 업무추진비 목록과 `pageIndex` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 화면 하단 공공누리 제1유형 `출처표시` 조건을 확인해 `council_attachment_board` 검증 출처로 등록했다.
- 광주광역시청: 공식 업무추진비 목록(`https://www.gwangju.go.kr/boardList.do?boardId=BD_0000000252&pageId=www101`)과 상세·XLS 다운로드 구조는 확인했다. 다만 상세 화면 공공누리 표시가 `자유이용 불가`로 안내되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 `legal_hold`로 둔다.
- 광주광역시의회: 공식 업무추진비 목록(`https://council.gwangju.go.kr/index.do?PID=168`)과 상세·PDF/XLS 다운로드 구조는 확인했다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 `legal_hold`로 둔다.
- 전라남도의회: 공식 의정활동 정보공개 업무추진비 목록(`https://www.jnassembly.go.kr/jnassem/board/412`)과 사전정보공표 업무추진비 목록, 경로형 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 세종시청: 공식 업무추진비 목록(`https://www.sejong.go.kr/bbs/R0091/list.do`)과 `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 상세 화면이 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 대전 기초단체: 동구청·동구의회·중구청·중구의회·서구청·유성구청·유성구의회·대덕구청·대덕구의회는 공식 업무추진비 목록과 첨부 구조를 확인했지만, 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다. 운영 DB 적재나 dry-run 파싱은 실행하지 않았다.
- 강원특별자치도청: 공식 도지사·부지사 업무추진비 목록과 실국과장·직속기관장 업무추진비 목록, `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 강원특별자치도의회: 공식 업무추진비 목록과 `page` 페이지네이션, 상세 화면 PDF/XLS 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 전북특별자치도청: 공식 업무추진비공개 목록과 `startPage` 페이지네이션, 상세 화면 HWP 다운로드 구조, 공공누리 제4유형 표시를 확인해 `legal_hold`로 등록했다.
- 전북특별자치도의회: 공식 정보공개 목록과 경로형 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 충청남도청: 공식 업무추진비 목록과 `pageIndex` 페이지네이션, 상세 화면 HWP 다운로드 구조, 공공누리 제4유형 표시를 확인해 `legal_hold`로 등록했다.
- 충청남도의회: 공식 업무추진비 목록과 `page` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 경상북도청: 공식 업무추진비 목록과 `Start` 페이지네이션, 상세 화면 XLSX/PDF 다운로드 구조, 공공누리 제3유형 표시를 확인해 `legal_hold`로 등록했다.
- 경상북도의회: 공식 업무추진비 현황 목록과 `page` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 전주시청: 공식 업무추진비 목록과 `page` 페이지네이션, 상세 화면 HWPX 다운로드 구조, 공공누리 제4유형 표시를 확인해 `legal_hold`로 등록했다.
- 군산시의회: 공식 업무추진비공개 목록과 `pageNum` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 포항시청: 공식 업무추진비 목록과 `page` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 포항시의회: 공식 업무추진비 현황 목록과 `page` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 충청북도청: 공식 업무추진비 공개 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 충청북도의회: 공식 업무추진비 현황 목록과 `page` 페이지네이션, 상세 화면 XLS/XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 울산시청: 공식 부서장 업무추진비 목록과 `curPage` 페이지네이션, 사용일자·결제내용·장소를 포함한 HTML 상세 표 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 울산시의회: 공식 업무추진비 집행 현황 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 울산 남구청: 공식 업무추진비 공개 목록과 구청장·부구청장·국장·부서장·동장·보건소 탭, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 울산 울주군의회: 공식 업무추진비 집행 현황 목록과 `page` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 목포시청: 공식 업무추진비 공개 목록과 `page` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 유형 표시가 비어 있어 `legal_hold`로 등록했다.
- 목포시의회: 공식 업무추진비 게시판과 `page` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 나주시청: 공식 예산살림 업무추진비 메뉴와 단체장업무추진비사용내역 목록은 확인했지만, 현재 로컬 수집 환경의 본문 0바이트 응답과 제1유형 미확인 때문에 `legal_hold`로 등록했다.
- 광양시청: 공식 열린시장실 업무추진비 공개 화면과 역할·분기 선택 목록, HTML 표 구조를 확인했다. 공공누리 표시가 출처표시+상업적이용금지+변경금지 조합으로 확인되어 `legal_hold`로 등록했다.
- 구례군청: 공식 업무추진비 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 구례군의회: 공식 업무추진비 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 고흥군청: 공식 사전정보공개 업무추진비 공개 목록과 `movePage` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 고흥군의회: 공식 열린의회 정보공개 업무추진비 목록과 경로형 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 여수시청: 공식 업무추진비 목록과 `page` 페이지네이션, 상세 화면 PDF/ZIP 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 순천시청: 공식 업무추진비 공개 목록과 `pageIdx` 페이지네이션, 상세 화면 PDF/HWPX 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 제주특별자치도청: 감사위원회 공식 업무추진비 공개 목록과 `page` 페이지네이션, 상세 화면 XLSX/HWP 다운로드 구조를 확인했다. 도청 전체 통합 출처로 확정할 수 없고 제1유형 표시도 확인되지 않아 `legal_hold`로 등록했다.
- 제주특별자치도의회: 공식 업무추진비공개 목록과 `page` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 경상남도청: 공식 업무추진비 공개 목록과 `pageNo` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 상세 화면이 자유이용 불가로 표시되어 `legal_hold`로 등록했다.
- 경상남도의회: 공식 업무추진비 현황 목록과 `pageNum` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 창원시청: 공식 업무추진비 공개 목록과 `cpage` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제4유형으로 표시되어 `legal_hold`로 등록했다.
- 창원시의회: 공식 업무추진비 진행 현황 목록과 `pageNo` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 천안시청: 현재 공식 업무추진비 공개 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX/XLS/PDF/HWP/HWPX/ZIP 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 천안시의회: 공식 업무추진비 목록과 `schPageNo` 페이지네이션, 상세 화면 XLSX 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 공주시청: 공식 업무추진비 공개 목록과 `pageIndex` 페이지네이션, 상세 화면 XLSX/XLS/HWP 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.
- 공주시의회: 공식 업무추진비공개 목록과 `pageIndex` 페이지네이션, 상세 화면 PDF 다운로드 구조를 확인했다. 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 `legal_hold`로 등록했다.

### 2026-06-01 P1 pending 비수도권 8개 기관 추가 출처 증거 조사

아래는 source registry 코드 반영 전 증거 기록이다. 조사 대상은 현재 등록부상 `pending`이고 `legal_hold`/`verified_in_code`가 아닌 비수도권 P1 기관으로 제한했다.

| 기관 | 공식 URL 후보 | 공개·라이선스 근거 | 첨부/본문 형식 | 어댑터 권장 | 권장 상태 |
|---|---|---|---|---|---|
| 보령시청 | `https://www.brcn.go.kr/cop/bbs/BBSMSTR_000000000386/selectBoardList.do?bbsId=BBSMSTR_000000000386&pageIndex=1` | 공식 업무추진비 목록에서 2025년 게시물이 확인되고, 같은 `BBSMSTR_000000000386` 상세가 공공누리 1유형 `출처표시` 조건으로 표시된다. | XLS/XLSX 중심, 일부 HWP/PDF 혼재 | `attachment_board`, `pageParam=pageIndex`, `followDetail=true`, `fileKinds=["xls","xlsx","hwp","pdf"]` | `verified_candidate` |
| 진도군청 | `https://www.jindo.go.kr/home/board/B0071.cs?m=52` | 공식 업무추진비 집행내역 목록과 상세 PDF 첨부가 확인되고, 상세 하단이 공공누리 `[출처표시]` 조건으로 표시된다. | PDF 중심 | `attachment_board`, `pageParam=pageIndex`, `followDetail=true`, `fileKinds=["pdf"]` | `verified_candidate` |
| 밀양시청 | `https://www.miryang.go.kr/twn/bbs/selectBoardDetail.do?bbsId=BBSMSTR_000000085910&mnNo=3040000&nttId=174279&owd=sammun&pageIndex=1` | 공식 밀양시 읍면동 공개자료실 상세에서 XLSX 첨부와 공공누리 `출처표시` 조건이 확인된다. 다만 조사 URL은 삼문동 세부 보드라 시청 전체 업무추진비 통합 list URL과 부서별 보드 범위 매핑이 추가로 필요하다. | XLSX | 다중 `attachment_board` 후보, `pageIndex`, `followDetail=true` | `pending` |
| 진주시청 | `https://www.jinju.go.kr/05638.web` / `https://www.jinju.go.kr/05637.web` | 과장급·국소장급 업무추진비 상세와 XLSX 첨부가 확인된다. 일부 상세는 공공누리 1유형이지만 같은 업무추진비 보드 다수 상세가 제4유형으로 표시되어 게시물별 라이선스 필터 없이는 수집 불가다. | XLSX | `attachment_board`, `gcode`별 extra list, `followDetail=true` | `legal_hold` |
| 인제군청 | `https://inje.gangwon.kr/portal/adm/public/operatingexpense?pageIndex=1` | 공식 업무추진비 공개 목록과 XLS/XLSX/PDF 첨부가 확인된다. 상세 화면은 공공누리 `출처표시+상업적 이용금지+변형 등 2차적 저작물 작성 금지` 조건으로 표시된다. | XLSX/XLS/PDF | `attachment_board`, `pageParam=pageIndex`, `followDetail=true` | `legal_hold` |
| 금정구청 | `https://www.geumjeong.go.kr/board/list.geumj?boardId=BBS_0000331&menuCd=DOM_000000124001011000&orderBy=REGISTER_DATE+DESC` | 공식 업무추진비 목록과 HWPX/XLSX 첨부 구조가 확인된다. 상세 하단이 공공누리 제4유형으로 표시된다. | HWPX 중심, 일부 XLSX | `attachment_board`, `pageParam=startPage`, `followDetail=true` | `legal_hold` |
| 정선군청 | `https://www.jeongseon.go.kr/portal/admininfo/openinfo/expense?pageIndex=1` | 공식 업무추진비 공개 목록과 XLSX 첨부 상세가 확인된다. 조사 시점에는 목록·상세에서 공공누리 제1유형 또는 동등 자유이용 표시를 확인하지 못했다. | XLSX | `attachment_board`, `pageParam=pageIndex`, `followDetail=true` | `pending` |
| 아산시청 | `https://asan.go.kr/main/cms/?no=335&tb_nm=dep_expense` | 공식 업무추진비공개 화면에서 공개대상(시장·부시장·국소장·실과장·읍면동장)과 공개내용(기관운영·시책추진), HWPX 첨부가 확인된다. 조사 시점에는 공공누리 제1유형 또는 동등 자유이용 표시를 확인하지 못했다. | HWPX | `attachment_board`, `pageParam=PageNo`, `followDetail=true`, `fileKinds=["hwpx"]` | `pending` |

## 검증 명령

최근 통과한 명령:

```bash
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline public-officer-pipeline source-registry --scope nationwide --format json
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline ruff check src tests
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest services/pipeline/tests/test_cli.py services/pipeline/tests/test_gncouncil_crawler.py services/pipeline/tests/test_agencies.py services/pipeline/tests/test_source_registry.py -q
uv --cache-dir /private/tmp/uv-cache run --project services/pipeline pytest -q
npm run check:public-contracts
npm run test:api
npm run test:web
npm run build
git diff --check
```

현재 확인된 통과 상태:

- 파이프라인 표적 테스트: `119 passed` (`test_cli.py`, `test_gncouncil_crawler.py`, `test_agencies.py`, `test_source_registry.py`)
- 파이프라인 전체 테스트: `360 passed`
- API 테스트: `74 passed`
- 웹 테스트: `29 passed`
- ruff 전체 검사: 통과
- workflow YAML parse: 통과
- 공개 route contract 검증: 통과
- 웹 빌드: 통과(Vite 500kB chunk 경고만 표시)

2026-06-01 추가 진행:

- Neon `gongmuwon-map` project에 staging branch `nationwide-staging-20260601` (`br-dawn-paper-aonnud0v`)를 생성했고 `ready` 상태를 확인했다.
- staging 연결 문자열은 secret이므로 문서나 리포트에 기록하지 않는다. 다음 단계는 `DATABASE_URL_STAGING`을 안전하게 설정한 뒤 baseline 리포트를 실행하는 것이다.
- source registry summary 기준 전국 2,200개 기관 중 139개가 코드 검증 완료, 1,994개 pending, 67개 legal_hold, invalid source pattern 0개다.
- LLM provider fallback과 shape drift를 보강했다. Gemini 2.5에는 unsupported `thinkingLevel`을 보내지 않고, OpenAI Chat Completions에는 unsupported `reasoning`을 보내지 않으며, `confidence: "high"` 같은 정성 confidence와 string `place_raw`를 정규화한다.
- `run-agencies` summary가 `raw_parsed_rows`를 집계하고, strict quality gate 실패 시에도 부분 stats와 구체 gate 메시지를 보존한다.
- 성남시청 표적 dry-run(`--quality-mode warn`, `--row-since 2026-04-01`)은 2개 게시글에서 21개 raw/filtered row, 21개 normalized visit, 20개 place, 18개 Kakao match를 확인했다.
- 성남시청 strict dry-run(`--quality-mode fail`)은 1개 게시글에서 18개 row와 17개 place까지 처리한 뒤 `missing_coordinates: 2/17 > 0.05`로 차단됐다. 이는 문서화된 좌표 누락 <5% gate를 완화하지 않고 유지한 결과다.
- 대전시청 strict dry-run(`--quality-mode fail`)은 1개 XLSX 게시글에서 10개 row, 10개 normalized visit, 10개 place, 10개 Kakao match로 통과했다.
- 검증 리포트 생성기가 GitHub run metadata, source file/storage_path 집계, per-agency retry evidence, 반복 가능한 `--targeted-run=label:path` 표적 dry-run 섹션을 렌더링하도록 보강됐다. 향후 scheduled regeneration이 수동 진단 섹션을 지우지 않는다.
- HTTP adaptive fallback은 `httpx.DecodingError` 발생 시 `Accept-Encoding: identity`와 non-`--compressed` curl 경로로 재시도한다. 이전 `incorrect header check`류 정부 사이트 다운로드 실패를 줄이기 위한 변경이며, oversized download guard는 그대로 유지한다.
- Anthropic PDF vision 요청은 Messages API의 `thinking` payload를 사용하고 thinking 사용 시 `temperature`를 빼도록 보강됐다. Gemini/OpenAI fallback은 기존 400 fallback-capable handling을 유지한다.
- PDF/text row parser는 `34:21`처럼 금액·OCR 조각이 시간처럼 잡힌 invalid time token을 행 스킵으로 처리해 기관 전체 retry를 낭비하지 않는다. 구로구청 표적 dry-run은 이 수정 후 1개 게시글에서 13개 row/visit, 12개 place, 11개 Kakao match까지 처리한 뒤 strict coordinate gate(`1/12 > 0.05`)에서 차단됐다.
- 보령시청·진도군청은 공식 제1유형 출처 확인 후 코드 검증 완료로 승격했다. 보령은 XLS/XLSX/PDF만 허용해 HWP extractor 미지원 경로를 피하고, 진도는 detail page가 bot user-agent에 500을 반환하는 현상을 source-specific `userAgent`로 격리했다.
- 보령/진도 표적 dry-run은 현 window에서 2/2 success, 9 posts_seen, 2 posts_fetched, 26 raw rows를 확인했다. row window를 2026-01-01로 넓힌 보조 run은 진도 22 parsed/normalized visits, 19 places를 확인했고, 보령 최신 1개 파일은 row cutoff 내 parsed row가 없었다.
- 전국 dry-run은 `--agency-timeout-seconds 60 --concurrency 12 --max-attempts 5`로 완료됐고, 2,200개 기관 중 47 success, 2,061 adapter_required/legal_hold, 90 timeout, 1 Kakao quality gate, 1 LLM timeout으로 집계됐다. 수집 활동은 142 posts_seen, 16 posts_fetched, 170 raw rows, 52 normalized visits, 47 Kakao matches다. 이 결과는 staging load 차단 사유로 검증 리포트에 남겼다.
- `run-agencies`에 기관 단위 wall-clock guard `--agency-timeout-seconds`를 추가했고 GitHub Actions scheduled crawl 기본값을 180초로 설정했다. 한 기관의 장시간 미응답이 전체 artifact 생성을 무기한 막지 않도록 하기 위한 운영 보강이다.
- timeout artifact의 retry evidence는 실제 timeout이 발생한 attempt를 기록하도록 보정했다. `timeout`은 더 이상 `auth_js_download`로 섞이지 않고 별도 `failure_reason`으로 집계된다.
- timeout 진단 필드는 `current_stage`, `last_stage`, `timeout_stage`, `stage_elapsed_ms`를 남긴다. 강북구청 5초 제한 표적 dry-run은 `timeout_stage=extract_rows`를 기록했고, 동일 조건에서 180초 제한으로 재실행한 표적 dry-run은 1개 게시글에서 10 raw/parsed/normalized visits, 7 places, 7 Kakao matches로 성공했다. 따라서 기존 60초 전국 dry-run의 timeout 90건은 현 코드와 180초 기본값으로 재시도해야 한다.
- staging write preflight는 `DATABASE_URL_STAGING` 또는 `STAGING_DATABASE_URL`을 먼저 요구하고, 원문 artifact를 생성하는 crawl/load 계열 명령에만 R2 provenance env를 추가 요구한다. schema/seed/refresh는 R2 env 없이 staging DB URL만으로 실행 가능하다. staging crawl/load는 runtime `R2_*`뿐 아니라 `R2_STAGING_*` env set도 직접 허용한다.
- scheduled staging load는 dry-run 전체가 green일 때만 진행하는 방식이 아니라, dry-run artifact에 성공 기관이 1개 이상 있으면 성공 기관 적재를 시도하고 실패 기관은 리포트에 보존한다. partial staging load 후 loaded visit이 있으면 public view refresh도 실행한다.
- production write gate는 서울/단일기관/스키마 명령을 포함한 모든 production write 경로에서 `--confirm-production-write`, `--allow-production-write`, `--production-gate-report`를 요구한다.
- staging load를 바로 실행할 수 있는 row-producing 후보는 서울시의회, 강남구청, 강화군청, 옹진군청이다. 다만 현재 로컬 환경과 GitHub Actions secret 목록에는 `DATABASE_URL_STAGING`/`STAGING_DATABASE_URL` 및 `R2_STAGING_*`가 없어 R2 provenance를 포함한 staging load는 아직 실행하지 않았다.

## 다음 순서

전국 업무추진비 원문 데이터를 기존 DB와 같은 구조로 재수집·적재하는 실행계획은 [전국 업무추진비 데이터셋 수집 실행 계획](nationwide_collection_execution_plan.md)을 기준으로 진행한다. 현재 기준선과 production 주입 판정은 [전국 수집 검증 리포트](nationwide_verification_report.md)에 기록한다.

1. 수도권은 현재 0 pending / 7 legal_hold 상태다. legal_hold는 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 적재하지 않는다.
2. 비수도권은 현재 8 verified / 280 pending / 60 legal_hold 상태다. 지역별로 공식 URL 검증을 진행하되, 광주·부산·대구·세종·강원·전북·전남·충남·충북·경북·경남·제주·울산·대전 기초·충남 기초·전남 기초 보류 기관은 제1유형 또는 수집 접근성 확인 전까지 적재하지 않는다.
3. P2 60개, P3 342개, P4 1,312개는 공식 기준 명부만 확정된 pending 상태다. 기관별 업무추진비 원문 URL·공공누리/라이선스·첨부 패턴 검증 전까지 크롤·적재하지 않는다.
4. 새 기관마다 공식 URL, 공공누리/라이선스, 첨부 패턴, crawler dry-run, parser 샘플 검증, 공공누리/출처 표시 업데이트를 완료한 뒤에만 staging 적재를 검토한다.
5. staging load 전 `DATABASE_URL_STAGING` 또는 `STAGING_DATABASE_URL`, `R2_STAGING_ACCOUNT_ID`, `R2_STAGING_ACCESS_KEY_ID`, `R2_STAGING_SECRET_ACCESS_KEY`, `R2_STAGING_BUCKET`을 GitHub Secrets 또는 로컬 shell에 주입한다. CLI 실행 시에는 staging R2 secret을 `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`으로 매핑한다. secret 값은 문서와 리포트에 남기지 않는다.
