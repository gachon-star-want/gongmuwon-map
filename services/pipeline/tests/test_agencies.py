from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.models import AgencyKind, SEOUL_CITY_HALL_AGENCY_ID


def test_seoul_agency_master_has_v1_scope() -> None:
    assert len(SEOUL_AGENCIES) == 52
    assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID


def test_seoul_agency_master_has_expected_kinds() -> None:
    counts = {kind: sum(1 for agency in SEOUL_AGENCIES if agency.kind == kind) for kind in AgencyKind}

    assert counts == {
        AgencyKind.CITY_HALL: 1,
        AgencyKind.CITY_COUNCIL: 1,
        AgencyKind.GU_OFFICE: 25,
        AgencyKind.GU_COUNCIL: 25,
    }


def test_seoul_agency_unique_identity_keys() -> None:
    keys = {(agency.kind, agency.parent_region, agency.sub_region) for agency in SEOUL_AGENCIES}

    assert len(keys) == len(SEOUL_AGENCIES)


def test_seoul_council_homepages_use_verified_domains() -> None:
    gangnam_council = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강남구의회")
    gangseo_council = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강서구의회")

    assert gangnam_council.homepage == "https://www.gncouncil.go.kr"
    assert gangseo_council.homepage == "https://gsc.gangseo.seoul.kr"


def test_seoul_council_attachment_boards_registered_for_verified_cost_pages() -> None:
    supported = {
        agency.short_name
        for agency in SEOUL_AGENCIES
        if agency.kind == AgencyKind.GU_COUNCIL and agency.source_pattern.get("adapter") == "council_attachment_board"
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
    assert jongno.source_pattern["followDetail"] is True
    assert junggu.source_pattern["followDetail"] is True


def test_seoul_office_html_estimate_board_registered_for_gwanak() -> None:
    gwanak = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "관악구청")

    assert gwanak.source_pattern["adapter"] == "estimate_list_html"
    assert gwanak.source_pattern["listUrl"] == "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do"


def test_seoul_office_attachment_board_registered_for_gangdong() -> None:
    gangdong = next(agency for agency in SEOUL_AGENCIES if agency.short_name == "강동구청")

    assert gangdong.source_pattern["adapter"] == "attachment_board"
    assert gangdong.source_pattern["listUrl"] == "https://www.gangdong.go.kr/web/newportal/bbs/b_054"
    assert gangdong.source_pattern["followDetail"] is True


def test_seoul_office_attachment_boards_registered_for_egov_boards() -> None:
    supported = {
        agency.short_name: agency.source_pattern["listUrl"]
        for agency in SEOUL_AGENCIES
        if agency.kind == AgencyKind.GU_OFFICE and agency.source_pattern.get("adapter") == "attachment_board"
    }

    assert supported["구로구청"] == "https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=655&key=1732"
    assert supported["금천구청"] == "https://www.geumcheon.go.kr/portal/selectBbsNttList.do?bbsNo=86&key=269"
    assert supported["동대문구청"] == "https://www.ddm.go.kr/www/selectBbsNttList.do?bbsNo=160&key=565"
    assert supported["서초구청"] == "https://www.seocho.go.kr/site/seocho/ex/bbs/List.do?cbIdx=33"
