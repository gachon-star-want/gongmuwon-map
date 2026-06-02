from collections import Counter

from public_officer_pipeline.agencies import (
    CAPITAL_AREA_AGENCIES,
    CENTRAL_STATE_AGENCIES,
    GYEONGGI_AGENCIES,
    INCHEON_AGENCIES,
    LOCAL_GOVERNMENT_AGENCIES,
    LOCAL_PUBLIC_INSTITUTION_AGENCIES,
    NATIONWIDE_AGENCIES,
    NON_CAPITAL_AGENCIES,
    PUBLIC_INSTITUTION_AGENCIES,
    SEOUL_AGENCIES,
)
from public_officer_pipeline.models import (
    ExpansionPhase,
    GovBranch,
    GovTier,
    JurisdictionType,
    SEOUL_CITY_HALL_AGENCY_ID,
)


def test_seoul_agency_master_has_v1_scope() -> None:
    assert len(SEOUL_AGENCIES) == 52
    assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID


def test_seoul_agency_master_has_expected_kinds() -> None:
    counts = {
        (tier, branch): sum(
            1 for agency in SEOUL_AGENCIES if agency.gov_tier == tier and agency.branch == branch
        )
        for tier in GovTier
        for branch in GovBranch
    }

    assert counts[GovTier.REGIONAL, GovBranch.ADMIN] == 1
    assert counts[GovTier.REGIONAL, GovBranch.COUNCIL] == 1
    assert counts[GovTier.BASIC, GovBranch.ADMIN] == 25
    assert counts[GovTier.BASIC, GovBranch.COUNCIL] == 25
    assert all(
        agency.jurisdiction_type in {JurisdictionType.SPECIAL_CITY, JurisdictionType.AUTONOMOUS_GU}
        for agency in SEOUL_AGENCIES
    )


def test_seoul_agency_unique_identity_keys() -> None:
    keys = {
        (agency.gov_tier, agency.branch, agency.parent_region, agency.sub_region)
        for agency in SEOUL_AGENCIES
    }

    assert len(keys) == len(SEOUL_AGENCIES)


def test_seoul_council_homepages_use_verified_domains() -> None:
    gangnam_council = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강남구의회")
    gangseo_council = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강서구의회")

    assert gangnam_council.homepage == "https://www.gncouncil.go.kr"
    assert gangseo_council.homepage == "https://gsc.gangseo.seoul.kr"


def test_seoul_office_homepages_use_verified_domains() -> None:
    junggu = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "중구청")
    jungnang = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "중랑구청")

    assert junggu.homepage == "https://www.junggu.seoul.kr"
    assert jungnang.homepage == "https://www.jungnang.go.kr"


def test_seoul_council_attachment_boards_registered_for_verified_cost_pages() -> None:
    supported = {
        agency.short_name
        for agency in SEOUL_AGENCIES
        if agency.gov_tier == GovTier.BASIC
        and agency.branch == GovBranch.COUNCIL
        and agency.source_pattern.get("adapter") == "council_attachment_board"
    }

    assert supported == {
        "강남구의회",
        "강동구의회",
        "강북구의회",
        "강서구의회",
        "관악구의회",
        "광진구의회",
        "구로구의회",
        "금천구의회",
        "동대문구의회",
        "동작구의회",
        "도봉구의회",
        "마포구의회",
        "서대문구의회",
        "서초구의회",
        "성동구의회",
        "성북구의회",
        "송파구의회",
        "양천구의회",
        "영등포구의회",
        "용산구의회",
        "은평구의회",
        "노원구의회",
        "종로구의회",
        "중구의회",
        "중랑구의회",
    }

    gangdong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강동구의회")
    gwangjin = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "광진구의회")
    dobong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "도봉구의회")
    mapo = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "마포구의회")
    seodaemun = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "서대문구의회")
    seocho = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "서초구의회")
    seongdong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "성동구의회")
    seongbuk = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "성북구의회")
    songpa = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "송파구의회")
    yangcheon = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "양천구의회")
    yeongdeungpo = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "영등포구의회")
    jongno = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "종로구의회")
    junggu = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "중구의회")
    nowon = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "노원구의회")
    assert gangdong.source_pattern["followDetail"] is True
    assert gwangjin.source_pattern["followDetail"] is True
    assert dobong.source_pattern["followDetail"] is True
    assert mapo.source_pattern["followDetail"] is True
    assert seodaemun.source_pattern["followDetail"] is True
    assert seocho.source_pattern["followDetail"] is True
    assert seongdong.source_pattern["followDetail"] is True
    assert seongbuk.source_pattern["followDetail"] is True
    assert songpa.source_pattern["followDetail"] is True
    assert yangcheon.source_pattern["followDetail"] is True
    assert yeongdeungpo.source_pattern["followDetail"] is True
    assert nowon.source_pattern["followDetail"] is True
    assert jongno.source_pattern["followDetail"] is True
    assert junggu.source_pattern["followDetail"] is True


def test_seoul_office_html_estimate_board_registered_for_gwanak() -> None:
    gwanak = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "관악구청")

    assert gwanak.source_pattern["adapter"] == "estimate_list_html"
    assert (
        gwanak.source_pattern["listUrl"]
        == "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do"
    )


def test_seoul_office_attachment_board_registered_for_gangdong() -> None:
    gangdong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강동구청")

    assert gangdong.source_pattern["adapter"] == "attachment_board"
    assert (
        gangdong.source_pattern["listUrl"] == "https://www.gangdong.go.kr/web/newportal/bbs/b_054"
    )
    assert gangdong.source_pattern["followDetail"] is True


def test_seoul_office_attachment_boards_registered_for_egov_boards() -> None:
    supported = {
        agency.short_name: agency.source_pattern["listUrl"]
        for agency in SEOUL_AGENCIES
        if agency.gov_tier == GovTier.BASIC
        and agency.branch == GovBranch.ADMIN
        and agency.source_pattern.get("adapter") == "attachment_board"
    }

    assert (
        supported["강북구청"]
        == "https://child.gangbuk.go.kr/portal/intgty/deptJobPrtnCt/list.do?menuNo=200155"
    )
    assert supported["강서구청"] == "https://www.gangseo.seoul.kr/gs030325"
    assert (
        supported["광진구청"]
        == "https://www.gwangjin.go.kr/portal/bbs/B0000027/list.do?menuNo=201646"
    )
    assert (
        supported["구로구청"] == "https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=655&key=1732"
    )
    assert (
        supported["금천구청"]
        == "https://www.geumcheon.go.kr/portal/selectBbsNttList.do?bbsNo=86&key=269"
    )
    assert supported["도봉구청"] == "https://www.dobong.go.kr/Contents.asp?code=10008860"
    assert (
        supported["동대문구청"] == "https://www.ddm.go.kr/www/selectBbsNttList.do?bbsNo=160&key=565"
    )
    assert (
        supported["동작구청"]
        == "https://www.dongjak.go.kr/portal/bbs/B0000591/list.do?menuNo=200209"
    )
    assert supported["마포구청"] == "https://www.mapo.go.kr/site/main/board/expense/list"
    assert (
        supported["노원구청"]
        == "https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1012"
    )
    assert supported["서초구청"] == "https://www.seocho.go.kr/site/seocho/ex/bbs/List.do?cbIdx=33"
    assert supported["성동구청"] == "https://sd.go.kr/main/selectBbsNttList.do?bbsNo=172&key=1330"
    assert supported["성북구청"] == "https://www.sb.go.kr/www/selectBbsNttList.do?bbsNo=28&key=5923"
    assert (
        supported["송파구청"]
        == "https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=327&key=2323"
    )
    assert (
        supported["양천구청"]
        == "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397"
    )
    assert (
        supported["영등포구청"] == "https://www.ydp.go.kr/www/selectBbsNttList.do?bbsNo=31&key=2814"
    )
    assert (
        supported["용산구청"]
        == "https://www.yongsan.go.kr/portal/bbs/B0000030/list.do?menuNo=200140"
    )
    assert supported["종로구청"] == (
        "https://www.jongno.go.kr/portal/bbs/selectBoardList.do"
        "?bbsId=BBSMSTR_000000001167&menuId=110210&menuNo=110210"
    )
    assert supported["중구청"] == "https://www.junggu.seoul.kr/content.do?cmsid=15383&exclude=Y"
    assert (
        supported["중랑구청"]
        == "https://www.jungnang.go.kr/portal/bbs/list/B0000143.do?menuNo=200432"
    )


def test_seoul_office_attachment_boards_register_required_pagination_and_detail_flags() -> None:
    gangbuk = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강북구청")
    gwangjin = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "광진구청")
    dobong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "도봉구청")
    seongbuk = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "성북구청")
    junggu = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "중구청")
    jungnang = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "중랑구청")

    assert gangbuk.source_pattern["pageParam"] == "pageIndex"
    assert gwangjin.source_pattern["followDetail"] is True
    assert gwangjin.source_pattern["pageParam"] == "pageIndex"
    assert dobong.source_pattern["followDetail"] is True
    assert seongbuk.source_pattern["followDetail"] is True
    assert junggu.source_pattern["followDetail"] is True
    assert junggu.source_pattern["pageParam"] == "page2"
    assert jungnang.source_pattern["pageParam"] == "pageIndex"
    assert jungnang.source_pattern["pageUnitParam"] == "pageUnit"


def test_seoul_office_inline_tables_registered() -> None:
    seodaemun = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "서대문구청")
    eunpyeong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "은평구청")

    assert seodaemun.source_pattern["adapter"] == "inline_expense_table"
    assert (
        seodaemun.source_pattern["listUrl"] == "https://www.sdm.go.kr/admininfo/budget/openmoney.do"
    )
    assert seodaemun.source_pattern["pageParam"] == "cp"
    assert eunpyeong.source_pattern["adapter"] == "inline_expense_table"
    assert (
        eunpyeong.source_pattern["listUrl"]
        == "https://www.ep.go.kr/www/selectJobPrtnCtWebList.do?key=666"
    )
    assert eunpyeong.source_pattern["rowsPerPage"] == 100


def test_capital_area_agency_counts() -> None:
    assert len(GYEONGGI_AGENCIES) == 64
    assert len(INCHEON_AGENCIES) == 22
    assert len(CAPITAL_AREA_AGENCIES) == 138


def test_nationwide_agency_master_tracks_all_local_governments_without_jeju_admin_cities() -> None:
    assert len(NON_CAPITAL_AGENCIES) == 348
    assert len(LOCAL_GOVERNMENT_AGENCIES) == 486
    assert len(NATIONWIDE_AGENCIES) == 2200

    regional = [
        agency for agency in LOCAL_GOVERNMENT_AGENCIES if agency.gov_tier == GovTier.REGIONAL
    ]
    basic = [agency for agency in LOCAL_GOVERNMENT_AGENCIES if agency.gov_tier == GovTier.BASIC]
    assert len(regional) == 34
    assert len(basic) == 452
    assert sum(1 for agency in LOCAL_GOVERNMENT_AGENCIES if agency.branch == GovBranch.ADMIN) == 243
    assert (
        sum(1 for agency in LOCAL_GOVERNMENT_AGENCIES if agency.branch == GovBranch.COUNCIL)
        == 243
    )
    assert not any(
        agency.sub_region in {"제주시", "서귀포시"} for agency in LOCAL_GOVERNMENT_AGENCIES
    )
    assert all(agency.expansion_phase == ExpansionPhase.P1 for agency in LOCAL_GOVERNMENT_AGENCIES)


def test_public_sector_priority_groups_use_official_baseline_counts() -> None:
    assert len(CENTRAL_STATE_AGENCIES) == 60
    assert len(PUBLIC_INSTITUTION_AGENCIES) == 342
    assert len(LOCAL_PUBLIC_INSTITUTION_AGENCIES) == 1312

    phase_counts = Counter(agency.expansion_phase for agency in NATIONWIDE_AGENCIES)
    assert phase_counts == {
        ExpansionPhase.P1: 486,
        ExpansionPhase.P2: 60,
        ExpansionPhase.P3: 342,
        ExpansionPhase.P4: 1312,
    }

    central_counts = Counter(agency.jurisdiction_type for agency in CENTRAL_STATE_AGENCIES)
    assert central_counts[JurisdictionType.CENTRAL_ADMINISTRATIVE_AGENCY] == 49
    assert central_counts[JurisdictionType.CONSTITUTIONAL_INSTITUTION] == 4
    assert central_counts[JurisdictionType.INDEPENDENT_STATE_AGENCY] == 7
    assert all(
        agency.source_pattern["status"] == "adapter_required"
        and agency.source_pattern["baselineSourceUrl"].startswith("https://www.org.go.kr/")
        and "정부조직관리정보시스템" in agency.source_pattern["baselineEvidence"]
        for agency in CENTRAL_STATE_AGENCIES
    )

    public_counts = Counter(agency.sub_region for agency in PUBLIC_INSTITUTION_AGENCIES)
    assert sum(count for label, count in public_counts.items() if str(label).startswith("공기업")) == 30
    assert (
        sum(count for label, count in public_counts.items() if str(label).startswith("준정부기관"))
        == 58
    )
    assert public_counts["기타공공기관"] == 254
    verified_public_institutions = [
        agency
        for agency in PUBLIC_INSTITUTION_AGENCIES
        if agency.source_pattern.get("status") != "adapter_required"
    ]
    adapter_required_public_institutions = [
        agency
        for agency in PUBLIC_INSTITUTION_AGENCIES
        if agency.source_pattern.get("status") == "adapter_required"
    ]
    assert [agency.short_name for agency in verified_public_institutions] == ["게임물관리위원회"]
    assert len(adapter_required_public_institutions) == 341
    assert all(
        agency.source_pattern["status"] == "adapter_required"
        and agency.source_pattern["baselineSourceUrl"].startswith("https://job.alio.go.kr/")
        and "잡알리오" in agency.source_pattern["baselineEvidence"]
        for agency in adapter_required_public_institutions
    )

    assert all(
        agency.source_pattern["status"] == "adapter_required"
        and agency.source_pattern["baselineSourceUrl"].startswith("https://www.cleaneye.go.kr/")
        and "2026.3.31 기준" in agency.source_pattern["baselineEvidence"]
        for agency in LOCAL_PUBLIC_INSTITUTION_AGENCIES
    )


def test_non_capital_pending_entries_keep_korean_public_values_without_real_urls() -> None:
    pending_agencies = [
        agency
        for agency in NON_CAPITAL_AGENCIES
        if agency.source_pattern.get("status") == "adapter_required"
    ]

    assert len(pending_agencies) == len(NON_CAPITAL_AGENCIES) - 13
    assert all(agency.homepage is None for agency in pending_agencies)
    assert all("listUrl" not in agency.source_pattern for agency in pending_agencies)
    assert all(any("가" <= char <= "힣" for char in agency.name) for agency in pending_agencies)
    assert all(
        any("가" <= char <= "힣" for char in agency.source_pattern["searchKeyword"])
        for agency in pending_agencies
    )

    sejong = next(agency for agency in pending_agencies if agency.short_name == "세종시청")
    gangwon = next(agency for agency in pending_agencies if agency.short_name == "강원특별자치도청")
    assert sejong.jurisdiction_type == JurisdictionType.SPECIAL_SELF_GOVERNING_CITY
    assert gangwon.jurisdiction_type == JurisdictionType.SPECIAL_SELF_GOVERNING_PROVINCE
    assert gangwon.source_pattern["holdStatus"] == "legal_hold"
    assert gangwon.source_pattern["fileKinds"] == ["xlsx"]
    assert gangwon.source_pattern["pageParam"] == "pageIndex"
    assert "도지사·부지사 업무추진비 목록" in gangwon.source_pattern["blocker"]

    gangwon_council = next(
        agency for agency in pending_agencies if agency.short_name == "강원특별자치도의회"
    )
    assert gangwon_council.source_pattern["holdStatus"] == "legal_hold"
    assert gangwon_council.source_pattern["fileKinds"] == ["pdf", "xls", "xlsx"]
    assert gangwon_council.source_pattern["pageParam"] == "page"
    assert "PDF/XLS 다운로드 구조" in gangwon_council.source_pattern["blocker"]

    jeonbuk_city = next(
        agency for agency in pending_agencies if agency.short_name == "전북특별자치도청"
    )
    jeonbuk_council = next(
        agency for agency in pending_agencies if agency.short_name == "전북특별자치도의회"
    )
    assert jeonbuk_city.source_pattern["holdStatus"] == "legal_hold"
    assert jeonbuk_city.source_pattern["pageParam"] == "startPage"
    assert "공공누리 제4유형" in jeonbuk_city.source_pattern["blocker"]
    assert jeonbuk_council.source_pattern["holdStatus"] == "legal_hold"
    assert jeonbuk_council.source_pattern["fileKinds"] == ["xlsx", "pdf", "hwp"]
    assert "XLSX/PDF/HWP 다운로드 구조" in jeonbuk_council.source_pattern["blocker"]

    chungnam_city = next(
        agency for agency in pending_agencies if agency.short_name == "충청남도청"
    )
    chungnam_council = next(
        agency for agency in pending_agencies if agency.short_name == "충청남도의회"
    )
    assert chungnam_city.source_pattern["holdStatus"] == "legal_hold"
    assert chungnam_city.source_pattern["fileKinds"] == ["hwp", "pdf"]
    assert chungnam_city.source_pattern["pageParam"] == "pageIndex"
    assert "공공누리 제4유형" in chungnam_city.source_pattern["blocker"]
    assert chungnam_council.source_pattern["holdStatus"] == "legal_hold"
    assert chungnam_council.source_pattern["fileKinds"] == ["pdf", "hwp", "xls", "xlsx"]
    assert chungnam_council.source_pattern["pageParam"] == "page"
    assert "PDF/HWP/XLS/XLSX 다운로드 구조" in chungnam_council.source_pattern["blocker"]

    cheonan_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "천안시청"
    )
    cheonan_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "천안시의회"
    )
    gongju_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "공주시청"
    )
    gongju_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "공주시의회"
    )
    seosan_city = next(
        agency
        for agency in NON_CAPITAL_AGENCIES
        if agency.parent_region == "충청남도" and agency.short_name == "서산시청"
    )
    boryeong_city = next(
        agency
        for agency in NON_CAPITAL_AGENCIES
        if agency.parent_region == "충청남도" and agency.short_name == "보령시청"
    )
    nonsan_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "논산시청"
    )
    nonsan_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "논산시의회"
    )
    buyeo_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "부여군청"
    )
    buyeo_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "충청남도" and agency.short_name == "부여군의회"
    )
    assert cheonan_city.source_pattern["holdStatus"] == "legal_hold"
    assert cheonan_city.source_pattern["sourceUrl"] == (
        "https://www.cheonan.go.kr/bbs/BBSMSTR_000000000050/list.do"
    )
    assert cheonan_city.source_pattern["fileKinds"] == ["xlsx", "xls", "pdf", "hwp", "hwpx", "zip"]
    assert cheonan_city.source_pattern["pageParam"] == "pageIndex"
    assert cheonan_council.source_pattern["holdStatus"] == "legal_hold"
    assert cheonan_council.source_pattern["fileKinds"] == ["xlsx"]
    assert cheonan_council.source_pattern["pageParam"] == "schPageNo"
    assert gongju_city.source_pattern["holdStatus"] == "legal_hold"
    assert gongju_city.source_pattern["fileKinds"] == ["xlsx", "xls", "hwp"]
    assert gongju_city.source_pattern["pageParam"] == "pageIndex"
    assert gongju_council.source_pattern["holdStatus"] == "legal_hold"
    assert gongju_council.source_pattern["sourceUrl"] == (
        "https://council.gongju.go.kr/bbs/BBSMSTR_000000000882/list.do"
    )
    assert "PDF 다운로드 구조" in gongju_council.source_pattern["blocker"]
    assert seosan_city.homepage == "https://www.seosan.go.kr"
    assert seosan_city.source_pattern["adapter"] == "attachment_board"
    assert seosan_city.source_pattern["listUrl"] == (
        "https://www.seosan.go.kr/www/selectBbsNttList.do?bbsNo=114&key=1278"
    )
    assert seosan_city.source_pattern["fileKinds"] == ["hwp", "xlsx", "xls"]
    assert seosan_city.source_pattern["pageParam"] == "pageIndex"
    assert seosan_city.source_pattern["verifiedBy"] == "공식 사이트 원격 확인"
    assert boryeong_city.homepage == "https://www.brcn.go.kr"
    assert boryeong_city.source_pattern["adapter"] == "attachment_board"
    assert boryeong_city.source_pattern["listUrl"] == (
        "https://www.brcn.go.kr/cop/bbs/BBSMSTR_000000000386/selectBoardList.do?"
        "bbsId=BBSMSTR_000000000386"
    )
    assert boryeong_city.source_pattern["fileKinds"] == ["xls", "xlsx", "pdf"]
    assert boryeong_city.source_pattern["pageParam"] == "pageIndex"
    assert boryeong_city.source_pattern["verifiedBy"] == "공식 사이트 원격 확인"
    assert nonsan_city.source_pattern["holdStatus"] == "legal_hold"
    assert nonsan_city.source_pattern["sourceUrl"] == (
        "https://www.nonsan.go.kr/kor/html/sub03/03080803.html?GotoPage=1&mode=L"
    )
    assert "저작권정책 링크" in nonsan_city.source_pattern["blocker"]
    assert nonsan_council.source_pattern["holdStatus"] == "legal_hold"
    assert nonsan_council.source_pattern["sourceUrl"] == (
        "https://www.nonsancl.go.kr/kr/activity/bbs?bbs_id=expense"
    )
    assert nonsan_council.source_pattern["fileKinds"] == ["xlsx"]
    assert buyeo_city.source_pattern["holdStatus"] == "legal_hold"
    assert buyeo_city.source_pattern["sourceUrl"] == (
        "https://www.buyeo.go.kr/_prog/_board/?code=service_010211&site_dvs_cd=kr&menu_dvs_cd=010211"
    )
    assert buyeo_city.source_pattern["fileKinds"] == ["hwp"]
    assert buyeo_city.source_pattern["pageParam"] == "GotoPage"
    assert "저작권정책 링크" in buyeo_city.source_pattern["blocker"]
    assert buyeo_council.source_pattern["holdStatus"] == "legal_hold"
    assert buyeo_council.source_pattern["sourceUrl"] == (
        "https://council.buyeo.go.kr/kr/open/bbsBusiness.do"
    )
    assert buyeo_council.source_pattern["fileKinds"] == ["pdf", "zip"]
    assert buyeo_council.source_pattern["pageParam"] == "pageNum"
    assert "목록 ZIP 다운로드" in buyeo_council.source_pattern["blocker"]

    busan_council = next(agency for agency in pending_agencies if agency.short_name == "부산시의회")
    assert busan_council.source_pattern["holdStatus"] == "legal_hold"
    assert "공공누리 유형 표시" in busan_council.source_pattern["blocker"]

    gwangju_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "광주광역시" and agency.short_name == "광주시청"
    )
    gwangju_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "광주광역시" and agency.short_name == "광주시의회"
    )
    assert gwangju_city.source_pattern["holdStatus"] == "legal_hold"
    assert gwangju_city.source_pattern["sourceUrl"] == (
        "https://www.gwangju.go.kr/boardList.do?boardId=BD_0000000252&pageId=www101"
    )
    assert gwangju_city.source_pattern["pageParam"] == "movePage"
    assert gwangju_city.source_pattern["fileKinds"] == ["xls"]
    assert "자유이용 불가" in gwangju_city.source_pattern["blocker"]
    assert gwangju_council.source_pattern["holdStatus"] == "legal_hold"
    assert gwangju_council.source_pattern["sourceUrl"] == (
        "https://council.gwangju.go.kr/index.do?PID=168"
    )
    assert gwangju_council.source_pattern["pageParam"] == "pageNo"
    assert "제1유형 확인 전까지 수집하지 않습니다" in gwangju_council.source_pattern["blocker"]

    chungbuk_city = next(
        agency for agency in pending_agencies if agency.short_name == "충청북도청"
    )
    chungbuk_council = next(
        agency for agency in pending_agencies if agency.short_name == "충청북도의회"
    )
    assert chungbuk_city.source_pattern["holdStatus"] == "legal_hold"
    assert chungbuk_city.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert chungbuk_city.source_pattern["pageParam"] == "pageIndex"
    assert "XLSX 다운로드 구조" in chungbuk_city.source_pattern["blocker"]
    assert chungbuk_council.source_pattern["holdStatus"] == "legal_hold"
    assert chungbuk_council.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert chungbuk_council.source_pattern["pageParam"] == "page"
    assert "XLS/XLSX 다운로드 구조" in chungbuk_council.source_pattern["blocker"]

    gyeongbuk_city = next(
        agency for agency in pending_agencies if agency.short_name == "경상북도청"
    )
    gyeongbuk_council = next(
        agency for agency in pending_agencies if agency.short_name == "경상북도의회"
    )
    assert gyeongbuk_city.source_pattern["holdStatus"] == "legal_hold"
    assert gyeongbuk_city.source_pattern["fileKinds"] == ["xlsx", "xls", "pdf"]
    assert gyeongbuk_city.source_pattern["pageParam"] == "Start"
    assert "공공누리 제3유형" in gyeongbuk_city.source_pattern["blocker"]
    assert gyeongbuk_council.source_pattern["holdStatus"] == "legal_hold"
    assert gyeongbuk_council.source_pattern["fileKinds"] == ["xlsx"]
    assert gyeongbuk_council.source_pattern["pageParam"] == "page"
    assert "XLSX 다운로드 구조" in gyeongbuk_council.source_pattern["blocker"]

    gyeongnam_city = next(
        agency for agency in pending_agencies if agency.short_name == "경상남도청"
    )
    gyeongnam_council = next(
        agency for agency in pending_agencies if agency.short_name == "경상남도의회"
    )
    assert gyeongnam_city.source_pattern["holdStatus"] == "legal_hold"
    assert gyeongnam_city.source_pattern["fileKinds"] == ["xlsx"]
    assert gyeongnam_city.source_pattern["pageParam"] == "pageNo"
    assert "자유이용을 불가" in gyeongnam_city.source_pattern["blocker"]
    assert gyeongnam_council.source_pattern["holdStatus"] == "legal_hold"
    assert gyeongnam_council.source_pattern["fileKinds"] == ["pdf"]
    assert gyeongnam_council.source_pattern["pageParam"] == "pageNum"
    assert "PDF 다운로드 구조" in gyeongnam_council.source_pattern["blocker"]

    ulsan_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "울산광역시" and agency.short_name == "울산시청"
    )
    ulsan_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "울산광역시" and agency.short_name == "울산시의회"
    )
    ulsan_namgu = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "울산광역시" and agency.short_name == "남구청"
    )
    ulju_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "울산광역시" and agency.short_name == "울주군의회"
    )
    assert ulsan_city.source_pattern["holdStatus"] == "legal_hold"
    assert ulsan_city.source_pattern["fileKinds"] == ["html"]
    assert ulsan_city.source_pattern["pageParam"] == "curPage"
    assert "HTML 상세 표 구조" in ulsan_city.source_pattern["blocker"]
    assert ulsan_council.source_pattern["holdStatus"] == "legal_hold"
    assert ulsan_council.source_pattern["fileKinds"] == ["xlsx"]
    assert ulsan_namgu.source_pattern["holdStatus"] == "legal_hold"
    assert ulsan_namgu.source_pattern["fileKinds"] == ["pdf"]
    assert "구청장·부구청장·국장·부서장·동장·보건소" in ulsan_namgu.source_pattern["blocker"]
    assert ulju_council.source_pattern["holdStatus"] == "legal_hold"
    assert ulju_council.source_pattern["sourceUrl"] == (
        "https://assembly.ulju.ulsan.kr/kr/bbs?bbs_id=business"
    )

    mokpo_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "목포시청"
    )
    mokpo_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "목포시의회"
    )
    naju_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "나주시청"
    )
    gurye_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "구례군청"
    )
    gurye_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "구례군의회"
    )
    goheung_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "고흥군청"
    )
    goheung_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "고흥군의회"
    )
    yeosu_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "여수시청"
    )
    gwangyang_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "광양시청"
    )
    suncheon_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전라남도" and agency.short_name == "순천시청"
    )
    assert mokpo_city.source_pattern["holdStatus"] == "legal_hold"
    assert mokpo_city.source_pattern["sourceUrl"] == (
        "https://www.mokpo.go.kr/www/open_data/open_operational_cost"
    )
    assert mokpo_city.source_pattern["fileKinds"] == ["pdf"]
    assert "공공누리 유형 표시가 비어" in mokpo_city.source_pattern["blocker"]
    assert mokpo_council.source_pattern["holdStatus"] == "legal_hold"
    assert mokpo_council.source_pattern["sourceUrl"] == (
        "https://council.mokpo.go.kr/kr/bbs?bbs_id=expenses"
    )
    assert "명확한 자유이용 표시" in mokpo_council.source_pattern["blocker"]
    assert naju_city.source_pattern["holdStatus"] == "legal_hold"
    assert naju_city.source_pattern["sourceUrl"] == "https://naju.go.kr/www/open_data/budget/expense"
    assert naju_city.source_pattern["fileKinds"] == ["html"]
    assert "본문이 0바이트" in naju_city.source_pattern["blocker"]
    assert gurye_city.source_pattern["holdStatus"] == "legal_hold"
    assert gurye_city.source_pattern["fileKinds"] == ["xlsx"]
    assert gurye_city.source_pattern["pageParam"] == "pageIndex"
    assert "공공누리 제4유형" in gurye_city.source_pattern["blocker"]
    assert gurye_council.source_pattern["holdStatus"] == "legal_hold"
    assert gurye_council.source_pattern["fileKinds"] == ["xlsx"]
    assert "전체 ZIP 다운로드 구조" in gurye_council.source_pattern["blocker"]
    assert goheung_city.source_pattern["holdStatus"] == "legal_hold"
    assert goheung_city.source_pattern["sourceUrl"] == (
        "https://www.goheung.go.kr/boardList.do?boardId=BD_00107&pageId=www497"
    )
    assert goheung_city.source_pattern["pageParam"] == "movePage"
    assert "사전정보공개 업무추진비 공개 목록" in goheung_city.source_pattern["blocker"]
    assert goheung_council.source_pattern["holdStatus"] == "legal_hold"
    assert goheung_council.source_pattern["sourceUrl"] == (
        "https://council.goheung.go.kr/main/board/45/1/category7"
    )
    assert goheung_council.source_pattern["pageParam"] == "path"
    assert "경로형 페이지네이션" in goheung_council.source_pattern["blocker"]
    assert yeosu_city.source_pattern["holdStatus"] == "legal_hold"
    assert yeosu_city.source_pattern["sourceUrl"] == (
        "https://www.yeosu.go.kr/www/pubinfo/announce/operating_expense"
    )
    assert yeosu_city.source_pattern["fileKinds"] == ["pdf", "zip"]
    assert "공공누리 제4유형" in yeosu_city.source_pattern["blocker"]
    assert gwangyang_city.source_pattern["holdStatus"] == "legal_hold"
    assert gwangyang_city.source_pattern["sourceUrl"] == (
        "https://gwangyang.go.kr/mayor/menu.es?mid=a20106014600"
    )
    assert gwangyang_city.source_pattern["fileKinds"] == ["html"]
    assert gwangyang_city.source_pattern["pageParam"] == "role_and_quarter"
    assert "역할별 분기 선택 목록과 HTML 표 구조" in gwangyang_city.source_pattern["blocker"]
    assert suncheon_city.source_pattern["holdStatus"] == "legal_hold"
    assert suncheon_city.source_pattern["fileKinds"] == ["pdf", "hwpx"]
    assert suncheon_city.source_pattern["pageParam"] == "pageIdx"
    assert "출처표시-비상업적-변경금지" in suncheon_city.source_pattern["blocker"]

    jeonju_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전북특별자치도" and agency.short_name == "전주시청"
    )
    gunsan_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전북특별자치도" and agency.short_name == "군산시의회"
    )
    assert jeonju_city.source_pattern["holdStatus"] == "legal_hold"
    assert jeonju_city.source_pattern["fileKinds"] == ["hwpx", "pdf", "xlsx", "xls"]
    assert "공공누리 제4유형" in jeonju_city.source_pattern["blocker"]
    assert gunsan_council.source_pattern["holdStatus"] == "legal_hold"
    assert gunsan_council.source_pattern["pageParam"] == "pageNum"
    assert "PDF/XLS/XLSX 다운로드 구조" in gunsan_council.source_pattern["blocker"]
    jeonju_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전북특별자치도" and agency.short_name == "전주시의회"
    )
    gunsan_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전북특별자치도" and agency.short_name == "군산시청"
    )
    jinan_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "전북특별자치도" and agency.short_name == "진안군의회"
    )
    assert jeonju_council.source_pattern["holdStatus"] == "legal_hold"
    assert "ALL RIGHTS RESERVED" in jeonju_council.source_pattern["blocker"]
    assert gunsan_city.source_pattern["holdStatus"] == "legal_hold"
    assert "공공누리 제4유형" in gunsan_city.source_pattern["blocker"]
    assert jinan_council.source_pattern["holdStatus"] == "legal_hold"
    assert "All rights reserved" in jinan_council.source_pattern["blocker"]

    geumjeong_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "부산광역시" and agency.short_name == "금정구청"
    )
    assert geumjeong_city.source_pattern["holdStatus"] == "legal_hold"
    assert geumjeong_city.source_pattern["fileKinds"] == ["hwpx", "xlsx"]
    assert geumjeong_city.source_pattern["pageParam"] == "startPage"
    assert "공공누리 제4유형" in geumjeong_city.source_pattern["blocker"]
    busan_seogu = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "부산광역시" and agency.short_name == "서구청"
    )
    busan_namgu = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "부산광역시" and agency.short_name == "남구청"
    )
    busan_junggu = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "부산광역시" and agency.short_name == "중구청"
    )
    assert busan_seogu.source_pattern["holdStatus"] == "adapter_hold"
    assert busan_seogu.source_pattern["fileKinds"] == ["hwp"]
    assert "HWP extractor" in busan_seogu.source_pattern["blocker"]
    assert busan_namgu.source_pattern["holdStatus"] == "legal_hold"
    assert "국장급 이상 업무추진비" in busan_namgu.source_pattern["blocker"]
    assert busan_junggu.source_pattern["holdStatus"] == "source_not_found"
    assert "searchedPaths" in busan_junggu.source_pattern

    pohang_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상북도" and agency.short_name == "포항시청"
    )
    pohang_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상북도" and agency.short_name == "포항시의회"
    )
    assert pohang_city.source_pattern["holdStatus"] == "legal_hold"
    assert pohang_city.source_pattern["fileKinds"] == ["xlsx", "xls", "pdf"]
    assert "XLSX 다운로드 구조" in pohang_city.source_pattern["blocker"]
    assert pohang_council.source_pattern["holdStatus"] == "legal_hold"
    assert pohang_council.source_pattern["fileKinds"] == ["pdf"]
    assert "PDF 다운로드 구조" in pohang_council.source_pattern["blocker"]
    mungyeong_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상북도" and agency.short_name == "문경시청"
    )
    assert mungyeong_city.source_pattern["holdStatus"] == "legal_hold"
    assert "공공누리 제4유형" in mungyeong_city.source_pattern["blocker"]

    jinju_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상남도" and agency.short_name == "진주시청"
    )
    assert jinju_city.source_pattern["holdStatus"] == "legal_hold"
    assert jinju_city.source_pattern["fileKinds"] == ["xlsx"]
    assert jinju_city.source_pattern["extraListUrls"] == ["https://www.jinju.go.kr/05637.web"]
    assert "게시물별 라이선스 필터" in jinju_city.source_pattern["blocker"]

    changwon_city = next(
        agency
        for agency in NON_CAPITAL_AGENCIES
        if agency.parent_region == "경상남도" and agency.short_name == "창원시청"
    )
    changwon_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상남도" and agency.short_name == "창원시의회"
    )
    assert changwon_city.homepage == "https://www.changwon.go.kr"
    assert changwon_city.source_pattern["adapter"] == "attachment_board"
    assert changwon_city.source_pattern["listUrl"] == (
        "https://www.changwon.go.kr/cwportal/10312/10620/10629.web?gcode=1036"
    )
    assert changwon_city.source_pattern["fileKinds"] == ["xlsx", "pdf"]
    assert changwon_city.source_pattern["pageParam"] == "cpage"
    assert changwon_council.source_pattern["holdStatus"] == "legal_hold"
    assert changwon_council.source_pattern["fileKinds"] == ["pdf"]
    assert changwon_council.source_pattern["pageParam"] == "pageNo"
    assert "PDF 다운로드 구조" in changwon_council.source_pattern["blocker"]
    gimhae_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상남도" and agency.short_name == "김해시청"
    )
    geochang_city = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상남도" and agency.short_name == "거창군청"
    )
    hadong_council = next(
        agency
        for agency in pending_agencies
        if agency.parent_region == "경상남도" and agency.short_name == "하동군의회"
    )
    assert gimhae_city.source_pattern["holdStatus"] == "legal_hold"
    assert "All Rights Reserved" in gimhae_city.source_pattern["blocker"]
    assert geochang_city.source_pattern["holdStatus"] == "legal_hold"
    assert geochang_city.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert hadong_council.source_pattern["holdStatus"] == "source_not_found"

    daegu_city = next(agency for agency in pending_agencies if agency.short_name == "대구시청")
    daegu_council = next(agency for agency in pending_agencies if agency.short_name == "대구시의회")
    assert daegu_city.source_pattern["holdStatus"] == "legal_hold"
    assert daegu_council.source_pattern["holdStatus"] == "legal_hold"
    assert "제1유형 확인 전까지 수집하지 않습니다" in daegu_city.source_pattern["blocker"]

    verified_non_capital = [
        agency
        for agency in NON_CAPITAL_AGENCIES
        if agency.source_pattern.get("status") != "adapter_required"
    ]
    assert {agency.short_name for agency in verified_non_capital} == {
        "대전시청",
        "대전시의회",
        "보령시청",
        "서산시청",
        "구미시청",
        "밀양시청",
        "창원시청",
        "영월군청",
        "곡성군청",
        "곡성군의회",
        "진도군청",
        "제주특별자치도청",
        "제주특별자치도의회",
    }
    daejeon_city = next(agency for agency in verified_non_capital if agency.short_name == "대전시청")
    daejeon_council = next(agency for agency in verified_non_capital if agency.short_name == "대전시의회")
    gumi_city = next(agency for agency in verified_non_capital if agency.short_name == "구미시청")
    miryang_city = next(agency for agency in verified_non_capital if agency.short_name == "밀양시청")
    jeonnam_city = next(agency for agency in pending_agencies if agency.short_name == "전라남도청")
    jeju_city = next(agency for agency in verified_non_capital if agency.short_name == "제주특별자치도청")
    jeju_council = next(
        agency for agency in verified_non_capital if agency.short_name == "제주특별자치도의회"
    )
    gokseong_city = next(agency for agency in verified_non_capital if agency.short_name == "곡성군청")
    gokseong_council = next(
        agency for agency in verified_non_capital if agency.short_name == "곡성군의회"
    )
    jindo_city = next(agency for agency in verified_non_capital if agency.short_name == "진도군청")
    jeonnam_council = next(agency for agency in pending_agencies if agency.short_name == "전라남도의회")
    assert daejeon_city.homepage == "https://www.daejeon.go.kr"
    assert daejeon_city.source_pattern["adapter"] == "attachment_board"
    assert daejeon_city.source_pattern["pageParam"] == "subPageIndex"
    assert daejeon_city.source_pattern["fileKinds"] == ["xlsx"]
    assert daejeon_council.homepage == "https://council.daejeon.go.kr"
    assert daejeon_council.source_pattern["adapter"] == "council_attachment_board"
    assert daejeon_council.source_pattern["pageParam"] == "pageNo"
    assert gumi_city.homepage == "https://www.gumi.go.kr"
    assert gumi_city.source_pattern["adapter"] == "attachment_board"
    assert gumi_city.source_pattern["listUrl"] == (
        "https://www.gumi.go.kr/portal/board/post/list.do?"
        "bcIdx=164&mid=0303100000"
    )
    assert gumi_city.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert gumi_city.source_pattern["pageParam"] == "page"
    assert miryang_city.homepage == "https://www.miryang.go.kr"
    assert miryang_city.source_pattern["adapter"] == "attachment_board"
    assert miryang_city.source_pattern["listUrl"] == (
        "https://www.miryang.go.kr/twn/bbs/selectBoardList.do?"
        "bbsId=BBSMSTR_000000085910&mnNo=3040000&owd=sammun"
    )
    assert miryang_city.source_pattern["fileKinds"] == ["xlsx"]
    assert miryang_city.source_pattern["pageParam"] == "pageIndex"
    assert miryang_city.source_pattern["userAgent"].startswith("Mozilla/5.0 (Macintosh")
    assert jeonnam_city.homepage is None
    assert jeonnam_city.source_pattern["adapter"] == "nationwide_office_required"
    assert jeonnam_city.source_pattern["holdStatus"] == "adapter_hold"
    assert jeonnam_city.source_pattern["sourceUrl"] == (
        "https://www.jeonnam.go.kr/M1925005/boardList.do?menuId=jeonnam0302050100"
    )
    assert jeonnam_city.source_pattern["fileKinds"] == ["hwp"]
    assert jeonnam_city.source_pattern["pageParam"] == "pageIndex"
    assert "HWP 본문 추출" in jeonnam_city.source_pattern["blocker"]
    assert jeju_city.homepage == "https://www.jeju.go.kr"
    assert jeju_city.source_pattern["adapter"] == "attachment_board"
    assert jeju_city.source_pattern["listUrl"] == (
        "https://www.jeju.go.kr/open/open/work/work2.htm?category=1409"
    )
    assert jeju_city.source_pattern["extraListUrls"] == [
        "https://www.jeju.go.kr/open/open/work/work1.htm?category=1003"
    ]
    assert jeju_city.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert "도 본청 업무추진비" in jeju_city.source_pattern["evidenceNote"]
    assert jeju_council.homepage == "https://www.council.jeju.kr"
    assert jeju_council.source_pattern["adapter"] == "council_attachment_board"
    assert jeju_council.source_pattern["listUrl"] == (
        "https://www.council.jeju.kr/clicknews/openpromotion.do"
    )
    assert jeju_council.source_pattern["extraListUrls"] == [
        "https://www.council.jeju.kr/notice/informationdisclosure/operations/expenses.do"
    ]
    assert jeju_council.source_pattern["fileKinds"] == ["xlsx", "xls"]
    assert "의회운영업무추진비" in jeju_council.source_pattern["evidenceNote"]
    assert gokseong_city.homepage == "https://www.gokseong.go.kr"
    assert gokseong_city.source_pattern["adapter"] == "attachment_board"
    assert gokseong_city.source_pattern["listUrl"] == (
        "https://www.gokseong.go.kr/kr/board/list.do?"
        "bbsId=BBS_000000000000540&menuNo=102006001000"
    )
    assert len(gokseong_city.source_pattern["extraListUrls"]) == 2
    assert gokseong_city.source_pattern["fileKinds"] == ["pdf", "xlsx"]
    assert gokseong_city.source_pattern["pageParam"] == "pageIndex"
    assert gokseong_council.homepage == "https://www.gokseong.go.kr"
    assert gokseong_council.source_pattern["adapter"] == "council_attachment_board"
    assert gokseong_council.source_pattern["listUrl"] == (
        "https://www.gokseong.go.kr/council/board/list.do?"
        "bbsId=BBS_000000000000380&menuNo=106005004000"
    )
    assert gokseong_council.source_pattern["fileKinds"] == ["pdf"]
    assert jindo_city.homepage == "https://www.jindo.go.kr"
    assert jindo_city.source_pattern["adapter"] == "attachment_board"
    assert jindo_city.source_pattern["listUrl"] == "https://www.jindo.go.kr/home/board/B0071.cs?m=52"
    assert jindo_city.source_pattern["fileKinds"] == ["pdf"]
    assert jindo_city.source_pattern["pageParam"] == "pageIndex"
    assert jindo_city.source_pattern["userAgent"].startswith("Mozilla/5.0")
    assert jindo_city.source_pattern["verifiedBy"] == "공식 사이트 원격 확인"
    assert jeonnam_council.source_pattern["holdStatus"] == "legal_hold"
    assert jeonnam_council.source_pattern["sourceUrl"] == (
        "https://www.jnassembly.go.kr/jnassem/board/412"
    )
    assert jeonnam_council.source_pattern["extraListUrls"] == [
        "https://www.jnassembly.go.kr/jnassem/board/51/1/category8"
    ]
    assert jeonnam_council.source_pattern["fileKinds"] == ["pdf"]
    assert jeonnam_council.source_pattern["pageParam"] == "path"
    assert "제1유형 확인 전까지 수집하지 않습니다" in jeonnam_council.source_pattern["blocker"]

    sejong_city = next(agency for agency in pending_agencies if agency.short_name == "세종시청")
    sejong_council = next(agency for agency in pending_agencies if agency.short_name == "세종시의회")
    assert sejong_city.source_pattern["holdStatus"] == "legal_hold"
    assert sejong_city.source_pattern["sourceUrl"] == "https://www.sejong.go.kr/bbs/R0091/list.do"
    assert sejong_city.source_pattern["fileKinds"] == ["xlsx"]
    assert sejong_city.source_pattern["pageParam"] == "pageIndex"
    assert "공공누리 제4유형" in sejong_city.source_pattern["blocker"]
    assert sejong_council.source_pattern["holdStatus"] == "legal_hold"
    assert "공공누리 유형 표시" in sejong_council.source_pattern["blocker"]

    daejeon_basic_holds = [
        agency
        for agency in pending_agencies
        if agency.parent_region == "대전광역시"
        and agency.source_pattern.get("holdStatus") == "legal_hold"
    ]
    assert {agency.short_name for agency in daejeon_basic_holds} == {
        "동구청",
        "동구의회",
        "중구청",
        "중구의회",
        "서구청",
        "유성구청",
        "유성구의회",
        "대덕구청",
        "대덕구의회",
    }
    daedeok_council = next(
        agency for agency in daejeon_basic_holds if agency.short_name == "대덕구의회"
    )
    assert daedeok_council.source_pattern["sourceUrl"] == (
        "https://council.daedeok.go.kr/kr/costBBS.do"
    )
    assert daedeok_council.source_pattern["pageParam"] == "page"
    assert "제1유형 확인 전까지 수집하지 않습니다" in daedeok_council.source_pattern["blocker"]


def test_capital_area_adapter_required_agencies_have_no_homepages_or_real_urls() -> None:
    pending_agencies = [
        agency
        for agency in GYEONGGI_AGENCIES + INCHEON_AGENCIES
        if agency.source_pattern.get("status") == "adapter_required"
    ]
    assert len(pending_agencies) == 7
    for agency in pending_agencies:
        assert agency.source_pattern.get("status") == "adapter_required"
        assert "listUrl" not in agency.source_pattern
        assert "source_url" not in agency.source_pattern
        assert agency.homepage is None

    incheon_council = next(agency for agency in INCHEON_AGENCIES if agency.short_name == "인천시의회")
    assert incheon_council.homepage == "https://www.icouncil.go.kr"
    assert incheon_council.source_pattern["listUrl"] == (
        "https://www.icouncil.go.kr/main/participate/expense_office.jsp"
    )
    assert incheon_council.source_pattern["extraListUrls"] == [
        "https://www.icouncil.go.kr/main/participate/expense.jsp"
    ]

    suwon_council = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "수원시의회")
    assert suwon_council.homepage == "https://council.suwon.go.kr"
    assert suwon_council.source_pattern["listUrl"] == (
        "https://council.suwon.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert suwon_council.source_pattern["fileKinds"] == ["xls", "xlsx", "pdf"]

    gyeonggi_council = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "경기도의회")
    assert gyeonggi_council.homepage == "https://www.ggc.go.kr"
    assert gyeonggi_council.source_pattern["listUrl"] == (
        "https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list"
    )
    assert gyeonggi_council.source_pattern["fileKinds"] == ["xlsx", "xls", "pdf"]

    verified_offices = {
        agency.short_name: agency
        for agency in GYEONGGI_AGENCIES
        if agency.short_name
        in {
            "수원시청",
            "성남시청",
            "평택시청",
            "안양시청",
            "의정부시청",
            "동두천시청",
            "안산시청",
            "부천시청",
            "고양시청",
            "과천시청",
            "김포시청",
            "하남시청",
            "광명시청",
            "구리시청",
            "남양주시청",
            "오산시청",
            "군포시청",
            "의왕시청",
            "용인시청",
            "파주시청",
            "양주시청",
            "포천시청",
            "연천군청",
            "양평군청",
            "안성시청",
            "광주시청",
            "가평군청",
        }
    }
    assert verified_offices["수원시청"].source_pattern["listUrl"] == (
        "https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179"
    )
    assert verified_offices["성남시청"].source_pattern["listUrl"] == (
        "https://www.seongnam.go.kr/city/1000199/30218/bbsList.do"
    )
    assert verified_offices["성남시청"].source_pattern["fileKinds"] == [
        "hwpx",
        "xlsx",
        "xls",
        "pdf",
    ]
    assert verified_offices["평택시청"].source_pattern["listUrl"] == (
        "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000"
    )
    assert verified_offices["안양시청"].source_pattern["listUrl"] == (
        "https://www.anyang.go.kr/main/selectBbsNttList.do?bbsNo=43&key=218"
    )
    assert verified_offices["의정부시청"].source_pattern["listUrl"] == (
        "https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25"
    )
    assert verified_offices["의정부시청"].source_pattern["extraListUrls"] == [
        "https://www.ui4u.go.kr/portal/contents.do?mId=0114010000",
        "https://www.ui4u.go.kr/portal/contents.do?mId=0114010100",
        "https://www.ui4u.go.kr/portal/contents.do?mId=0114010200",
        "https://www.ui4u.go.kr/portal/contents.do?mId=0114010400",
    ]
    assert verified_offices["동두천시청"].source_pattern["listUrl"] == (
        "https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122"
    )
    assert verified_offices["안산시청"].source_pattern["listUrl"] == (
        "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471"
    )
    assert verified_offices["부천시청"].source_pattern["listUrl"] == (
        "https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002"
    )
    assert verified_offices["고양시청"].source_pattern["listUrl"] == (
        "https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84"
    )
    assert verified_offices["김포시청"].source_pattern["listUrl"] == (
        "https://www.gimpo.go.kr/portal/selectBbsNttList.do?bbsNo=199&key=1110"
    )
    assert verified_offices["하남시청"].source_pattern["listUrl"] == (
        "https://www.hanam.go.kr/www/selectBbsNttList.do?bbsNo=15&key=51"
    )
    assert verified_offices["광명시청"].source_pattern["listUrl"] == (
        "https://www.gm.go.kr/pt/user/bbs/BD_selectBbsList.do?q_bbsCode=2472"
    )
    assert verified_offices["구리시청"].source_pattern["listUrl"] == (
        "https://www.guri.go.kr/www/selectBbsNttList.do?bbsNo=14&key=331"
    )
    assert verified_offices["남양주시청"].source_pattern["listUrl"] == (
        "https://www.nyj.go.kr/www/selectBbsNttList.do?key=2432&bbsNo=43"
    )
    assert verified_offices["오산시청"].source_pattern["listUrl"] == (
        "https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000"
    )
    assert verified_offices["군포시청"].source_pattern["listUrl"] == (
        "https://www.gunpo.go.kr/www/selectBbsNttList.do?bbsNo=715&key=4276"
    )
    assert verified_offices["의왕시청"].source_pattern["listUrl"] == "https://www.uiwang.go.kr/UWKOROPEN0210"
    assert verified_offices["용인시청"].source_pattern["listUrl"] == (
        "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6"
    )
    assert verified_offices["파주시청"].source_pattern["listUrl"] == (
        "https://www.paju.go.kr/user/policy_02/board/BD_board.list.do?bbsCd=1018"
    )
    assert verified_offices["양주시청"].source_pattern["listUrl"] == (
        "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=30&key=234"
    )
    assert verified_offices["포천시청"].source_pattern["listUrl"] == (
        "https://www.pocheon.go.kr/www/selectBbsNttList.do?bbsNo=214&key=3687"
    )
    assert verified_offices["연천군청"].source_pattern["listUrl"] == (
        "https://www.yeoncheon.go.kr/www/selectBbsNttList.do?bbsNo=152&key=3352"
    )
    assert verified_offices["양평군청"].source_pattern["listUrl"] == (
        "https://www.yp21.go.kr/www/selectBbsNttList.do?bbsNo=43&key=1597"
    )
    assert verified_offices["안성시청"].source_pattern["listUrl"] == (
        "https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000"
    )
    assert verified_offices["과천시청"].source_pattern["listUrl"] == (
        "https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000"
    )
    assert verified_offices["광주시청"].source_pattern["listUrl"] == (
        "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53"
    )
    assert verified_offices["가평군청"].source_pattern["listUrl"] == (
        "https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454"
    )

    verified_councils = {
        agency.short_name: agency
        for agency in GYEONGGI_AGENCIES
        if agency.short_name
        in {
            "경기도의회",
            "성남시의회",
            "평택시의회",
            "의정부시의회",
            "동두천시의회",
            "광명시의회",
            "고양시의회",
            "구리시의회",
            "남양주시의회",
            "용인시의회",
            "부천시의회",
            "안양시의회",
            "군포시의회",
            "의왕시의회",
            "과천시의회",
            "오산시의회",
            "시흥시의회",
            "하남시의회",
            "파주시의회",
            "광주시의회",
            "양주시의회",
            "이천시의회",
            "안성시의회",
            "김포시의회",
            "화성시의회",
            "포천시의회",
            "여주시의회",
            "연천군의회",
            "가평군의회",
            "양평군의회",
        }
    }
    assert verified_councils["경기도의회"].source_pattern["listUrl"] == (
        "https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list"
    )
    assert verified_councils["성남시의회"].source_pattern["listUrl"] == (
        "https://www.sncouncil.go.kr/kr/news/bbsCost.do"
    )
    assert verified_councils["평택시의회"].source_pattern["listUrl"] == (
        "https://www.ptcouncil.go.kr/coun/cost/reportList.do"
    )
    assert verified_councils["의정부시의회"].source_pattern["listUrl"] == (
        "https://www.ujbcl.go.kr/svc/bbs/BusinessList.do?bbsMnuCd=MNU002300000650400000666"
    )
    assert verified_councils["동두천시의회"].source_pattern["listUrl"] == (
        "https://council.ddc.go.kr/kr/news/bbsCost.do"
    )
    assert verified_councils["광명시의회"].source_pattern["listUrl"] == (
        "https://council.gm.go.kr/kr/costBBS.do"
    )
    assert verified_councils["고양시의회"].source_pattern["listUrl"] == (
        "https://www.goyangcouncil.go.kr/kr/costBBS.do"
    )
    assert verified_councils["구리시의회"].source_pattern["listUrl"] == (
        "https://www.gcc.or.kr/board/news/list.do?tbname=cost"
    )
    assert verified_councils["남양주시의회"].source_pattern["listUrl"] == (
        "https://nyjc.go.kr/content/dataroom/propelclosed.html"
    )
    assert verified_councils["용인시의회"].source_pattern["listUrl"] == (
        "https://council.yongin.go.kr/kr/costBBS.do"
    )
    assert verified_councils["부천시의회"].source_pattern["listUrl"] == (
        "https://council.bucheon.go.kr/kr/intro/bbsInfo.do"
    )
    assert verified_councils["안양시의회"].source_pattern["listUrl"] == (
        "https://www.aycouncil.go.kr/kr/costBBSlist.do?page=1"
    )
    assert verified_councils["군포시의회"].source_pattern["listUrl"] == (
        "https://www.gunpocouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_councils["의왕시의회"].source_pattern["listUrl"] == (
        "https://council.uiwang.go.kr/kr/news/bbsCost.do?flag=&keyword="
    )
    assert verified_councils["과천시의회"].source_pattern["listUrl"] == (
        "https://www.gccouncil.go.kr/kr/costBBSlist.do?page=1"
    )
    assert verified_councils["오산시의회"].source_pattern["listUrl"] == (
        "https://www.osancouncil.go.kr/kr/news/bbs?bbs_id=work"
    )
    assert verified_councils["시흥시의회"].source_pattern["listUrl"] == (
        "https://www.siheungcouncil.go.kr/content/activity/business.html"
    )
    assert verified_councils["하남시의회"].source_pattern["listUrl"] == (
        "https://council.hanam.go.kr/content/community/business.html"
    )
    assert verified_councils["파주시의회"].source_pattern["listUrl"] == (
        "https://www.pajucouncil.go.kr/content/data/operatingExpense.html"
    )
    assert verified_councils["광주시의회"].source_pattern["listUrl"] == (
        "https://www.gjcouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_councils["포천시의회"].source_pattern["listUrl"] == (
        "https://council.pocheon.go.kr/kr/news/bbsBusiness.do"
    )
    assert verified_councils["여주시의회"].source_pattern["listUrl"] == (
        "https://www.yeojucouncil.go.kr/kr/costBBS.do"
    )
    assert verified_councils["양주시의회"].source_pattern["listUrl"] == (
        "https://yjcc.yangju.go.kr/yjcc/selectBbsNttList.do?bbsNo=302&key=2559"
    )
    assert verified_councils["이천시의회"].source_pattern["listUrl"] == (
        "https://council.icheon.go.kr/content/information/businessOperatingExpense.html"
    )
    assert verified_councils["안성시의회"].source_pattern["listUrl"] == (
        "https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    )
    assert verified_councils["김포시의회"].source_pattern["listUrl"] == (
        "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702"
    )
    assert verified_councils["김포시의회"].source_pattern["jsDownloadPath"] == (
        "/sma/utl/FileDownLoad.php"
    )
    assert verified_councils["화성시의회"].source_pattern["listUrl"] == (
        "https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08"
    )
    assert verified_councils["화성시의회"].source_pattern["jsDownloadPath"] == (
        "/cms/utl/FileDownLoad.php"
    )
    assert verified_councils["연천군의회"].source_pattern["listUrl"] == (
        "https://www.yca21.go.kr/board/news/list.do?tbname=cost"
    )
    assert verified_councils["가평군의회"].source_pattern["listUrl"] == (
        "https://www.gpassem.go.kr/kr/operations2BBS.do"
    )
    assert verified_councils["양평군의회"].source_pattern["listUrl"] == (
        "https://www.ypcouncil.go.kr/main/selectBbsNttList.do?bbsNo=9&key=43"
    )

    verified_incheon = {
        agency.short_name: agency
        for agency in INCHEON_AGENCIES
        if agency.short_name
        in {
            "인천시청",
            "중구청",
            "중구의회",
            "동구청",
            "미추홀구청",
            "연수구청",
            "부평구청",
            "남동구청",
            "남동구의회",
            "계양구청",
            "서구청",
            "동구의회",
            "연수구의회",
            "부평구의회",
            "계양구의회",
            "서구의회",
            "강화군청",
            "강화군의회",
            "옹진군청",
            "옹진군의회",
        }
    }
    assert verified_incheon["인천시청"].source_pattern["listUrl"] == (
        "https://www.incheon.go.kr/open/OPEN010305"
    )
    assert verified_incheon["중구청"].source_pattern["listUrl"] == "https://www.icjg.go.kr/krop0307c"
    assert verified_incheon["중구의회"].source_pattern["listUrl"] == (
        "https://www.icjg.go.kr/council/cnac04b"
    )
    assert verified_incheon["동구청"].source_pattern["listUrl"] == (
        "https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84"
    )
    assert verified_incheon["계양구청"].source_pattern["listUrl"] == (
        "https://www.gyeyang.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=board_14&cate1=94"
    )
    assert verified_incheon["서구청"].source_pattern["listUrl"] == (
        "https://www.seo.incheon.kr/open_content/main/bbs/bbsMsgList.do?bcd=clean_cost"
    )
    assert verified_incheon["미추홀구청"].source_pattern["listUrl"] == (
        "https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year="
    )
    assert verified_incheon["연수구청"].source_pattern["listUrl"] == (
        "https://www.yeonsu.go.kr/main/administration/open_info/charge.asp"
    )
    assert verified_incheon["부평구청"].source_pattern["listUrl"] == (
        "https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost"
    )
    assert verified_incheon["남동구청"].source_pattern["listUrl"] == (
        "https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure"
    )
    assert verified_incheon["남동구의회"].source_pattern["listUrl"] == (
        "https://council.namdong.go.kr/kr/data/bbsBreakdown.do"
    )
    assert verified_incheon["서구의회"].source_pattern["listUrl"] == (
        "https://www.seo.incheon.kr/open_content/council/activity/open.jsp"
    )
    assert verified_incheon["동구의회"].source_pattern["listUrl"] == (
        "https://council.icdonggu.go.kr/kr/costBBS.do"
    )
    assert verified_incheon["연수구의회"].source_pattern["listUrl"] == (
        "https://council.yeonsu.go.kr/kr/businessBBS.do"
    )
    assert verified_incheon["부평구의회"].source_pattern["listUrl"] == (
        "https://council.icbp.go.kr/kr/data/bbs?bbs_id=expense"
    )
    assert verified_incheon["계양구의회"].source_pattern["listUrl"] == (
        "https://council.gyeyang.go.kr/kr/costBBS.do"
    )
    assert verified_incheon["강화군청"].source_pattern["listUrl"] == (
        "https://www.ganghwa.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=operation"
    )
    assert verified_incheon["강화군의회"].source_pattern["listUrl"] == (
        "https://council.ganghwa.go.kr/kr/workBBS.do"
    )
    assert verified_incheon["옹진군청"].source_pattern["listUrl"] == (
        "https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1"
    )
    assert verified_incheon["옹진군의회"].source_pattern["listUrl"] == (
        "https://council.ongjin.go.kr/kr/costBBS.do"
    )


def test_capital_area_parent_regions_are_correct() -> None:
    assert all(agency.parent_region == "경기도" for agency in GYEONGGI_AGENCIES)
    assert all(agency.parent_region == "인천광역시" for agency in INCHEON_AGENCIES)


def test_nationwide_does_not_create_eup_myeon_dong_agencies() -> None:
    forbidden_fragments = {"행정복지센터", "주민센터", "동사무소", "읍사무소", "면사무소"}

    assert all(
        not any(fragment in agency.name for fragment in forbidden_fragments)
        for agency in NATIONWIDE_AGENCIES
    )


def test_capital_area_ids_are_region_prefixed_and_unique() -> None:
    assert len({a.id for a in CAPITAL_AREA_AGENCIES}) == 138
    assert len({a.id for a in LOCAL_GOVERNMENT_AGENCIES}) == 486
    assert len({a.id for a in NATIONWIDE_AGENCIES}) == 2200


def test_capital_area_jurisdiction_type_spot_checks() -> None:
    gyeonggi = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "경기도청")
    suwon = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "수원시청")
    yeonseongun = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "연천군청")
    incheon = next(agency for agency in INCHEON_AGENCIES if agency.short_name == "인천시청")
    ganghwa = next(agency for agency in INCHEON_AGENCIES if agency.short_name == "강화군청")
    junro = next(agency for agency in INCHEON_AGENCIES if agency.short_name == "중구청")

    assert gyeonggi.jurisdiction_type == JurisdictionType.PROVINCE
    assert suwon.jurisdiction_type == JurisdictionType.SI
    assert yeonseongun.jurisdiction_type == JurisdictionType.GUN
    assert incheon.jurisdiction_type == JurisdictionType.METRO_CITY
    assert ganghwa.jurisdiction_type == JurisdictionType.GUN
    assert junro.jurisdiction_type == JurisdictionType.AUTONOMOUS_GU
