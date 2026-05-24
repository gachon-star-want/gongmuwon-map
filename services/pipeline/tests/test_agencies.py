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
        "강북구의회",
        "강서구의회",
        "관악구의회",
        "구로구의회",
        "동작구의회",
        "은평구의회",
        "중랑구의회",
    }
