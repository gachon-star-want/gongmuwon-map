from __future__ import annotations

from uuid import UUID, uuid5

from public_officer_pipeline.models import (
    SEOUL_CITY_HALL_AGENCY_ID,
    Agency,
    AgencyKind,
)


AGENCY_NAMESPACE = UUID("01aa6c02-04a8-4f38-b69c-3b49f6a6f24d")

SEOUL_GU_NAMES = [
    "강남구",
    "강동구",
    "강북구",
    "강서구",
    "관악구",
    "광진구",
    "구로구",
    "금천구",
    "노원구",
    "도봉구",
    "동대문구",
    "동작구",
    "마포구",
    "서대문구",
    "서초구",
    "성동구",
    "성북구",
    "송파구",
    "양천구",
    "영등포구",
    "용산구",
    "은평구",
    "종로구",
    "중구",
    "중랑구",
]

SEOUL_GU_DOMAIN_SLUGS = {
    "강남구": "gangnam",
    "강동구": "gangdong",
    "강북구": "gangbuk",
    "강서구": "gangseo",
    "관악구": "gwanak",
    "광진구": "gwangjin",
    "구로구": "guro",
    "금천구": "geumcheon",
    "노원구": "nowon",
    "도봉구": "dobong",
    "동대문구": "ddm",
    "동작구": "dongjak",
    "마포구": "mapo",
    "서대문구": "sdm",
    "서초구": "seocho",
    "성동구": "sd",
    "성북구": "sb",
    "송파구": "songpa",
    "양천구": "yangcheon",
    "영등포구": "ydp",
    "용산구": "yongsan",
    "은평구": "ep",
    "종로구": "jongno",
    "중구": "junggu",
    "중랑구": "jn",
}


def agency_uuid(key: str) -> UUID:
    return uuid5(AGENCY_NAMESPACE, key)


def seoul_agencies() -> list[Agency]:
    agencies = [
        Agency(),
        Agency(
            id=agency_uuid("seoul_city_council"),
            name="서울특별시의회",
            short_name="서울시의회",
            kind=AgencyKind.CITY_COUNCIL,
            parent_region="서울특별시",
            homepage="https://opengov.seoul.go.kr/expense/list",
            source_pattern={
                "adapter": "seoul_opengov",
                "searchKeyword": "의회사무처",
                "titleIncludes": ["의회사무처"],
            },
        ),
    ]

    for gu in SEOUL_GU_NAMES:
        domain_slug = SEOUL_GU_DOMAIN_SLUGS[gu]
        agencies.append(
            Agency(
                id=agency_uuid(f"{gu}:office"),
                name=f"서울특별시 {gu}청",
                short_name=f"{gu}청",
                kind=AgencyKind.GU_OFFICE,
                parent_region="서울특별시",
                sub_region=gu,
                homepage=f"https://www.{domain_slug}.go.kr",
                source_pattern={
                    "adapter": "district_board_required",
                    "searchKeyword": f"{gu}청 업무추진비",
                    "status": "adapter_required",
                },
            )
        )
        agencies.append(
            Agency(
                id=agency_uuid(f"{gu}:council"),
                name=f"서울특별시 {gu}의회",
                short_name=f"{gu}의회",
                kind=AgencyKind.GU_COUNCIL,
                parent_region="서울특별시",
                sub_region=gu,
                homepage=f"https://council.{domain_slug}.go.kr",
                source_pattern={
                    "adapter": "district_council_board_required",
                    "searchKeyword": f"{gu}의회 업무추진비",
                    "status": "adapter_required",
                },
            )
        )

    return agencies


SEOUL_AGENCIES = seoul_agencies()

assert len(SEOUL_AGENCIES) == 52
assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID
