from public_officer_pipeline.agencies import (
    CAPITAL_AREA_AGENCIES,
    CENTRAL_STATE_AGENCIES,
    GYEONGGI_AGENCIES,
    INCHEON_AGENCIES,
    LOCAL_PUBLIC_INSTITUTION_AGENCIES,
    NATIONWIDE_AGENCIES,
    NON_CAPITAL_AGENCIES,
    PUBLIC_INSTITUTION_AGENCIES,
    SEOUL_AGENCIES,
)
from public_officer_pipeline.models import Agency
from public_officer_pipeline.source_registry import source_registry_entries, source_registry_summary


def test_source_registry_tracks_verified_seoul_and_legal_hold_new_regions() -> None:
    entries = source_registry_entries(CAPITAL_AREA_AGENCIES)
    summary = source_registry_summary(entries)

    assert summary.total == 138
    assert summary.verified_in_code == 131
    assert summary.pending == 0
    assert summary.legal_hold == 7
    assert summary.invalid_source_pattern == 0

    seoul_entries = [entry for entry in entries if entry.parent_region == "서울특별시"]
    assert len(seoul_entries) == len(SEOUL_AGENCIES)
    assert all(entry.verification_status == "verified_in_code" for entry in seoul_entries)
    assert all(entry.source_url for entry in seoul_entries)

    new_region_entries = [
        entry for entry in entries if entry.parent_region in {"경기도", "인천광역시"}
    ]
    assert len(new_region_entries) == len(GYEONGGI_AGENCIES) + len(INCHEON_AGENCIES)
    assert sum(1 for entry in new_region_entries if entry.verification_status == "verified_in_code") == 79
    assert sum(1 for entry in new_region_entries if entry.verification_status == "pending") == 0
    assert sum(1 for entry in new_region_entries if entry.verification_status == "legal_hold") == 7
    verified_by_values = [
        entry.verified_by
        for entry in new_region_entries
        if entry.verification_status == "verified_in_code" and entry.verified_by
    ]
    assert verified_by_values
    assert all(any("가" <= char <= "힣" for char in value) for value in verified_by_values)

    incheon_council = next(entry for entry in entries if entry.short_name == "인천시의회")
    assert incheon_council.verification_status == "verified_in_code"
    assert incheon_council.verification_status_label == "코드 검증 완료"
    assert incheon_council.gov_tier_label == "광역자치단체"
    assert incheon_council.branch_label == "의회"
    assert incheon_council.jurisdiction_type_label == "광역시"
    assert incheon_council.source_url == "https://www.icouncil.go.kr/main/participate/expense_office.jsp"
    assert incheon_council.verified_at == "2026-06-01"

    suwon_council = next(entry for entry in entries if entry.short_name == "수원시의회")
    assert suwon_council.verification_status == "verified_in_code"
    assert suwon_council.source_url == (
        "https://council.suwon.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert suwon_council.verified_at == "2026-06-01"

    gyeonggi_council = next(entry for entry in entries if entry.short_name == "경기도의회")
    assert gyeonggi_council.verification_status == "verified_in_code"
    assert gyeonggi_council.source_url == (
        "https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list"
    )
    assert gyeonggi_council.verified_at == "2026-06-01"

    verified_office_urls = {
        entry.short_name: entry.source_url
        for entry in new_region_entries
        if entry.verification_status == "verified_in_code"
    }
    assert verified_office_urls["수원시청"] == (
        "https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179"
    )
    assert verified_office_urls["성남시청"] == (
        "https://www.seongnam.go.kr/city/1000199/30218/bbsList.do"
    )
    assert verified_office_urls["평택시청"] == (
        "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000"
    )
    assert verified_office_urls["안양시청"] == (
        "https://www.anyang.go.kr/main/selectBbsNttList.do?bbsNo=43&key=218"
    )
    assert verified_office_urls["의정부시청"] == (
        "https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25"
    )
    assert verified_office_urls["동두천시청"] == (
        "https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122"
    )
    assert verified_office_urls["안산시청"] == (
        "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471"
    )
    assert verified_office_urls["부천시청"] == (
        "https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002"
    )
    assert verified_office_urls["고양시청"] == (
        "https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84"
    )
    assert verified_office_urls["김포시청"] == (
        "https://www.gimpo.go.kr/portal/selectBbsNttList.do?bbsNo=199&key=1110"
    )
    assert verified_office_urls["하남시청"] == (
        "https://www.hanam.go.kr/www/selectBbsNttList.do?bbsNo=15&key=51"
    )
    assert verified_office_urls["광명시청"] == (
        "https://www.gm.go.kr/pt/user/bbs/BD_selectBbsList.do?q_bbsCode=2472"
    )
    assert verified_office_urls["구리시청"] == (
        "https://www.guri.go.kr/www/selectBbsNttList.do?bbsNo=14&key=331"
    )
    assert verified_office_urls["남양주시청"] == (
        "https://www.nyj.go.kr/www/selectBbsNttList.do?key=2432&bbsNo=43"
    )
    assert verified_office_urls["오산시청"] == (
        "https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000"
    )
    assert verified_office_urls["군포시청"] == (
        "https://www.gunpo.go.kr/www/selectBbsNttList.do?bbsNo=715&key=4276"
    )
    assert verified_office_urls["의왕시청"] == "https://www.uiwang.go.kr/UWKOROPEN0210"
    assert verified_office_urls["용인시청"] == (
        "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6"
    )
    assert verified_office_urls["파주시청"] == (
        "https://www.paju.go.kr/user/policy_02/board/BD_board.list.do?bbsCd=1018"
    )
    assert verified_office_urls["양주시청"] == (
        "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=30&key=234"
    )
    assert verified_office_urls["포천시청"] == (
        "https://www.pocheon.go.kr/www/selectBbsNttList.do?bbsNo=214&key=3687"
    )
    assert verified_office_urls["연천군청"] == (
        "https://www.yeoncheon.go.kr/www/selectBbsNttList.do?bbsNo=152&key=3352"
    )
    assert verified_office_urls["양평군청"] == (
        "https://www.yp21.go.kr/www/selectBbsNttList.do?bbsNo=43&key=1597"
    )
    assert verified_office_urls["안성시청"] == (
        "https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000"
    )
    assert verified_office_urls["과천시청"] == (
        "https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000"
    )
    assert verified_office_urls["광주시청"] == (
        "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53"
    )
    assert verified_office_urls["가평군청"] == (
        "https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454"
    )
    assert verified_office_urls["성남시의회"] == "https://www.sncouncil.go.kr/kr/news/bbsCost.do"
    assert verified_office_urls["평택시의회"] == "https://www.ptcouncil.go.kr/coun/cost/reportList.do"
    assert verified_office_urls["의정부시의회"] == (
        "https://www.ujbcl.go.kr/svc/bbs/BusinessList.do?bbsMnuCd=MNU002300000650400000666"
    )
    assert verified_office_urls["동두천시의회"] == "https://council.ddc.go.kr/kr/news/bbsCost.do"
    assert verified_office_urls["광명시의회"] == "https://council.gm.go.kr/kr/costBBS.do"
    assert verified_office_urls["고양시의회"] == "https://www.goyangcouncil.go.kr/kr/costBBS.do"
    assert verified_office_urls["구리시의회"] == "https://www.gcc.or.kr/board/news/list.do?tbname=cost"
    assert verified_office_urls["남양주시의회"] == (
        "https://nyjc.go.kr/content/dataroom/propelclosed.html"
    )
    assert verified_office_urls["용인시의회"] == "https://council.yongin.go.kr/kr/costBBS.do"
    assert verified_office_urls["부천시의회"] == "https://council.bucheon.go.kr/kr/intro/bbsInfo.do"
    assert verified_office_urls["안양시의회"] == "https://www.aycouncil.go.kr/kr/costBBSlist.do?page=1"
    assert verified_office_urls["군포시의회"] == (
        "https://www.gunpocouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_office_urls["의왕시의회"] == (
        "https://council.uiwang.go.kr/kr/news/bbsCost.do?flag=&keyword="
    )
    assert verified_office_urls["과천시의회"] == "https://www.gccouncil.go.kr/kr/costBBSlist.do?page=1"
    assert verified_office_urls["오산시의회"] == "https://www.osancouncil.go.kr/kr/news/bbs?bbs_id=work"
    assert verified_office_urls["시흥시의회"] == (
        "https://www.siheungcouncil.go.kr/content/activity/business.html"
    )
    assert verified_office_urls["하남시의회"] == (
        "https://council.hanam.go.kr/content/community/business.html"
    )
    assert verified_office_urls["파주시의회"] == (
        "https://www.pajucouncil.go.kr/content/data/operatingExpense.html"
    )
    assert verified_office_urls["광주시의회"] == (
        "https://www.gjcouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_office_urls["포천시의회"] == (
        "https://council.pocheon.go.kr/kr/news/bbsBusiness.do"
    )
    assert verified_office_urls["여주시의회"] == "https://www.yeojucouncil.go.kr/kr/costBBS.do"
    assert verified_office_urls["양주시의회"] == (
        "https://yjcc.yangju.go.kr/yjcc/selectBbsNttList.do?bbsNo=302&key=2559"
    )
    assert verified_office_urls["이천시의회"] == (
        "https://council.icheon.go.kr/content/information/businessOperatingExpense.html"
    )
    assert verified_office_urls["안성시의회"] == (
        "https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_office_urls["김포시의회"] == (
        "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702"
    )
    assert verified_office_urls["화성시의회"] == (
        "https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08"
    )
    assert verified_office_urls["가평군의회"] == "https://www.gpassem.go.kr/kr/operations2BBS.do"
    assert verified_office_urls["연천군의회"] == (
        "https://www.yca21.go.kr/board/news/list.do?tbname=cost"
    )
    assert verified_office_urls["양평군의회"] == (
        "https://www.ypcouncil.go.kr/main/selectBbsNttList.do?bbsNo=9&key=43"
    )
    assert verified_office_urls["인천시청"] == "https://www.incheon.go.kr/open/OPEN010305"
    assert verified_office_urls["중구청"] == "https://www.icjg.go.kr/krop0307c"
    assert verified_office_urls["중구의회"] == "https://www.icjg.go.kr/council/cnac04b"
    assert verified_office_urls["동구청"] == (
        "https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84"
    )
    assert verified_office_urls["계양구청"] == (
        "https://www.gyeyang.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=board_14&cate1=94"
    )
    assert verified_office_urls["서구청"] == (
        "https://www.seo.incheon.kr/open_content/main/bbs/bbsMsgList.do?bcd=clean_cost"
    )
    assert verified_office_urls["미추홀구청"] == (
        "https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year="
    )
    assert verified_office_urls["연수구청"] == (
        "https://www.yeonsu.go.kr/main/administration/open_info/charge.asp"
    )
    assert verified_office_urls["부평구청"] == "https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost"
    assert verified_office_urls["남동구청"] == (
        "https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure"
    )
    assert verified_office_urls["남동구의회"] == (
        "https://council.namdong.go.kr/kr/data/bbsBreakdown.do"
    )
    assert verified_office_urls["강화군청"] == (
        "https://www.ganghwa.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=operation"
    )
    assert verified_office_urls["옹진군청"] == (
        "https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1"
    )
    assert verified_office_urls["서구의회"] == (
        "https://www.seo.incheon.kr/open_content/council/activity/open.jsp"
    )
    assert verified_office_urls["동구의회"] == "https://council.icdonggu.go.kr/kr/costBBS.do"
    assert verified_office_urls["연수구의회"] == "https://council.yeonsu.go.kr/kr/businessBBS.do"
    assert verified_office_urls["부평구의회"] == (
        "https://council.icbp.go.kr/kr/data/bbs?bbs_id=expense"
    )
    assert verified_office_urls["계양구의회"] == "https://council.gyeyang.go.kr/kr/costBBS.do"
    assert verified_office_urls["강화군의회"] == "https://council.ganghwa.go.kr/kr/workBBS.do"
    assert verified_office_urls["옹진군의회"] == "https://council.ongjin.go.kr/kr/costBBS.do"

    legal_hold_new_region_entries = [
        entry for entry in new_region_entries if entry.verification_status == "legal_hold"
    ]
    assert all(entry.source_url is None for entry in legal_hold_new_region_entries)
    assert all(entry.homepage is None for entry in legal_hold_new_region_entries)
    assert all(
        entry.verification_status_label == "법적 검토 보류"
        for entry in legal_hold_new_region_entries
    )
    legal_hold_notes = {entry.short_name: entry.evidence_note for entry in legal_hold_new_region_entries}
    assert "공공누리 제3유형" in legal_hold_notes["경기도청"]
    assert "변경금지 제한" in legal_hold_notes["경기도청"]
    assert "공공누리 제3유형" in legal_hold_notes["안산시의회"]
    assert "변경금지 제한" in legal_hold_notes["안산시의회"]
    assert "공공누리 제4유형" in legal_hold_notes["시흥시청"]
    assert "상업적 이용금지 및 변경금지 제한" in legal_hold_notes["시흥시청"]
    assert "공공누리 미부착 자료" in legal_hold_notes["이천시청"]
    assert "사전 협의" in legal_hold_notes["이천시청"]
    assert "무단사용" in legal_hold_notes["화성시청"]
    assert "사전 협의" in legal_hold_notes["화성시청"]
    assert "All Rights Reserved" in legal_hold_notes["여주시청"]
    assert "사전 협의" in legal_hold_notes["여주시청"]
    assert "공공누리 제4유형" in legal_hold_notes["미추홀구의회"]
    assert "ZIP 중심" in legal_hold_notes["미추홀구의회"]


def test_source_registry_tracks_nationwide_pending_scope_with_korean_labels() -> None:
    entries = source_registry_entries(NATIONWIDE_AGENCIES)
    summary = source_registry_summary(entries)

    assert summary.total == 2202
    assert summary.verified_in_code == 207
    assert summary.pending == 46
    assert summary.legal_hold == 162
    assert summary.source_not_found == 124
    assert summary.no_recent_data == 295
    assert summary.pdf_vision_hold == 17
    assert summary.adapter_hold == 1351
    assert summary.invalid_source_pattern == 0
    assert summary.priority_group_counts["p1"].total == 488
    assert summary.priority_group_counts["p1"].verified_in_code == 165
    assert summary.priority_group_counts["p1"].pending == 46
    assert summary.priority_group_counts["p1"].legal_hold == 162
    assert summary.priority_group_counts["p1"].source_not_found == 92
    assert summary.priority_group_counts["p1"].no_recent_data == 1
    assert summary.priority_group_counts["p1"].pdf_vision_hold == 9
    assert summary.priority_group_counts["p1"].adapter_hold == 13
    assert summary.priority_group_counts["p2"].total == 60
    assert summary.priority_group_counts["p2"].pending == 0
    assert summary.priority_group_counts["p2"].source_not_found == 32
    assert summary.priority_group_counts["p2"].adapter_hold == 28
    assert summary.priority_group_counts["p3"].total == 342
    assert summary.priority_group_counts["p3"].verified_in_code == 6
    assert summary.priority_group_counts["p3"].pending == 0
    assert summary.priority_group_counts["p3"].no_recent_data == 280
    assert summary.priority_group_counts["p3"].pdf_vision_hold == 8
    assert summary.priority_group_counts["p3"].adapter_hold == 48
    assert summary.priority_group_counts["p4"].total == 1312
    assert summary.priority_group_counts["p4"].verified_in_code == 36
    assert summary.priority_group_counts["p4"].pending == 0
    assert summary.priority_group_counts["p4"].no_recent_data == 14
    assert summary.priority_group_counts["p4"].adapter_hold == 1262

    non_capital_entries = [
        entry
        for entry in entries
        if entry.priority_group == "p1"
        and entry.parent_region not in {"서울특별시", "경기도", "인천광역시"}
    ]
    assert len(non_capital_entries) == len(NON_CAPITAL_AGENCIES)
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "verified_in_code") == 34
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "pending") == 46
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "legal_hold") == 155
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "no_recent_data") == 1
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "pdf_vision_hold") == 9
    assert (
        sum(1 for entry in non_capital_entries if entry.verification_status == "source_not_found")
        == 92
    )
    assert sum(1 for entry in non_capital_entries if entry.verification_status == "adapter_hold") == 13
    assert all(
        entry.source_url is None
        for entry in non_capital_entries
        if entry.verification_status == "pending"
    )
    assert all(
        entry.homepage is None
        for entry in non_capital_entries
        if entry.verification_status in {"pending", "source_not_found"}
    )
    assert all(any("가" <= char <= "힣" for char in entry.name) for entry in non_capital_entries)

    busan_council = next(entry for entry in non_capital_entries if entry.short_name == "부산시의회")
    assert busan_council.verification_status == "legal_hold"
    assert busan_council.verification_status_label == "법적 검토 보류"
    assert "공공누리 유형 표시" in busan_council.evidence_note
    assert "제1유형 확인 전까지 수집하지 않습니다" in busan_council.evidence_note

    busan_city = next(entry for entry in non_capital_entries if entry.short_name == "부산시청")
    daegu_city = next(entry for entry in non_capital_entries if entry.short_name == "대구시청")
    daegu_council = next(entry for entry in non_capital_entries if entry.short_name == "대구시의회")
    assert busan_city.verification_status == "legal_hold"
    assert "보안 장비 차단" in busan_city.evidence_note
    assert daegu_city.verification_status == "legal_hold"
    assert "사전 협의" in daegu_city.evidence_note
    assert daegu_council.verification_status == "legal_hold"
    assert "공공누리 표시가 부착된 공공저작물" in daegu_council.evidence_note

    gwangju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "광주시청"
    )
    gwangju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "광주시의회"
    )
    assert gwangju_city.verification_status == "legal_hold"
    assert "자유이용 불가" in gwangju_city.evidence_note
    assert gwangju_council.verification_status == "legal_hold"
    assert "제1유형 확인 전까지 수집하지 않습니다" in gwangju_council.evidence_note

    daejeon_city = next(entry for entry in non_capital_entries if entry.short_name == "대전시청")
    daejeon_council = next(entry for entry in non_capital_entries if entry.short_name == "대전시의회")
    sejong_city = next(entry for entry in non_capital_entries if entry.short_name == "세종시청")
    sejong_council = next(entry for entry in non_capital_entries if entry.short_name == "세종시의회")
    assert daejeon_city.verification_status == "verified_in_code"
    assert daejeon_city.source_url == (
        "https://www.daejeon.go.kr/drh/open/drhDataOpen/drhDataOpenBoardView.do?boardSeq=747&menuSeq=4804"
    )
    assert daejeon_city.homepage == "https://www.daejeon.go.kr"
    assert daejeon_city.verified_at == "2026-06-01"
    assert daejeon_council.verification_status == "verified_in_code"
    assert daejeon_council.source_url == (
        "https://council.daejeon.go.kr/svc/inf/OperatingExpenseList.do"
    )
    assert daejeon_council.homepage == "https://council.daejeon.go.kr"
    gumi_city = next(entry for entry in non_capital_entries if entry.short_name == "구미시청")
    assert gumi_city.verification_status == "verified_in_code"
    assert gumi_city.source_url == (
        "https://www.gumi.go.kr/portal/board/post/list.do?"
        "bcIdx=164&mid=0303100000"
    )
    assert gumi_city.homepage == "https://www.gumi.go.kr"
    assert gumi_city.source_file_kinds == ["xlsx", "xls"]
    assert gumi_city.verified_at == "2026-06-01"
    miryang_city = next(entry for entry in non_capital_entries if entry.short_name == "밀양시청")
    assert miryang_city.verification_status == "verified_in_code"
    assert miryang_city.source_url == (
        "https://www.miryang.go.kr/twn/bbs/selectBoardList.do?"
        "bbsId=BBSMSTR_000000085910&mnNo=3040000&owd=sammun"
    )
    assert miryang_city.homepage == "https://www.miryang.go.kr"
    assert miryang_city.source_file_kinds == ["xlsx"]
    assert miryang_city.verified_at == "2026-06-01"
    jeonnam_city = next(entry for entry in non_capital_entries if entry.short_name == "전라남도청")
    jeonnam_council = next(entry for entry in non_capital_entries if entry.short_name == "전라남도의회")
    gokseong_city = next(entry for entry in non_capital_entries if entry.short_name == "곡성군청")
    gokseong_council = next(entry for entry in non_capital_entries if entry.short_name == "곡성군의회")
    jindo_city = next(entry for entry in non_capital_entries if entry.short_name == "진도군청")
    jangseong_city = next(entry for entry in non_capital_entries if entry.short_name == "장성군청")
    jangseong_council = next(entry for entry in non_capital_entries if entry.short_name == "장성군의회")
    shinan_city = next(entry for entry in non_capital_entries if entry.short_name == "신안군청")
    shinan_council = next(entry for entry in non_capital_entries if entry.short_name == "신안군의회")
    assert jeonnam_city.verification_status == "adapter_hold"
    assert jeonnam_city.source_url == (
        "https://www.jeonnam.go.kr/M1925005/boardList.do?menuId=jeonnam0302050100"
    )
    assert jeonnam_city.homepage is None
    assert jeonnam_city.source_file_kinds == ["hwp"]
    assert jeonnam_city.verified_at == "2026-06-02"
    assert "공공누리 제1유형 표시" in jeonnam_city.evidence_note
    assert "HWP 본문 추출" in jeonnam_city.evidence_note
    assert gokseong_city.verification_status == "verified_in_code"
    assert gokseong_city.source_url == (
        "https://www.gokseong.go.kr/kr/board/list.do?"
        "bbsId=BBS_000000000000540&menuNo=102006001000"
    )
    assert gokseong_city.homepage == "https://www.gokseong.go.kr"
    assert gokseong_council.verification_status == "verified_in_code"
    assert gokseong_council.source_url == (
        "https://www.gokseong.go.kr/council/board/list.do?"
        "bbsId=BBS_000000000000380&menuNo=106005004000"
    )
    assert gokseong_council.homepage == "https://www.gokseong.go.kr"
    assert jindo_city.verification_status == "verified_in_code"
    assert jindo_city.source_url == "https://www.jindo.go.kr/home/board/B0071.cs?m=52"
    assert jindo_city.homepage == "https://www.jindo.go.kr"
    assert jindo_city.source_file_kinds == ["pdf"]
    assert jindo_city.verified_at == "2026-06-01"
    assert jindo_city.verified_by == "공식 사이트 원격 확인"
    assert jangseong_city.verification_status == "legal_hold"
    assert jangseong_city.source_url == (
        "https://www.jangseong.go.kr/home/www/gov3/gov3_13/gov3_13_03"
    )
    assert jangseong_city.source_file_kinds == ["xlsx", "pdf"]
    assert "공공누리가 부착되지 않은 자료" in jangseong_city.evidence_note
    assert jangseong_council.verification_status == "legal_hold"
    assert jangseong_council.source_url == (
        "https://www.jangseong.go.kr/home/council/info/info_18/info_01_04"
    )
    assert jangseong_council.source_file_kinds == ["pdf"]
    assert "공공누리 미부착 자료 이용 시 사전 협의" in jangseong_council.evidence_note
    assert shinan_city.verification_status == "legal_hold"
    assert shinan_city.source_url == (
        "https://www.shinan.go.kr/home/www/gov30/gov30_08/gov30_09_01_05"
    )
    assert shinan_city.source_file_kinds == ["xlsx"]
    assert "신안군청 행정정보공개 업무추진비 목록" in shinan_city.evidence_note
    assert "공공누리가 부착되지 않은 자료" in shinan_city.evidence_note
    assert shinan_council.verification_status == "legal_hold"
    assert shinan_council.source_url == (
        "https://www.shinan.go.kr/home/council/function/function_18/page.wscms"
    )
    assert shinan_council.source_file_kinds == ["pdf"]
    assert "신안군의회 의정활동 업무추진비 목록" in shinan_council.evidence_note
    assert "사전 협의" in shinan_council.evidence_note
    assert jeonnam_council.verification_status == "legal_hold"
    assert jeonnam_council.source_url == "https://www.jnassembly.go.kr/jnassem/board/412"
    assert "의정활동 정보공개 업무추진비 목록" in jeonnam_council.evidence_note
    assert "제1유형 확인 전까지 수집하지 않습니다" in jeonnam_council.evidence_note
    assert sejong_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in sejong_city.evidence_note
    assert sejong_council.verification_status == "verified_in_code"
    assert sejong_council.source_url == (
        "https://council.sejong.go.kr/mnu/cap/businessExpenseList.do"
    )
    assert "facts-only 적재 정책" in sejong_council.verified_by

    gangwon_city = next(
        entry for entry in non_capital_entries if entry.short_name == "강원특별자치도청"
    )
    gangwon_council = next(
        entry for entry in non_capital_entries if entry.short_name == "강원특별자치도의회"
    )
    assert gangwon_city.verification_status == "legal_hold"
    assert gangwon_city.list_url == (
        "https://state.gwd.go.kr/portal/administration/opendata/propulsionCost/governor"
    )
    assert gangwon_city.copyright_url == "https://state.gwd.go.kr/portal/services/copyright"
    assert gangwon_city.public_works_policy_url == (
        "https://state.gwd.go.kr/portal/services/copyright"
    )
    assert gangwon_city.commercial_use_status == "not_confirmed_without_kogl_type1"
    assert gangwon_city.derivative_use_status == "not_confirmed_without_kogl_type1"
    assert "도지사·부지사 업무추진비 목록" in gangwon_city.evidence_note
    assert "XLSX 다운로드 구조" in gangwon_city.evidence_note
    assert "첨부 내부 문자열 검사" in gangwon_city.evidence_note
    assert gangwon_council.verification_status == "legal_hold"
    assert gangwon_council.copyright_url == (
        "https://council.gangwon.kr/kr/infoBBSview.do?"
        "uid=3EDF15021B1FDB4D25D06BF8BBA2437A&schwrd=&flag=all&sch_use_start_date="
        "&sch_use_end_date=&page=1&list_style="
    )
    assert "PDF/XLS 다운로드 구조" in gangwon_council.evidence_note
    assert "첨부 내부 문자열 검사" in gangwon_council.evidence_note
    yeongwol_city = next(entry for entry in non_capital_entries if entry.short_name == "영월군청")
    chuncheon_city = next(entry for entry in non_capital_entries if entry.short_name == "춘천시청")
    wonju_council = next(entry for entry in non_capital_entries if entry.short_name == "원주시의회")
    donghae_city = next(entry for entry in non_capital_entries if entry.short_name == "동해시청")
    donghae_council = next(
        entry for entry in non_capital_entries if entry.short_name == "동해시의회"
    )
    sokcho_city = next(entry for entry in non_capital_entries if entry.short_name == "속초시청")
    taebaek_council = next(entry for entry in non_capital_entries if entry.short_name == "태백시의회")
    gangneung_city = next(entry for entry in non_capital_entries if entry.short_name == "강릉시청")
    hoengseong_council = next(entry for entry in non_capital_entries if entry.short_name == "횡성군의회")
    cheorwon_city = next(entry for entry in non_capital_entries if entry.short_name == "철원군청")
    cheorwon_council = next(
        entry for entry in non_capital_entries if entry.short_name == "철원군의회"
    )
    hwacheon_city = next(entry for entry in non_capital_entries if entry.short_name == "화천군청")
    jeongseon_city = next(entry for entry in non_capital_entries if entry.short_name == "정선군청")
    yanggu_city = next(entry for entry in non_capital_entries if entry.short_name == "양구군청")
    yanggu_council = next(entry for entry in non_capital_entries if entry.short_name == "양구군의회")
    goseong_city = next(entry for entry in non_capital_entries if entry.short_name == "고성군청")
    goseong_council = next(entry for entry in non_capital_entries if entry.short_name == "고성군의회")
    yangyang_city = next(entry for entry in non_capital_entries if entry.short_name == "양양군청")
    yangyang_council = next(entry for entry in non_capital_entries if entry.short_name == "양양군의회")
    assert yeongwol_city.verification_status == "verified_in_code"
    assert yeongwol_city.source_url == "https://www.yw.go.kr/www/selectBbsNttList.do?bbsNo=7&key=196"
    assert yeongwol_city.detail_url == (
        "https://www.yw.go.kr/www/selectBbsNttView.do?"
        "key=196&bbsNo=7&nttNo=154331&searchCtgry=&searchCnd=all&searchKrwd="
        "&pageIndex=1&integrDeptCode=&pageUnit=10"
    )
    assert yeongwol_city.attachment_url == (
        "https://www.yw.go.kr/www/downloadBbsFile.do?bbsNo=7&atchmnflNo=131573"
    )
    assert yeongwol_city.public_works_policy_url == "https://www.yw.go.kr/www/contents.do?key=528"
    assert yeongwol_city.commercial_use_status == "allowed_kogl_type1_commercial"
    assert yeongwol_city.derivative_use_status == "allowed_kogl_type1_derivatives"
    assert yeongwol_city.source_file_kinds == ["xlsx"]
    assert "첨부 내부 문자열 검사" not in yeongwol_city.evidence_note
    assert "kogl_box type1" in yeongwol_city.evidence_note
    assert "production 적재가 완료" in yeongwol_city.evidence_note
    assert chuncheon_city.verification_status == "legal_hold"
    assert "춘천시청 업무추진비 집행내역 목록" in chuncheon_city.evidence_note
    assert wonju_council.verification_status == "legal_hold"
    assert "원주시의회 업무추진비 현황 목록" in wonju_council.evidence_note
    assert donghae_city.verification_status == "legal_hold"
    assert donghae_city.detail_url == (
        "https://www.dh.go.kr/www/selectBbsNttView.do?"
        "key=237&bbsNo=67&nttNo=201950&searchCtgry=&searchCnd=all&searchKrwd=&integrDeptCode=&pageIndex=1"
    )
    assert donghae_city.attachment_url == (
        "https://www.dh.go.kr/www/downloadBbsFile.do?atchmnflNo=249725"
    )
    assert "koglUseAt=N" in donghae_city.evidence_note
    assert donghae_council.list_url == (
        "https://www.dhcc.go.kr/content/news/operatingExpenseList.html"
    )
    assert donghae_council.attachment_url == (
        "https://www.dhcc.go.kr/gtb_download.php?gtid=information&fid=17405"
    )
    assert donghae_council.copyright_url == (
        "https://www.dhcc.go.kr/content/news/operatingExpenseList.html?"
        "fidx=6975&pg=vv&sid=1000&page=1&sword="
    )
    assert sokcho_city.detail_url == (
        "https://www.sokcho.go.kr/sc/portal/adminfo/disclosure/expense/mayor"
    )
    assert taebaek_council.verification_status == "legal_hold"
    assert taebaek_council.list_url == "https://council.taebaek.go.kr/source/kr/news/info2.html"
    assert taebaek_council.detail_url == (
        "https://council.taebaek.go.kr/source/kr/news/info2.html?mode=view&number=112"
    )
    assert taebaek_council.attachment_url == (
        "https://council.taebaek.go.kr/Mboard/download.html?"
        "table=board_official&column=userfile&uid=112"
    )
    assert taebaek_council.copyright_url == "https://www.taebaek.go.kr/www/sub.do?key=590"
    assert taebaek_council.public_works_policy_url == (
        "https://www.taebaek.go.kr/www/sub.do?key=590"
    )
    assert taebaek_council.commercial_use_status == "not_confirmed_without_kogl_mark"
    assert taebaek_council.derivative_use_status == "not_confirmed_without_kogl_mark"
    assert "태백시의회 정보공개 업무추진비 현황 목록" in taebaek_council.evidence_note
    assert "공공누리가 부착되지 않은 자료" in taebaek_council.evidence_note
    assert gangneung_city.verification_status == "legal_hold"
    assert gangneung_city.copyright_url == "https://www.gn.go.kr/www/sub.do?key=782"
    assert gangneung_city.public_works_policy_url == (
        "https://www.gn.go.kr/www/selectBbsNttList.do?bbsNo=4&key=20"
    )
    assert gangneung_city.commercial_use_status == "prohibited_kogl_type4_noncommercial"
    assert gangneung_city.derivative_use_status == "prohibited_kogl_type4_no_derivatives"
    assert "공공누리 제4유형" in gangneung_city.evidence_note
    assert hoengseong_council.verification_status == "legal_hold"
    assert hoengseong_council.detail_url == (
        "https://www.hsg.go.kr/council/selectBbsNttView.do?"
        "key=1464&bbsNo=41&nttNo=421094&pageUnit=10&searchCnd=all"
    )
    assert hoengseong_council.attachment_url == (
        "https://www.hsg.go.kr/council/downloadBbsFile.do?atchmnflNo=547678"
    )
    assert hoengseong_council.copyright_url == "https://www.hsg.go.kr/www/contents.do?key=906"
    assert hoengseong_council.public_works_policy_url == (
        "https://www.hsg.go.kr/www/contents.do?key=906"
    )
    assert "횡성군의회 공식 경로가 횡성군 통합 도메인" in hoengseong_council.evidence_note
    assert "공공누리가 부착되지 않은 자료" in hoengseong_council.evidence_note
    assert cheorwon_city.verification_status == "legal_hold"
    assert cheorwon_city.list_url == (
        "https://www.cwg.go.kr/www/selectInfoPublicWebList.do?"
        "key=183&searchCnd=all&searchKrwd=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84"
    )
    assert cheorwon_city.attachment_url == (
        "https://www.cwg.go.kr/www/pubDownload.do?idx=2089&key=183"
    )
    assert "기존 후보 URL" in cheorwon_city.evidence_note
    assert "2026년 1분기 단체장 업무추진비" in cheorwon_city.evidence_note
    assert cheorwon_council.attachment_url == (
        "https://council.cwg.go.kr/council/downloadBbsFile.do?"
        "atchmnflNo=170009&bbsNo=69&nttNo=277732"
    )
    assert hwacheon_city.verification_status == "legal_hold"
    assert "ALL RIGHTS RESERVED" in hwacheon_city.evidence_note
    assert jeongseon_city.public_works_policy_url == (
        "https://www.jeongseon.go.kr/portal/admininfo/openinfo/opendata"
    )
    assert yanggu_city.attachment_url == (
        "https://www.yanggu.go.kr/fnc_bbs/user_bbs_download?bcd=bpc_info&bn=155012&num=1"
    )
    assert yanggu_council.verification_status == "legal_hold"
    assert yanggu_council.list_url == "http://ygcl.go.kr/portal/F50000/F50700/boardList"
    assert yanggu_council.detail_url == (
        "http://ygcl.go.kr/portal/F50000/F50700/boardView?board_key=29098&page=1"
    )
    assert yanggu_council.attachment_url == (
        "http://ygcl.go.kr/downLoad.do?"
        "file_key=112148&save_file_name=202606011780277936024551.xlsx"
    )
    assert yanggu_council.commercial_use_status == "not_confirmed_without_kogl_mark"
    assert yanggu_council.derivative_use_status == "not_confirmed_without_kogl_mark"
    assert "총 80개 게시글" in yanggu_council.evidence_note
    assert "All Rights Reserved" in yanggu_council.evidence_note
    assert goseong_city.verification_status == "legal_hold"
    assert "공공누리 유형 영역이 비어" in goseong_city.evidence_note
    assert goseong_council.verification_status == "legal_hold"
    assert goseong_council.attachment_url == (
        "https://council.gwgs.go.kr/downLoad.do?"
        "file_key=22829&save_file_name=202604061775453177982507.xlsx"
    )
    assert "ALL RIGHT RESERVED" in goseong_council.evidence_note
    assert yangyang_city.list_url == (
        "https://www.yangyang.go.kr/gw/portal/yyc_opinfo_adinfo_oper_governor"
    )
    assert yangyang_city.commercial_use_status == "prohibited_kogl_type4_noncommercial"
    assert yangyang_city.derivative_use_status == "prohibited_kogl_type4_no_derivatives"
    assert "공공누리 제4유형" in yangyang_city.evidence_note
    assert yangyang_council.verification_status == "legal_hold"
    assert "양양군의회 업무추진비공개 목록" in yangyang_council.evidence_note

    jeonbuk_city = next(
        entry for entry in non_capital_entries if entry.short_name == "전북특별자치도청"
    )
    jeonbuk_council = next(
        entry for entry in non_capital_entries if entry.short_name == "전북특별자치도의회"
    )
    assert jeonbuk_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in jeonbuk_city.evidence_note
    assert "HWP/HWPX/XLSX/PDF 다운로드 구조" in jeonbuk_city.evidence_note
    assert jeonbuk_council.verification_status == "legal_hold"
    assert "XLSX/PDF/HWP 다운로드 구조" in jeonbuk_council.evidence_note

    chungnam_city = next(entry for entry in non_capital_entries if entry.short_name == "충청남도청")
    chungnam_council = next(
        entry for entry in non_capital_entries if entry.short_name == "충청남도의회"
    )
    assert chungnam_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in chungnam_city.evidence_note
    assert "HWP/PDF 다운로드 구조" in chungnam_city.evidence_note
    assert chungnam_council.verification_status == "pdf_vision_hold"
    assert "PDF vision extraction" in chungnam_council.evidence_note

    cheonan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "천안시청"
    )
    cheonan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "천안시의회"
    )
    gongju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "공주시청"
    )
    gongju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "공주시의회"
    )
    seosan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "서산시청"
    )
    boryeong_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "보령시청"
    )
    nonsan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "논산시청"
    )
    nonsan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "논산시의회"
    )
    buyeo_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "부여군청"
    )
    buyeo_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청남도" and entry.short_name == "부여군의회"
    )
    assert cheonan_city.verification_status == "adapter_hold"
    assert cheonan_city.source_url == "https://www.cheonan.go.kr/bbs/BBSMSTR_000000000050/list.do"
    assert "HTTP status 403" in cheonan_city.evidence_note
    assert cheonan_council.verification_status == "adapter_hold"
    assert "goBbsViewPage" in cheonan_council.evidence_note
    assert gongju_city.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in gongju_city.verified_by
    assert gongju_council.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in gongju_council.verified_by
    assert seosan_city.verification_status == "verified_in_code"
    assert seosan_city.source_url == (
        "https://www.seosan.go.kr/www/selectBbsNttList.do?bbsNo=114&key=1278"
    )
    assert seosan_city.verified_by == "공식 사이트 원격 확인"
    assert boryeong_city.verification_status == "verified_in_code"
    assert boryeong_city.source_url == (
        "https://www.brcn.go.kr/cop/bbs/BBSMSTR_000000000386/selectBoardList.do?"
        "bbsId=BBSMSTR_000000000386"
    )
    assert boryeong_city.homepage == "https://www.brcn.go.kr"
    assert boryeong_city.source_file_kinds == ["xls", "xlsx", "pdf"]
    assert boryeong_city.verified_at == "2026-06-01"
    assert boryeong_city.verified_by == "공식 사이트 원격 확인"
    assert nonsan_city.verification_status == "adapter_hold"
    assert "File is not a zip file" in nonsan_city.evidence_note
    assert nonsan_council.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in nonsan_council.verified_by
    assert buyeo_city.verification_status == "legal_hold"
    assert "HWP 다운로드 링크 구조" in buyeo_city.evidence_note
    assert buyeo_council.verification_status == "legal_hold"
    assert "목록 ZIP 다운로드" in buyeo_council.evidence_note

    chungbuk_city = next(entry for entry in non_capital_entries if entry.short_name == "충청북도청")
    chungbuk_council = next(
        entry for entry in non_capital_entries if entry.short_name == "충청북도의회"
    )
    cheongju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청북도" and entry.short_name == "청주시청"
    )
    cheongju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청북도" and entry.short_name == "청주시의회"
    )
    chungju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청북도" and entry.short_name == "충주시의회"
    )
    jecheon_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "충청북도" and entry.short_name == "제천시청"
    )
    assert chungbuk_city.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in chungbuk_city.verified_by
    assert chungbuk_council.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in chungbuk_council.verified_by
    assert cheongju_city.verification_status == "adapter_hold"
    assert "HTTP 200 block" in cheongju_city.evidence_note
    assert cheongju_council.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in cheongju_council.verified_by
    assert chungju_council.verification_status == "legal_hold"
    assert "화면 하단 저작권 문구" in chungju_council.evidence_note
    assert jecheon_city.verification_status == "legal_hold"
    assert "2025년 업무추진비 내역" in jecheon_city.evidence_note

    gyeongbuk_city = next(entry for entry in non_capital_entries if entry.short_name == "경상북도청")
    gyeongbuk_council = next(
        entry for entry in non_capital_entries if entry.short_name == "경상북도의회"
    )
    assert gyeongbuk_city.verification_status == "legal_hold"
    assert "공공누리 제3유형" in gyeongbuk_city.evidence_note
    assert "XLSX/XLS/PDF 다운로드 구조" in gyeongbuk_city.evidence_note
    assert gyeongbuk_council.verification_status == "legal_hold"
    assert "XLSX 다운로드 구조" in gyeongbuk_council.evidence_note

    gyeongnam_city = next(entry for entry in non_capital_entries if entry.short_name == "경상남도청")
    gyeongnam_council = next(
        entry for entry in non_capital_entries if entry.short_name == "경상남도의회"
    )
    jeju_city = next(entry for entry in non_capital_entries if entry.short_name == "제주특별자치도청")
    jeju_council = next(
        entry for entry in non_capital_entries if entry.short_name == "제주특별자치도의회"
    )
    jejusi_city = next(entry for entry in non_capital_entries if entry.short_name == "제주시청")
    seogwipo_city = next(entry for entry in non_capital_entries if entry.short_name == "서귀포시청")
    assert gyeongnam_city.verification_status == "legal_hold"
    assert "자유이용을 불가" in gyeongnam_city.evidence_note
    assert gyeongnam_council.verification_status == "legal_hold"
    assert "PDF 다운로드 구조" in gyeongnam_council.evidence_note
    assert jeju_city.verification_status == "verified_in_code"
    assert jeju_city.source_url == "https://www.jeju.go.kr/open/open/work/work2.htm?category=1409"
    assert jeju_city.homepage == "https://www.jeju.go.kr"
    assert "도 본청 업무추진비" in jeju_city.evidence_note
    assert "공공저작물 이용안내" in jeju_city.evidence_note
    assert jeju_council.verification_status == "verified_in_code"
    assert jeju_council.source_url == "https://www.council.jeju.kr/clicknews/openpromotion.do"
    assert jeju_council.homepage == "https://www.council.jeju.kr"
    assert "업무추진비 현황" in jeju_council.evidence_note
    assert "의회 이용약관" in jeju_council.evidence_note
    assert jejusi_city.verification_status == "verified_in_code"
    assert jejusi_city.source_url == "https://www.jejusi.go.kr/information/status/sijang.do"
    assert jejusi_city.homepage == "https://www.jejusi.go.kr"
    assert jejusi_city.branch == "admin"
    assert "부서별 업무추진비 공개" in jejusi_city.evidence_note
    assert "산하 행정시" in jejusi_city.evidence_note
    assert seogwipo_city.verification_status == "verified_in_code"
    assert seogwipo_city.source_url == "https://www.seogwipo.go.kr/info/gov/open/expense.htm"
    assert seogwipo_city.homepage == "https://www.seogwipo.go.kr"
    assert seogwipo_city.branch == "admin"
    assert "업무추진비공개" in seogwipo_city.evidence_note
    assert "산하 행정시" in seogwipo_city.evidence_note

    ulsan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "울산시청"
    )
    ulsan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "울산시의회"
    )
    ulsan_namgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "남구청"
    )
    ulsan_junggu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "중구청"
    )
    ulsan_junggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "중구의회"
    )
    ulsan_namgu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "남구의회"
    )
    ulsan_bukgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "북구청"
    )
    ulsan_bukgu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "북구의회"
    )
    ulju_office = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "울주군청"
    )
    ulju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "울주군의회"
    )
    assert ulsan_city.verification_status == "legal_hold"
    assert ulsan_city.verification_status_label == "법적 검토 보류"
    assert "HTML 상세 표 구조" in ulsan_city.evidence_note
    assert "사용일자·결제내용·결제방법" in ulsan_city.evidence_note
    assert ulsan_council.verification_status == "legal_hold"
    assert "XLSX 다운로드 구조" in ulsan_council.evidence_note
    assert ulsan_junggu.verification_status == "legal_hold"
    assert "부구청장 업무추진비 ZIP 첨부" in ulsan_junggu.evidence_note
    assert ulsan_junggu_council.verification_status == "legal_hold"
    assert "업무추진비 현황 경로" in ulsan_junggu_council.evidence_note
    assert ulsan_namgu.verification_status == "legal_hold"
    assert "구청장·부구청장·국장·부서장·동장·보건소" in ulsan_namgu.evidence_note
    assert ulsan_namgu_council.verification_status == "legal_hold"
    assert "의정운영공통경비 PDF 첨부" in ulsan_namgu_council.evidence_note
    assert ulsan_bukgu.verification_status == "legal_hold"
    assert "공공누리 제4유형" in ulsan_bukgu.evidence_note
    assert ulsan_bukgu_council.verification_status == "legal_hold"
    assert "ALL RIGHTS RESERVED" in ulsan_bukgu_council.evidence_note
    assert ulju_office.verification_status == "legal_hold"
    assert "부군수·국장·부서장 탭" in ulju_office.evidence_note
    assert ulju_council.verification_status == "legal_hold"
    assert "XLSX 다운로드 구조" in ulju_council.evidence_note
    ulsan_donggu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "동구청"
    )
    ulsan_donggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "울산광역시" and entry.short_name == "동구의회"
    )
    assert ulsan_donggu.verification_status == "legal_hold"
    assert "공공누리 제2유형" in ulsan_donggu.evidence_note
    assert ulsan_donggu_council.verification_status == "legal_hold"
    assert "의정운영공통경비" in ulsan_donggu_council.evidence_note

    daegu_namgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "남구청"
    )
    daegu_bukgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "북구청"
    )
    daegu_suseong = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "수성구청"
    )
    daegu_seogu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "서구청"
    )
    daegu_junggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "중구의회"
    )
    daegu_donggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "동구의회"
    )
    daegu_seogu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "서구의회"
    )
    daegu_bukgu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "북구의회"
    )
    daegu_suseong_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "수성구의회"
    )
    daegu_dalseo = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "달서구청"
    )
    daegu_dalseo_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "달서구의회"
    )
    daegu_dalseong = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "달성군청"
    )
    daegu_dalseong_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "달성군의회"
    )
    daegu_gunwi = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대구광역시" and entry.short_name == "군위군청"
    )
    assert daegu_namgu.verification_status == "legal_hold"
    assert "XLS/XLSX 첨부 구조" in daegu_namgu.evidence_note
    assert daegu_bukgu.verification_status == "legal_hold"
    assert "공공누리 제4유형" in daegu_bukgu.evidence_note
    assert daegu_suseong.verification_status == "legal_hold"
    assert "공공누리 영역이 비어" in daegu_suseong.evidence_note
    assert daegu_seogu.verification_status == "legal_hold"
    assert "사전정보공표 업무추진비 공개" in daegu_seogu.evidence_note
    assert daegu_junggu_council.verification_status == "legal_hold"
    assert "의회운영업무추진비 XLS 첨부 구조" in daegu_junggu_council.evidence_note
    assert daegu_donggu_council.verification_status == "legal_hold"
    assert "업무추진비·공통경비 PDF 첨부 구조" in daegu_donggu_council.evidence_note
    assert daegu_seogu_council.verification_status == "legal_hold"
    assert daegu_seogu_council.source_url == "https://dgscouncil.go.kr/kr/bbs?bbs_id=cost"
    assert "XLSX 첨부 구조" in daegu_seogu_council.evidence_note
    assert "All Rights Reserved" in daegu_seogu_council.evidence_note
    assert daegu_bukgu_council.verification_status == "legal_hold"
    assert daegu_bukgu_council.source_url == "https://www.bukgucouncil.daegu.kr/kr/costBBS.do"
    assert "의정운영공통경비 PDF 첨부 구조" in daegu_bukgu_council.evidence_note
    assert "All Rights Reserved" in daegu_bukgu_council.evidence_note
    assert daegu_suseong_council.verification_status == "legal_hold"
    assert "업무추진비 XLS 첨부 구조" in daegu_suseong_council.evidence_note
    assert daegu_dalseo.verification_status == "legal_hold"
    assert "공공누리 영역이 비어" in daegu_dalseo.evidence_note
    assert daegu_dalseo_council.verification_status == "legal_hold"
    assert "의정공통경비 XLSX 첨부 구조" in daegu_dalseo_council.evidence_note
    assert daegu_dalseong.verification_status == "legal_hold"
    assert "XLS/XLSX 첨부 구조" in daegu_dalseong.evidence_note
    assert daegu_dalseong_council.verification_status == "legal_hold"
    assert "업무추진비 XLS 첨부 구조" in daegu_dalseong_council.evidence_note
    assert daegu_gunwi.verification_status == "pdf_vision_hold"
    assert daegu_gunwi.source_url == "https://www.gunwi.go.kr/ko/page.do?mnu_uid=160"
    assert "scanned PDF vision extraction" in daegu_gunwi.evidence_note

    geumjeong_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "금정구청"
    )
    assert geumjeong_city.verification_status == "legal_hold"
    assert "HWPX/XLSX 첨부 구조" in geumjeong_city.evidence_note
    assert "공공누리 제4유형" in geumjeong_city.evidence_note
    busan_seogu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "서구청"
    )
    busan_namgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "남구청"
    )
    busan_donggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "동구의회"
    )
    assert busan_seogu.verification_status == "adapter_hold"
    assert "HWP 본문 추출" in busan_seogu.evidence_note
    assert busan_namgu.verification_status == "legal_hold"
    assert "국장급 이상 업무추진비" in busan_namgu.evidence_note
    assert busan_donggu_council.verification_status == "legal_hold"
    assert "의장단 업무추진비 공개 목록" in busan_donggu_council.evidence_note
    assert "공공누리 제4유형" in busan_donggu_council.evidence_note
    busan_junggu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "중구청"
    )
    busan_dongnae = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "동래구청"
    )
    busan_bukgu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "북구청"
    )
    busan_gangseo = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "강서구청"
    )
    busan_gangseo_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "강서구의회"
    )
    busan_yeonje = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "연제구청"
    )
    busan_gijang = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "부산광역시" and entry.short_name == "기장군청"
    )
    assert busan_junggu.verification_status == "legal_hold"
    assert "업무추진비 공개 목록" in busan_junggu.evidence_note
    assert busan_dongnae.verification_status == "legal_hold"
    assert "자유이용 불가 안내" in busan_dongnae.evidence_note
    assert busan_bukgu.verification_status == "legal_hold"
    assert "공공누리 미부착 자료의 사전 협의" in busan_bukgu.evidence_note
    assert busan_gangseo.verification_status == "legal_hold"
    assert "과장급 이상 업무추진비" in busan_gangseo.evidence_note
    assert busan_gangseo_council.verification_status == "legal_hold"
    assert "의회 업무추진비 사용내역" in busan_gangseo_council.evidence_note
    assert busan_yeonje.verification_status == "legal_hold"
    assert "상업적 목적 사용 불가" in busan_yeonje.evidence_note
    assert busan_gijang.verification_status == "legal_hold"
    assert "HTML 표" in busan_gijang.evidence_note

    mokpo_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "목포시청"
    )
    mokpo_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "목포시의회"
    )
    naju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "나주시청"
    )
    gurye_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "구례군청"
    )
    gurye_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "구례군의회"
    )
    goheung_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "고흥군청"
    )
    goheung_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "고흥군의회"
    )
    yeosu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "여수시청"
    )
    gwangyang_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "광양시청"
    )
    suncheon_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "순천시청"
    )
    gangjin_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "강진군청"
    )
    gangjin_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전라남도" and entry.short_name == "강진군의회"
    )
    assert mokpo_city.verification_status == "legal_hold"
    assert "공공누리 유형 표시가 비어" in mokpo_city.evidence_note
    assert mokpo_council.verification_status == "legal_hold"
    assert "명확한 자유이용 표시" in mokpo_council.evidence_note
    assert naju_city.verification_status == "legal_hold"
    assert "본문이 0바이트" in naju_city.evidence_note
    assert gurye_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in gurye_city.evidence_note
    assert gurye_council.verification_status == "legal_hold"
    assert "전체 ZIP 다운로드 구조" in gurye_council.evidence_note
    assert goheung_city.verification_status == "legal_hold"
    assert "사전정보공개 업무추진비 공개 목록" in goheung_city.evidence_note
    assert goheung_council.verification_status == "legal_hold"
    assert "경로형 페이지네이션" in goheung_council.evidence_note
    assert yeosu_city.verification_status == "legal_hold"
    assert "PDF/ZIP 다운로드 구조" in yeosu_city.evidence_note
    assert "공공누리 제4유형" in yeosu_city.evidence_note
    assert gwangyang_city.verification_status == "legal_hold"
    assert "HTML 표 구조" in gwangyang_city.evidence_note
    assert "출처표시+상업적이용금지+변경금지" in gwangyang_city.evidence_note
    assert suncheon_city.verification_status == "legal_hold"
    assert "PDF/HWPX 다운로드 구조" in suncheon_city.evidence_note
    assert "출처표시-비상업적-변경금지" in suncheon_city.evidence_note
    assert gangjin_city.verification_status == "legal_hold"
    assert "file_download XLSX 다운로드" in gangjin_city.evidence_note
    assert "All Rights Reserved" in gangjin_city.evidence_note
    assert gangjin_council.verification_status == "legal_hold"
    assert "2025년 4분기" in gangjin_council.evidence_note
    assert "All rights reserved" in gangjin_council.evidence_note

    gwangju_donggu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "동구청"
    )
    gwangju_donggu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "동구의회"
    )
    gwangju_seogu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "서구청"
    )
    gwangju_seogu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "서구의회"
    )
    gwangju_namgu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "남구청"
    )
    gwangju_bukgu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "북구청"
    )
    gwangju_bukgu_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "북구의회"
    )
    gwangju_gwangsan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "광주광역시" and entry.short_name == "광산구청"
    )
    assert gwangju_donggu_city.verification_status == "legal_hold"
    assert "부서장 업무추진비 목록" in gwangju_donggu_city.evidence_note
    assert "공공누리 제4유형" in gwangju_donggu_city.evidence_note
    assert gwangju_donggu_council.verification_status == "legal_hold"
    assert "업무추진비 현황 목록과 XLSX 첨부" in gwangju_donggu_council.evidence_note
    assert "제1유형 확인 전까지 수집하지 않습니다" in gwangju_donggu_council.evidence_note
    assert gwangju_seogu_city.verification_status == "legal_hold"
    assert "국장급이상 업무추진비 공개" in gwangju_seogu_city.evidence_note
    assert "All Rights Reserved" in gwangju_seogu_city.evidence_note
    assert gwangju_seogu_council.verification_status == "no_recent_data"
    assert "2023-08-29" in gwangju_seogu_council.evidence_note
    assert "최근 12개월 적재 대상 데이터가 없습니다" in gwangju_seogu_council.evidence_note
    assert gwangju_namgu_city.verification_status == "legal_hold"
    assert "업무추진비 공개 목록" in gwangju_namgu_city.evidence_note
    assert "공공누리 제4유형" in gwangju_namgu_city.evidence_note
    assert gwangju_bukgu_city.verification_status == "legal_hold"
    assert "업무추진비공개 목록" in gwangju_bukgu_city.evidence_note
    assert "사전 협의" in gwangju_bukgu_city.evidence_note
    assert gwangju_bukgu_council.verification_status == "legal_hold"
    assert gwangju_bukgu_council.source_url == (
        "https://council.bukgu.gwangju.kr/index.do?PID=094"
    )
    assert gwangju_bukgu_council.detail_url == (
        "https://council.bukgu.gwangju.kr/index.do?PID=094&bbsSn=28777"
    )
    assert gwangju_bukgu_council.attachment_url == (
        "https://council.bukgu.gwangju.kr/download.do?attSeq=83251&bbsSn=28777"
    )
    assert gwangju_bukgu_council.source_file_kinds == ["xlsx"]
    assert gwangju_bukgu_council.commercial_use_status == "not_confirmed_without_kogl_mark"
    assert gwangju_bukgu_council.derivative_use_status == "not_confirmed_without_kogl_mark"
    assert "업무추진비 현황" in gwangju_bukgu_council.evidence_note
    assert "ALL RIGHTS RESERVED" in gwangju_bukgu_council.evidence_note
    assert gwangju_gwangsan_city.verification_status == "legal_hold"
    assert "getInfoOpenList.do/getInfoOpenData.do" in gwangju_gwangsan_city.evidence_note
    assert "2026-05-29" in gwangju_gwangsan_city.evidence_note
    assert "공공누리 제4유형" in gwangju_gwangsan_city.evidence_note

    jeonju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "전주시청"
    )
    gunsan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "군산시의회"
    )
    jeonju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "전주시의회"
    )
    gunsan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "군산시청"
    )
    iksan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "익산시의회"
    )
    jinan_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "진안군청"
    )
    jinan_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "진안군의회"
    )
    namwon_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "남원시청"
    )
    jangsu_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "전북특별자치도" and entry.short_name == "장수군청"
    )
    assert jeonju_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in jeonju_city.evidence_note
    assert "HWPX/PDF/XLSX 다운로드 구조" in jeonju_city.evidence_note
    assert jeonju_council.verification_status == "legal_hold"
    assert "2026년 1분기" in jeonju_council.evidence_note
    assert "ALL RIGHTS RESERVED" in jeonju_council.evidence_note
    assert gunsan_city.verification_status == "legal_hold"
    assert "eFileDownload 첨부 구조" in gunsan_city.evidence_note
    assert "공공누리 제4유형" in gunsan_city.evidence_note
    assert gunsan_council.verification_status == "legal_hold"
    assert "PDF/XLS/XLSX 다운로드 구조" in gunsan_council.evidence_note
    assert iksan_council.verification_status == "legal_hold"
    assert "상세·PDF 다운로드 구조" in iksan_council.evidence_note
    assert "공공누리 제4유형" in iksan_council.evidence_note
    assert jinan_city.verification_status == "legal_hold"
    assert "2025년 6~12월" in jinan_city.evidence_note
    assert "공공누리 표시가 부착된 저작물만" in jinan_city.evidence_note
    assert jinan_council.verification_status == "legal_hold"
    assert "업무추진비 공개 메뉴" in jinan_council.evidence_note
    assert "All rights reserved" in jinan_council.evidence_note
    assert namwon_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in namwon_city.evidence_note
    assert jangsu_city.verification_status == "legal_hold"
    assert "상세·PDF 다운로드 구조" in jangsu_city.evidence_note
    assert "공공누리 제4유형" in jangsu_city.evidence_note

    pohang_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "포항시청"
    )
    pohang_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "포항시의회"
    )
    assert pohang_city.verification_status == "legal_hold"
    assert "XLSX 다운로드 구조" in pohang_city.evidence_note
    assert pohang_council.verification_status == "legal_hold"
    assert "PDF 다운로드 구조" in pohang_council.evidence_note
    mungyeong_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "문경시청"
    )
    gyeongju_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "경주시의회"
    )
    gimcheon_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "김천시청"
    )
    andong_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상북도" and entry.short_name == "안동시청"
    )
    assert mungyeong_city.verification_status == "legal_hold"
    assert "공공누리 제4유형" in mungyeong_city.evidence_note
    assert gyeongju_council.verification_status == "legal_hold"
    assert "분기별 PDF 첨부 구조" in gyeongju_council.evidence_note
    assert "All Rights Reserved" in gyeongju_council.evidence_note
    assert gimcheon_city.verification_status == "legal_hold"
    assert "일부 상세 HTML 표 구조" in gimcheon_city.evidence_note
    assert andong_city.verification_status == "legal_hold"
    assert "공공누리 자유이용 불가" in andong_city.evidence_note

    jinju_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "진주시청"
    )
    changwon_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "창원시청"
    )
    changwon_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "창원시의회"
    )
    assert jinju_city.verification_status == "legal_hold"
    assert "과장급·국소장급 업무추진비 목록" in jinju_city.evidence_note
    assert "게시물별 라이선스 필터" in jinju_city.evidence_note
    assert changwon_city.verification_status == "verified_in_code"
    assert changwon_city.source_url == (
        "https://www.changwon.go.kr/cwportal/10312/10620/10629.web?gcode=1036"
    )
    assert changwon_city.homepage == "https://www.changwon.go.kr"
    assert changwon_city.source_file_kinds == ["xlsx", "pdf"]
    assert changwon_city.verified_at == "2026-06-01"
    assert changwon_city.verified_by == "공식 사이트 원격 확인"
    assert changwon_council.verification_status == "legal_hold"
    assert "PDF 다운로드 구조" in changwon_council.evidence_note
    gimhae_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "김해시청"
    )
    sancheong_city = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "산청군청"
    )
    hadong_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "경상남도" and entry.short_name == "하동군의회"
    )
    assert gimhae_city.verification_status == "legal_hold"
    assert "All Rights Reserved" in gimhae_city.evidence_note
    assert sancheong_city.verification_status == "legal_hold"
    assert "실제 공공누리 제1유형 표시" in sancheong_city.evidence_note
    assert hadong_council.verification_status == "source_not_found"

    daejeon_basic_hold_names = {
        entry.short_name
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시" and entry.verification_status == "legal_hold"
    }
    assert daejeon_basic_hold_names == {
        "동구청",
        "중구청",
        "서구청",
    }
    daejeon_verified_names = {
        entry.short_name
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시"
        and entry.verification_status == "verified_in_code"
    }
    assert daejeon_verified_names == {
        "대전시청",
        "대전시의회",
        "동구의회",
        "중구의회",
        "대덕구의회",
    }
    daejeon_pdf_hold_names = {
        entry.short_name
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시"
        and entry.verification_status == "pdf_vision_hold"
    }
    assert daejeon_pdf_hold_names == {"유성구청", "대덕구청"}
    daejeon_adapter_hold_names = {
        entry.short_name
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시"
        and entry.verification_status == "adapter_hold"
    }
    assert daejeon_adapter_hold_names == {"유성구의회"}
    daejeon_source_not_found_names = {
        entry.short_name
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시"
        and entry.verification_status == "source_not_found"
    }
    assert daejeon_source_not_found_names == {"서구의회"}
    daejeon_junggu = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시" and entry.short_name == "중구청"
    )
    assert "공공누리가 부착되지 않은 자료" in daejeon_junggu.evidence_note
    daejeon_daedeok_council = next(
        entry
        for entry in non_capital_entries
        if entry.parent_region == "대전광역시" and entry.short_name == "대덕구의회"
    )
    assert daejeon_daedeok_council.verification_status == "verified_in_code"
    assert "facts-only 적재 정책" in daejeon_daedeok_council.verified_by

    sejong = next(entry for entry in entries if entry.short_name == "세종시청")
    gangwon = next(entry for entry in entries if entry.short_name == "강원특별자치도청")
    assert sejong.jurisdiction_type_label == "특별자치시"
    assert gangwon.jurisdiction_type_label == "특별자치도"


def test_source_registry_exposes_public_sector_priority_group_metadata() -> None:
    entries = source_registry_entries(
        CENTRAL_STATE_AGENCIES + PUBLIC_INSTITUTION_AGENCIES + LOCAL_PUBLIC_INSTITUTION_AGENCIES
    )

    assert len(entries) == 1714
    assert {entry.priority_group for entry in entries} == {"p2", "p3", "p4"}
    assert sum(1 for entry in entries if entry.verification_status == "pending") == 0
    assert sum(1 for entry in entries if entry.verification_status == "verified_in_code") == 42
    assert sum(1 for entry in entries if entry.verification_status == "source_not_found") == 32
    assert sum(1 for entry in entries if entry.verification_status == "no_recent_data") == 294
    assert sum(1 for entry in entries if entry.verification_status == "pdf_vision_hold") == 8
    assert sum(1 for entry in entries if entry.verification_status == "adapter_hold") == 1338
    assert sum(1 for entry in entries if entry.verification_status == "invalid_source_pattern") == 0
    assert all(entry.baseline_source_url for entry in entries)
    assert all(any("가" <= char <= "힣" for char in entry.evidence_note) for entry in entries)

    science = next(entry for entry in entries if entry.short_name == "과학기술정보통신부")
    haeng = next(entry for entry in entries if entry.short_name == "행정안전부")
    audit = next(entry for entry in entries if entry.short_name == "감사원")
    court = next(entry for entry in entries if entry.short_name == "헌법재판소")
    nps = next(entry for entry in entries if entry.short_name == "국민연금공단")
    grac = next(entry for entry in entries if entry.short_name == "게임물관리위원회")

    assert science.priority_group_label == "P2 중앙행정기관·독립기관"
    assert science.jurisdiction_type_label == "중앙행정기관"
    assert science.verification_status == "source_not_found"
    assert "정부조직관리정보시스템" in science.evidence_note
    assert "source URL 미발견" in science.evidence_note
    assert haeng.verification_status == "adapter_hold"
    assert haeng.source_url == "https://mois.go.kr/frt/sub/a02/openBusinessPromotion/screen.do"
    assert audit.jurisdiction_type_label == "독립국가기관"
    assert court.gov_tier_label == "헌법기관"
    assert court.branch_label == "헌법기관"
    assert nps.priority_group_label == "P3 지정 공공기관"
    assert nps.gov_tier_label == "공공기관"
    assert nps.jurisdiction_type_label == "지정 공공기관"
    assert "잡알리오" in nps.evidence_note
    assert nps.verification_status == "no_recent_data"
    assert nps.source_url == "https://www.alio.go.kr/item/itemOrganList.do?reportFormRootNo=20701"
    assert grac.verification_status == "verified_in_code"
    assert grac.adapter == "alio_item_disclosure"
    assert grac.source_file_kinds == ["xlsx"]
    assert "사용처/장소" in grac.evidence_note

    knoc = next(entry for entry in entries if entry.short_name == "한국석유공사")
    gh = next(entry for entry in entries if entry.short_name == "경기주택도시공사")
    seoul_facility = next(entry for entry in entries if entry.short_name == "서울시설공단")
    assert knoc.verification_status == "verified_in_code"
    assert knoc.adapter == "alio_item_disclosure"
    assert gh.verification_status == "verified_in_code"
    assert gh.adapter == "cleaneye_owner_work_cost"
    assert gh.source_url == "https://www.cleaneye.go.kr/user/empOwnerWorkCost.do"
    assert "FileDownload.do" in gh.evidence_note
    assert seoul_facility.verification_status == "no_recent_data"
    assert "place-level" in seoul_facility.evidence_note

    local_public = next(entry for entry in entries if entry.priority_group == "p4")
    assert local_public.priority_group_label == "P4 지방공공기관"
    assert local_public.gov_tier_label == "지방공공기관"
    assert local_public.jurisdiction_type_label == "지방공공기관"
    assert local_public.verification_status == "adapter_hold"
    assert local_public.source_url == "https://www.cleaneye.go.kr/user/headOrgWorkCostStat.do"
    assert "클린아이" in local_public.evidence_note


def test_source_registry_keeps_incheon_name_collisions_disambiguated() -> None:
    entries = source_registry_entries(CAPITAL_AREA_AGENCIES)
    junggu_entries = [
        entry for entry in entries if entry.short_name == "중구청" and entry.branch == "admin"
    ]

    assert {entry.parent_region for entry in junggu_entries} == {"서울특별시", "인천광역시"}
    assert len({entry.agency_id for entry in junggu_entries}) == 2


def test_source_registry_rejects_new_region_verified_source_without_evidence() -> None:
    [entry] = source_registry_entries(
        [
            Agency(
                name="경기도 테스트청",
                short_name="테스트청",
                parent_region="경기도",
                homepage="https://example.go.kr",
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "https://example.go.kr/expense",
                    "fileKinds": ["xlsx"],
                },
            )
        ]
    )

    assert entry.verification_status == "invalid_source_pattern"
    assert "verifiedAt" in entry.evidence_note


def test_source_registry_rejects_new_region_verified_source_with_host_mismatch() -> None:
    [entry] = source_registry_entries(
        [
            Agency(
                name="경기도 테스트청",
                short_name="테스트청",
                parent_region="경기도",
                homepage="https://example.go.kr",
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "https://not-official.example.com/expense",
                    "fileKinds": ["xlsx"],
                    "verifiedAt": "2026-06-01",
                    "verifiedBy": "공식 사이트 원격 확인",
                },
            )
        ]
    )

    assert entry.verification_status == "invalid_source_pattern"
    assert "호스트" in entry.evidence_note


def test_source_registry_rejects_new_region_verified_source_with_relative_url() -> None:
    [entry] = source_registry_entries(
        [
            Agency(
                name="경기도 테스트청",
                short_name="테스트청",
                parent_region="경기도",
                homepage="https://example.go.kr",
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "/expense",
                    "fileKinds": ["xlsx"],
                    "verifiedAt": "2026-06-01",
                    "verifiedBy": "공식 사이트 원격 확인",
                },
            )
        ]
    )

    assert entry.verification_status == "invalid_source_pattern"
    assert "절대 경로" in entry.evidence_note


def test_source_registry_rejects_blank_new_region_evidence_fields() -> None:
    [entry] = source_registry_entries(
        [
            Agency(
                name="경기도 테스트청",
                short_name="테스트청",
                parent_region="경기도",
                homepage="https://example.go.kr",
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "https://example.go.kr/expense",
                    "fileKinds": ["xlsx"],
                    "verifiedAt": " ",
                    "verifiedBy": "공식 사이트 원격 확인",
                },
            )
        ]
    )

    assert entry.verification_status == "invalid_source_pattern"
    assert "verifiedAt" in entry.evidence_note


def test_source_registry_summary_counts_invalid_patterns() -> None:
    entries = source_registry_entries(
        [
            Agency(
                name="경기도 테스트청",
                short_name="테스트청",
                parent_region="경기도",
                source_pattern={"adapter": "unknown_adapter"},
            )
        ]
    )
    summary = source_registry_summary(entries)

    assert summary.total == 1
    assert summary.pending == 0
    assert summary.legal_hold == 0
    assert summary.invalid_source_pattern == 1
    assert entries[0].verification_status == "invalid_source_pattern"
