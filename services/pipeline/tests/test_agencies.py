from public_officer_pipeline.agencies import (
    CAPITAL_AREA_AGENCIES,
    GYEONGGI_AGENCIES,
    INCHEON_AGENCIES,
    SEOUL_AGENCIES,
)
from public_officer_pipeline.models import (
    GovTier,
    GovBranch,
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


def test_capital_area_adapter_required_agencies_have_no_homepages_or_real_urls() -> None:
    for agency in GYEONGGI_AGENCIES + INCHEON_AGENCIES:
        assert agency.source_pattern.get("status") == "adapter_required"
        assert "listUrl" not in agency.source_pattern
        assert "source_url" not in agency.source_pattern
        assert agency.homepage is None


def test_capital_area_parent_regions_are_correct() -> None:
    assert all(agency.parent_region == "경기도" for agency in GYEONGGI_AGENCIES)
    assert all(agency.parent_region == "인천광역시" for agency in INCHEON_AGENCIES)


def test_capital_area_ids_are_region_prefixed_and_unique() -> None:
    assert len({a.id for a in CAPITAL_AREA_AGENCIES}) == 138


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
