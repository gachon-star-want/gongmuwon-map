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

SEOUL_COUNCIL_HOMEPAGES = {
    "강남구": "https://www.gncouncil.go.kr",
    "강동구": "https://council.gangdong.go.kr",
    "강북구": "https://council.gangbuk.go.kr",
    "강서구": "https://gsc.gangseo.seoul.kr",
    "관악구": "https://www.ga21c.seoul.kr",
    "광진구": "https://council.gwangjin.go.kr",
    "구로구": "https://www.guroc.go.kr",
    "금천구": "https://council.geumcheon.go.kr",
    "노원구": "https://council.nowon.kr",
    "도봉구": "https://www.council-dobong.seoul.kr",
    "동대문구": "https://council.ddm.go.kr",
    "동작구": "https://assembly.dongjak.go.kr",
    "마포구": "https://council.mapo.seoul.kr",
    "서대문구": "https://www.sdmcouncil.go.kr",
    "서초구": "https://www.sdc.seoul.kr",
    "성동구": "https://sdcouncil.sd.go.kr",
    "성북구": "https://www.sbc.go.kr",
    "송파구": "https://council.songpa.go.kr",
    "양천구": "https://www.ycc.go.kr",
    "영등포구": "https://www.ydpc.go.kr",
    "용산구": "https://www.yscl.go.kr",
    "은평구": "https://council.ep.go.kr",
    "종로구": "https://council.jongno.go.kr",
    "중구": "https://council.junggu.seoul.kr",
    "중랑구": "https://council.jungnang.go.kr",
}

SEOUL_COUNCIL_ATTACHMENT_BOARDS = {
    "강남구": "https://www.gncouncil.go.kr/kr/noticeBBS.do",
    "강동구": "https://council.gangdong.go.kr/kr/news/bbsBusiness.do",
    "강북구": "https://council.gangbuk.go.kr/kr/costBBS.do",
    "강서구": "https://gsc.gangseo.seoul.kr/kr/costBBS.do",
    "관악구": "https://www.ga21c.seoul.kr/kr/costBBS.do",
    "광진구": "https://council.gwangjin.go.kr/kr/data/bbs?bbs_id=businesswork",
    "구로구": "https://www.guroc.go.kr/kr/costBBS.do",
    "금천구": "https://council.geumcheon.go.kr/council/kr/costBBS.do",
    "동대문구": "https://council.ddm.go.kr/kr/busiexpensesBBS.do",
    "동작구": "https://assembly.dongjak.go.kr/kr/costBBS.do",
    "도봉구": "https://www.council-dobong.seoul.kr/kr/activity/bbsCost.do",
    "마포구": "https://council.mapo.seoul.kr/kr/news/bbsCost.do",
    "서대문구": "https://www.sdmcouncil.go.kr/source/korean/partake/business.html",
    "서초구": "https://www.sdc.seoul.kr/kr/news/bbsBusiness.do",
    "성동구": "https://sdcouncil.sd.go.kr/kr/data/bbs?bbs_id=expenses",
    "성북구": "https://www.sbc.go.kr/kr/news/bbsCost.do",
    "송파구": "https://council.songpa.go.kr/kr/news/bbsCost.do",
    "양천구": "https://www.ycc.go.kr/kr/news/bbs?bbs_id=business",
    "영등포구": "https://www.ydpc.go.kr/content/news/bbsCost.html",
    "용산구": "https://www.yscl.go.kr/kr/councilcostBBS.do",
    "은평구": "https://council.ep.go.kr/kr/costBBS.do",
    "종로구": "https://council.jongno.go.kr/council/bbs/BBSMSTR_000000000061/list.do?menuNo=401070",
    "중구": "https://council.junggu.seoul.kr/kr/bbs?bbs_id=cost",
    "중랑구": "https://council.jungnang.go.kr/kr/costBBS.do",
}

SEOUL_COUNCIL_DETAIL_ATTACHMENT_BOARDS = {
    "강동구",
    "광진구",
    "도봉구",
    "마포구",
    "서대문구",
    "서초구",
    "성동구",
    "성북구",
    "송파구",
    "양천구",
    "영등포구",
    "종로구",
    "중구",
}

SEOUL_OFFICE_ATTACHMENT_BOARDS = {
    "강동구": "https://www.gangdong.go.kr/web/newportal/bbs/b_054",
    "강서구": "https://www.gangseo.seoul.kr/gs030325",
    "구로구": "https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=655&key=1732",
    "금천구": "https://www.geumcheon.go.kr/portal/selectBbsNttList.do?bbsNo=86&key=269",
    "동대문구": "https://www.ddm.go.kr/www/selectBbsNttList.do?bbsNo=160&key=565",
    "마포구": "https://www.mapo.go.kr/site/main/board/expense/list",
    "노원구": "https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1012",
    "서초구": "https://www.seocho.go.kr/site/seocho/ex/bbs/List.do?cbIdx=33",
    "성동구": "https://sd.go.kr/main/selectBbsNttList.do?bbsNo=172&key=1330",
    "송파구": "https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=327&key=2323",
    "양천구": "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397",
}

SEOUL_OFFICE_DETAIL_ATTACHMENT_BOARDS = {
    "강동구",
    "강서구",
    "금천구",
    "동대문구",
    "마포구",
    "서초구",
    "양천구",
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
        office_source_pattern = {
            "adapter": "district_board_required",
            "searchKeyword": f"{gu}청 업무추진비",
            "status": "adapter_required",
        }
        if gu == "강남구":
            office_source_pattern = {
                "adapter": "gangnam_xlsx_board",
                "listUrl": "https://www.gangnam.go.kr/board/B_000673/list.do?mid=ID05_04200502",
                "fileKinds": ["xlsx"],
            }
        elif gu == "관악구":
            office_source_pattern = {
                "adapter": "estimate_list_html",
                "listUrl": "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do",
                "rowsPerPage": 10,
            }
        elif gu in SEOUL_OFFICE_ATTACHMENT_BOARDS:
            office_source_pattern = {
                "adapter": "attachment_board",
                "listUrl": SEOUL_OFFICE_ATTACHMENT_BOARDS[gu],
                "fileKinds": ["pdf", "xls", "xlsx"],
                "followDetail": gu in SEOUL_OFFICE_DETAIL_ATTACHMENT_BOARDS,
            }
        agencies.append(
            Agency(
                id=agency_uuid(f"{gu}:office"),
                name=f"서울특별시 {gu}청",
                short_name=f"{gu}청",
                kind=AgencyKind.GU_OFFICE,
                parent_region="서울특별시",
                sub_region=gu,
                homepage=f"https://www.{domain_slug}.go.kr",
                source_pattern=office_source_pattern,
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
                homepage=SEOUL_COUNCIL_HOMEPAGES[gu],
                source_pattern=(
                    {
                        "adapter": "council_attachment_board",
                        "listUrl": SEOUL_COUNCIL_ATTACHMENT_BOARDS[gu],
                        "fileKinds": ["pdf", "xls", "xlsx"],
                        "followDetail": gu in SEOUL_COUNCIL_DETAIL_ATTACHMENT_BOARDS,
                    }
                    if gu in SEOUL_COUNCIL_ATTACHMENT_BOARDS
                    else {
                        "adapter": "district_council_board_required",
                        "searchKeyword": f"{gu}의회 업무추진비",
                        "status": "adapter_required",
                    }
                ),
            )
        )

    return agencies


SEOUL_AGENCIES = seoul_agencies()

assert len(SEOUL_AGENCIES) == 52
assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID
