from __future__ import annotations

from uuid import UUID, uuid5

from public_officer_pipeline.models import (
    SEOUL_CITY_HALL_AGENCY_ID,
    Agency,
    ExpansionPhase,
    GovTier,
    GovBranch,
    JurisdictionType,
)
from public_officer_pipeline.public_sector_baselines import (
    CENTRAL_STATE_BASELINE_SOURCE_URL,
    CENTRAL_STATE_CHART_URL,
    LOCAL_PUBLIC_BASELINE_SOURCE_URL,
    PUBLIC_INSTITUTION_BASELINE_SOURCE_URL,
    PUBLIC_INSTITUTION_MOEF_SOURCE_URL,
    central_state_baseline,
    local_public_institution_baseline,
    public_institution_baseline,
)


AGENCY_NAMESPACE = UUID("01aa6c02-04a8-4f38-b69c-3b49f6a6f24d")
ALIO_WORKCOST_SOURCE_URL = "https://www.alio.go.kr/item/itemOrganList.do?reportFormRootNo=20701"
ALIO_WORKCOST_LIST_API_URL = "https://www.alio.go.kr/item/itemOrganListJung.json"
ALIO_COPYRIGHT_URL = "https://www.alio.go.kr/notice/copyright.do"
CLEANEYE_PUBLIC_ENTERPRISE_WORKCOST_URL = "https://www.cleaneye.go.kr/user/headOrgWorkCostStat.do"
CLEANEYE_PUBLIC_ENTERPRISE_DISCLOSURE_URL = "https://www.cleaneye.go.kr/user/itemGongsi.do"
CLEANEYE_PUBLIC_ENTERPRISE_OWNER_WORKCOST_URL = "https://www.cleaneye.go.kr/user/empOwnerWorkCost.do"
CLEANEYE_LOCAL_FOUNDATION_DISCLOSURE_URL = "https://www.cleaneye.go.kr/user/iptItemGongsi.do"
CLEANEYE_COPYRIGHT_URL = "https://www.cleaneye.go.kr/user/copyrightPolicy.do"

P3_ALIO_PLACE_LEVEL_CANDIDATES = {
    "게임물관리위원회",
    "(재)우체국금융개발원",
    "한국남부발전(주)",
    "한국석유공사",
}
P3_ALIO_AMOUNT_THOUSANDS_NEEDS_PATCH: set[str] = set()
P3_ALIO_RECENT_AGGREGATE_ONLY = {
    "농림수산식품교육문화정보원",
    "인천국제공항공사",
    "한국수산자원공단",
}
P3_ALIO_PDF_VISION_HOLD = {
    "공간정보산업진흥원",
    "민주화운동기념사업회",
    "수도권매립지관리공사",
    "주택관리공단(주)",
    "학교법인한국폴리텍",
    "한국교통연구원",
    "한국국제협력단",
    "한국형사·법무정책연구원",
}
P3_ALIO_HWP_PARSER_HOLD = {
    "대한법률구조공단",
    "정부법무공단",
}
P3_ALIO_DOWNLOAD_HOLD = {
    "대한장애인체육회",
    "대한체육회",
    "스포츠윤리센터",
    "아시아·태평양경제협력체 기후센터",
    "재단법인 건설기술교육원",
    "재단법인 대한건설기계안전관리원",
    "재단법인 장애인기업종합지원센터",
    "재단법인 한국공공조직은행",
    "재단법인 한국에너지재단",
    "재단법인 한국자활복지개발원",
    "재단법인 한국장기조직기증원",
    "주식회사 에스알",
    "한국등산·트레킹지원센터",
    "한국영유아보육·교육진흥원",
}
P3_ALIO_XLS_PARSER_HOLD = {
    "(재)한국통계진흥원",
    "건강보험심사평가원",
    "경제인문사회연구회",
    "공간정보품질관리원",
    "국립낙동강생물자원관",
    "국립중앙의료원",
    "국민건강보험공단",
    "국제방송교류재단",
    "국제식물검역인증원",
    "농림식품기술기획평가원",
    "농업정책보험금융원",
    "무역안보관리원",
    "예술의전당",
    "울산항만공사",
    "전남대학교병원",
    "중소기업은행",
    "창업진흥원",
    "축산물품질평가원",
    "태권도진흥재단",
    "통일연구원",
    "한국건강가정진흥원",
    "한국국토정보공사",
    "한국농촌경제연구원",
    "한국법무보호복지공단",
    "한국보건산업진흥원",
    "한국부동산원",
    "한국에너지공단",
    "한국에너지정보문화재단",
    "한국전력거래소",
    "한국제품안전관리원",
    "한국토지주택공사",
    "한국항로표지기술원",
    "한국해양교통안전공단",
    "한국해양조사협회",
}
P4_CLEANEYE_PLACE_LEVEL_CANDIDATES = {
    "경기주택도시공사": {
        "entId": "2007100239",
        "entKind": "006002",
        "entName": "경기주택도시공사",
    }
}
P4_CLEANEYE_RECENT_AGGREGATE_ONLY = {
    "서울시설공단": {
        "entId": "2007100264",
        "entKind": "011001",
        "entName": "서울시설공단",
    },
    "서울농수산식품공사": {
        "entId": "2007100247",
        "entKind": "006003",
        "entName": "서울특별시농수산식품공사",
    },
}

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

SEOUL_GU_HOMEPAGES = {
    "중구": "https://www.junggu.seoul.kr",
    "중랑구": "https://www.jungnang.go.kr",
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
    "노원구": "https://council.nowon.kr/kr/news/bbsData.do",
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
    "노원구",
}

SEOUL_OFFICE_ATTACHMENT_BOARDS = {
    "강북구": "https://child.gangbuk.go.kr/portal/intgty/deptJobPrtnCt/list.do?menuNo=200155",
    "강동구": "https://www.gangdong.go.kr/web/newportal/bbs/b_054",
    "강서구": "https://www.gangseo.seoul.kr/gs030325",
    "광진구": "https://www.gwangjin.go.kr/portal/bbs/B0000027/list.do?menuNo=201646",
    "구로구": "https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=655&key=1732",
    "금천구": "https://www.geumcheon.go.kr/portal/selectBbsNttList.do?bbsNo=86&key=269",
    "도봉구": "https://www.dobong.go.kr/Contents.asp?code=10008860",
    "동대문구": "https://www.ddm.go.kr/www/selectBbsNttList.do?bbsNo=160&key=565",
    "동작구": "https://www.dongjak.go.kr/portal/bbs/B0000591/list.do?menuNo=200209",
    "마포구": "https://www.mapo.go.kr/site/main/board/expense/list",
    "노원구": "https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1012",
    "서초구": "https://www.seocho.go.kr/site/seocho/ex/bbs/List.do?cbIdx=33",
    "성동구": "https://sd.go.kr/main/selectBbsNttList.do?bbsNo=172&key=1330",
    "성북구": "https://www.sb.go.kr/www/selectBbsNttList.do?bbsNo=28&key=5923",
    "송파구": "https://www.songpa.go.kr/www/selectBbsNttList.do?bbsNo=327&key=2323",
    "양천구": "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397",
    "영등포구": "https://www.ydp.go.kr/www/selectBbsNttList.do?bbsNo=31&key=2814",
    "용산구": "https://www.yongsan.go.kr/portal/bbs/B0000030/list.do?menuNo=200140",
    "종로구": "https://www.jongno.go.kr/portal/bbs/selectBoardList.do?bbsId=BBSMSTR_000000001167&menuId=110210&menuNo=110210",
    "중구": "https://www.junggu.seoul.kr/content.do?cmsid=15383&exclude=Y",
    "중랑구": "https://www.jungnang.go.kr/portal/bbs/list/B0000143.do?menuNo=200432",
}

SEOUL_OFFICE_INLINE_TABLES = {
    "서대문구": "https://www.sdm.go.kr/admininfo/budget/openmoney.do",
    "은평구": "https://www.ep.go.kr/www/selectJobPrtnCtWebList.do?key=666",
}

SEOUL_OFFICE_DETAIL_ATTACHMENT_BOARDS = {
    "강동구",
    "강서구",
    "광진구",
    "금천구",
    "도봉구",
    "동대문구",
    "동작구",
    "마포구",
    "서초구",
    "성북구",
    "양천구",
    "중구",
}

SEOUL_OFFICE_ATTACHMENT_PAGE_PARAMS = {
    "강북구": "pageIndex",
    "광진구": "pageIndex",
    "성북구": "pageIndex",
    "중구": "page2",
    "중랑구": "pageIndex",
}

SEOUL_OFFICE_ATTACHMENT_PAGE_UNIT_PARAMS = {
    "중랑구": "pageUnit",
}

GYEONGGI_CITIES = [
    "수원시",
    "성남시",
    "의정부시",
    "안양시",
    "부천시",
    "광명시",
    "평택시",
    "동두천시",
    "안산시",
    "고양시",
    "과천시",
    "구리시",
    "남양주시",
    "오산시",
    "시흥시",
    "군포시",
    "의왕시",
    "하남시",
    "용인시",
    "파주시",
    "이천시",
    "안성시",
    "김포시",
    "화성시",
    "광주시",
    "양주시",
    "포천시",
    "여주시",
]

GYEONGGI_COUNTIES = [
    "연천군",
    "가평군",
    "양평군",
]

GYEONGGI_OFFICE_PENDING_BLOCKERS = {
    "경기도청": (
        "공식 업무추진비 공개 보드군(https://www.gg.go.kr/bbs/board.do?bsIdx=803&menuId=1768 "
        "등)은 확인했지만 목록/상세 하단이 공공누리 제3유형(출처표시+변경금지)으로 "
        "표시되어 새 legal 재검토 기준상 변경금지 제한에 해당하므로 보류합니다. "
        "저작권 정책(https://www.gg.go.kr/contents/contents.do?ciIdx=1066&menuId=2772)도 "
        "제3유형의 2차적저작물 작성 등 변경금지를 명시합니다."
    ),
    "시흥시": (
        "공식 업무추진비 목록(https://www.siheung.go.kr/main/bbs/list.do?ptIdx=41&mId=0309110100)과 "
        "XLSX 첨부 구조는 확인했지만 상세 하단이 공공누리 제4유형(출처표시+상업적 "
        "이용금지+변경금지)으로 표시되어 새 legal 재검토 기준상 상업적 이용금지 및 "
        "변경금지 제한에 해당하므로 보류합니다."
    ),
    "이천시": (
        "공식 업무추진비 공개 페이지(https://www.icheon.go.kr/portal/contents.do?mid=0304080000)와 "
        "최근 XLSX 첨부 구조는 확인했습니다. 다만 개별 업무추진비 상세는 공공누리 유형 표시 "
        "없이 All Rights Reserved 푸터만 노출되고, 저작권보호정책"
        "(https://www.icheon.go.kr/portal/contents.do?mid=0705000000)이 공공누리 미부착 자료는 "
        "공공저작물 담당자와 사전 협의 후 이용하도록 명시하므로 보류합니다."
    ),
    "화성시": (
        "공식 사전정보공표 업무추진비 목록"
        "(https://www.hscity.go.kr/www/beffatPublict/BD_selectBeffatPublictBbsList.do?"
        "q_beffatPublictTy=1008&q_beffatPublictSj=657)과 최근 XLSX 첨부 구조는 확인했습니다. "
        "다만 업무추진비 목록/상세에는 공공누리 유형 표시가 없고, 저작권정책"
        "(https://www.hscity.go.kr/agree/copyright_policy.jsp)이 무단사용·변조·상업적 용도 "
        "사용 방지 및 공공누리 미부착 자료의 사전 협의를 명시하므로 보류합니다. "
        "또한 해당 사전정보공표 viewer는 별도 adapter 보강이 필요합니다."
    ),
    "여주시": (
        "공식 역할별 업무추진비 목록(시장 https://www.yeoju.go.kr/www/selectBbsNttList.do?bbsNo=32&key=369, "
        "부시장 bbsNo=33, 국장 bbsNo=34)과 최근 PDF/XLSX 첨부 구조는 확인했습니다. "
        "다만 목록/상세는 공공누리 유형 표시 없이 All Rights Reserved 푸터만 노출되고, "
        "저작권정책(https://www.yeoju.go.kr/www/contents.do?key=661)이 공공누리 미부착 자료는 "
        "담당자와 사전 협의 후 이용하도록 명시하므로 보류합니다."
    ),
}

GYEONGGI_COUNCIL_PENDING_BLOCKERS = {
    "안산시": (
        "공식 안산시의회 업무추진비 목록"
        "(https://www.ansan.go.kr/council/common/bbs/selectPageListBbs.do?bbs_code=B0406)과 "
        "최근 XLSX 첨부 구조는 확인했지만 목록 하단이 공공누리 제3유형(출처표시+변경금지)으로 "
        "표시되어 새 legal 재검토 기준상 변경금지 제한에 해당하므로 보류합니다."
    ),
}

INCHEON_COUNCIL_PENDING_BLOCKERS = {
    "미추홀구": (
        "공식 의회 의원업무추진비 목록"
        "(https://www.michuhol.go.kr/council/open_council/business_cost.asp, iframe "
        "https://www.michuhol.go.kr/ndsys/ndBBs/bbs_list.asp?bbs_code=board_189&dept_idx=)은 "
        "확인했지만 최근 첨부가 ZIP 중심이고 목록 하단이 공공누리 제4유형(출처표시+상업적 "
        "이용금지+변경금지)으로 표시되어 보류합니다. 새 legal 재검토 기준상 상업적 이용금지 "
        "및 변경금지 제한이며, ZIP 중심 첨부는 현재 안정 적재 대상이 아닙니다."
    ),
}

GYEONGGI_OFFICE_ATTACHMENT_BOARDS = {
    "수원시": {
        "homepage": "https://www.suwon.go.kr",
        "listUrl": "https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "성남시": {
        "homepage": "https://www.seongnam.go.kr",
        "listUrl": "https://www.seongnam.go.kr/city/1000199/30218/bbsList.do",
        "fileKinds": ["hwpx", "xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "currentPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "평택시": {
        "homepage": "https://www.pyeongtaek.go.kr",
        "listUrl": "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "안양시": {
        "homepage": "https://www.anyang.go.kr",
        "listUrl": "https://www.anyang.go.kr/main/selectBbsNttList.do?bbsNo=43&key=218",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "의정부시": {
        "homepage": "https://www.ui4u.go.kr",
        "listUrl": "https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25",
        "extraListUrls": [
            "https://www.ui4u.go.kr/portal/contents.do?mId=0114010000",
            "https://www.ui4u.go.kr/portal/contents.do?mId=0114010100",
            "https://www.ui4u.go.kr/portal/contents.do?mId=0114010200",
            "https://www.ui4u.go.kr/portal/contents.do?mId=0114010400",
        ],
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "동두천시": {
        "homepage": "https://www.ddc.go.kr",
        "listUrl": "https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "안산시": {
        "homepage": "https://www.ansan.go.kr",
        "listUrl": "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "currentPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "부천시": {
        "homepage": "https://www.bucheon.go.kr",
        "listUrl": "https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002",
        "fileKinds": ["xlsx", "xls", "pdf", "hwpx"],
        "followDetail": True,
        "pageParam": "currentpage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "김포시": {
        "homepage": "https://www.gimpo.go.kr",
        "listUrl": "https://www.gimpo.go.kr/portal/selectBbsNttList.do?bbsNo=199&key=1110",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "하남시": {
        "homepage": "https://www.hanam.go.kr",
        "listUrl": "https://www.hanam.go.kr/www/selectBbsNttList.do?bbsNo=15&key=51",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "광명시": {
        "homepage": "https://www.gm.go.kr",
        "listUrl": "https://www.gm.go.kr/pt/user/bbs/BD_selectBbsList.do?q_bbsCode=2472",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면 확인",
    },
    "구리시": {
        "homepage": "https://www.guri.go.kr",
        "listUrl": "https://www.guri.go.kr/www/selectBbsNttList.do?bbsNo=14&key=331",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "남양주시": {
        "homepage": "https://www.nyj.go.kr",
        "listUrl": "https://www.nyj.go.kr/www/selectBbsNttList.do?key=2432&bbsNo=43",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "오산시": {
        "homepage": "https://www.osan.go.kr",
        "listUrl": "https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "군포시": {
        "homepage": "https://www.gunpo.go.kr",
        "listUrl": "https://www.gunpo.go.kr/www/selectBbsNttList.do?bbsNo=715&key=4276",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "의왕시": {
        "homepage": "https://www.uiwang.go.kr",
        "listUrl": "https://www.uiwang.go.kr/UWKOROPEN0210",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "curPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "용인시": {
        "homepage": "https://www.yongin.go.kr",
        "listUrl": "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "q_currPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "고양시": {
        "homepage": "https://www.goyang.go.kr",
        "listUrl": "https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "q_currPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "파주시": {
        "homepage": "https://www.paju.go.kr",
        "listUrl": "https://www.paju.go.kr/user/policy_02/board/BD_board.list.do?bbsCd=1018",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "양주시": {
        "homepage": "https://www.yangju.go.kr",
        "listUrl": "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=30&key=234",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "포천시": {
        "homepage": "https://www.pocheon.go.kr",
        "listUrl": "https://www.pocheon.go.kr/www/selectBbsNttList.do?bbsNo=214&key=3687",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "연천군": {
        "homepage": "https://www.yeoncheon.go.kr",
        "listUrl": "https://www.yeoncheon.go.kr/www/selectBbsNttList.do?bbsNo=152&key=3352",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "광주시": {
        "homepage": "https://www.gjcity.go.kr",
        "listUrl": "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "과천시": {
        "homepage": "https://www.gccity.go.kr",
        "listUrl": "https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "가평군": {
        "homepage": "https://www.gp.go.kr",
        "listUrl": "https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "양평군": {
        "homepage": "https://www.yp21.go.kr",
        "listUrl": "https://www.yp21.go.kr/www/selectBbsNttList.do?bbsNo=43&key=1597",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "안성시": {
        "homepage": "https://www.anseong.go.kr",
        "listUrl": "https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
}

GYEONGGI_COUNCIL_ATTACHMENT_BOARDS = {
    "수원시": {
        "homepage": "https://council.suwon.go.kr",
        "listUrl": "https://council.suwon.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "성남시": {
        "homepage": "https://www.sncouncil.go.kr",
        "listUrl": "https://www.sncouncil.go.kr/kr/news/bbsCost.do",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": True,
        "pageParam": "pageNum",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "평택시": {
        "homepage": "https://www.ptcouncil.go.kr",
        "listUrl": "https://www.ptcouncil.go.kr/coun/cost/reportList.do",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "pageCurNo",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "의정부시": {
        "homepage": "https://www.ujbcl.go.kr",
        "listUrl": "https://www.ujbcl.go.kr/svc/bbs/BusinessList.do?bbsMnuCd=MNU002300000650400000666",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNo",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "동두천시": {
        "homepage": "https://council.ddc.go.kr",
        "listUrl": "https://council.ddc.go.kr/kr/news/bbsCost.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNum",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "광명시": {
        "homepage": "https://council.gm.go.kr",
        "listUrl": "https://council.gm.go.kr/kr/costBBS.do",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "고양시": {
        "homepage": "https://www.goyangcouncil.go.kr",
        "listUrl": "https://www.goyangcouncil.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "구리시": {
        "homepage": "https://www.gcc.or.kr",
        "listUrl": "https://www.gcc.or.kr/board/news/list.do?tbname=cost",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "남양주시": {
        "homepage": "https://nyjc.go.kr",
        "listUrl": "https://nyjc.go.kr/content/dataroom/propelclosed.html",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "용인시": {
        "homepage": "https://council.yongin.go.kr",
        "listUrl": "https://council.yongin.go.kr/kr/costBBS.do",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "부천시": {
        "homepage": "https://council.bucheon.go.kr",
        "listUrl": "https://council.bucheon.go.kr/kr/intro/bbsInfo.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNum",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "안양시": {
        "homepage": "https://www.aycouncil.go.kr",
        "listUrl": "https://www.aycouncil.go.kr/kr/costBBSlist.do?page=1",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "군포시": {
        "homepage": "https://www.gunpocouncil.go.kr",
        "listUrl": "https://www.gunpocouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "의왕시": {
        "homepage": "https://council.uiwang.go.kr",
        "listUrl": "https://council.uiwang.go.kr/kr/news/bbsCost.do?flag=&keyword=",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNum",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "과천시": {
        "homepage": "https://www.gccouncil.go.kr",
        "listUrl": "https://www.gccouncil.go.kr/kr/costBBSlist.do?page=1",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "오산시": {
        "homepage": "https://www.osancouncil.go.kr",
        "listUrl": "https://www.osancouncil.go.kr/kr/news/bbs?bbs_id=work",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "시흥시": {
        "homepage": "https://www.siheungcouncil.go.kr",
        "listUrl": "https://www.siheungcouncil.go.kr/content/activity/business.html",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "하남시": {
        "homepage": "https://council.hanam.go.kr",
        "listUrl": "https://council.hanam.go.kr/content/community/business.html",
        "fileKinds": ["pdf"],
        "defaultFileKind": "pdf",
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "파주시": {
        "homepage": "https://www.pajucouncil.go.kr",
        "listUrl": "https://www.pajucouncil.go.kr/content/data/operatingExpense.html",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "광주시": {
        "homepage": "https://www.gjcouncil.go.kr",
        "listUrl": "https://www.gjcouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "양주시": {
        "homepage": "https://yjcc.yangju.go.kr",
        "listUrl": "https://yjcc.yangju.go.kr/yjcc/selectBbsNttList.do?bbsNo=302&key=2559",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "이천시": {
        "homepage": "https://council.icheon.go.kr",
        "listUrl": "https://council.icheon.go.kr/content/information/businessOperatingExpense.html",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "안성시": {
        "homepage": "https://www.anseongcl.go.kr",
        "listUrl": "https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "김포시": {
        "homepage": "https://gimpocouncil.go.kr",
        "listUrl": "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNo",
        "jsDownloadPath": "/sma/utl/FileDownLoad.php",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "화성시": {
        "homepage": "https://council.hscity.go.kr",
        "listUrl": "https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNo",
        "jsDownloadPath": "/cms/utl/FileDownLoad.php",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "포천시": {
        "homepage": "https://council.pocheon.go.kr",
        "listUrl": "https://council.pocheon.go.kr/kr/news/bbsBusiness.do",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "여주시": {
        "homepage": "https://www.yeojucouncil.go.kr",
        "listUrl": "https://www.yeojucouncil.go.kr/kr/costBBS.do",
        "fileKinds": ["xls", "xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면 확인",
    },
    "가평군": {
        "homepage": "https://www.gpassem.go.kr",
        "listUrl": "https://www.gpassem.go.kr/kr/operations2BBS.do",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "followDetail": False,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "연천군": {
        "homepage": "https://www.yca21.go.kr",
        "listUrl": "https://www.yca21.go.kr/board/news/list.do?tbname=cost",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "양평군": {
        "homepage": "https://www.ypcouncil.go.kr",
        "listUrl": "https://www.ypcouncil.go.kr/main/selectBbsNttList.do?bbsNo=9&key=43",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
}

INCHEON_GUS = [
    "중구",
    "동구",
    "미추홀구",
    "연수구",
    "남동구",
    "부평구",
    "계양구",
    "서구",
]

INCHEON_COUNTIES = [
    "강화군",
    "옹진군",
]

NON_CAPITAL_REGIONAL_GOVERNMENTS = [
    (
        "busan",
        "부산광역시",
        "부산광역시청",
        "부산시청",
        "부산광역시의회",
        "부산시의회",
        JurisdictionType.METRO_CITY,
    ),
    (
        "daegu",
        "대구광역시",
        "대구광역시청",
        "대구시청",
        "대구광역시의회",
        "대구시의회",
        JurisdictionType.METRO_CITY,
    ),
    (
        "gwangju",
        "광주광역시",
        "광주광역시청",
        "광주시청",
        "광주광역시의회",
        "광주시의회",
        JurisdictionType.METRO_CITY,
    ),
    (
        "daejeon",
        "대전광역시",
        "대전광역시청",
        "대전시청",
        "대전광역시의회",
        "대전시의회",
        JurisdictionType.METRO_CITY,
    ),
    (
        "ulsan",
        "울산광역시",
        "울산광역시청",
        "울산시청",
        "울산광역시의회",
        "울산시의회",
        JurisdictionType.METRO_CITY,
    ),
    (
        "sejong",
        "세종특별자치시",
        "세종특별자치시청",
        "세종시청",
        "세종특별자치시의회",
        "세종시의회",
        JurisdictionType.SPECIAL_SELF_GOVERNING_CITY,
    ),
    (
        "gangwon",
        "강원특별자치도",
        "강원특별자치도청",
        "강원특별자치도청",
        "강원특별자치도의회",
        "강원특별자치도의회",
        JurisdictionType.SPECIAL_SELF_GOVERNING_PROVINCE,
    ),
    (
        "chungbuk",
        "충청북도",
        "충청북도청",
        "충청북도청",
        "충청북도의회",
        "충청북도의회",
        JurisdictionType.PROVINCE,
    ),
    (
        "chungnam",
        "충청남도",
        "충청남도청",
        "충청남도청",
        "충청남도의회",
        "충청남도의회",
        JurisdictionType.PROVINCE,
    ),
    (
        "jeonbuk",
        "전북특별자치도",
        "전북특별자치도청",
        "전북특별자치도청",
        "전북특별자치도의회",
        "전북특별자치도의회",
        JurisdictionType.SPECIAL_SELF_GOVERNING_PROVINCE,
    ),
    (
        "jeonnam",
        "전라남도",
        "전라남도청",
        "전라남도청",
        "전라남도의회",
        "전라남도의회",
        JurisdictionType.PROVINCE,
    ),
    (
        "gyeongbuk",
        "경상북도",
        "경상북도청",
        "경상북도청",
        "경상북도의회",
        "경상북도의회",
        JurisdictionType.PROVINCE,
    ),
    (
        "gyeongnam",
        "경상남도",
        "경상남도청",
        "경상남도청",
        "경상남도의회",
        "경상남도의회",
        JurisdictionType.PROVINCE,
    ),
    (
        "jeju",
        "제주특별자치도",
        "제주특별자치도청",
        "제주특별자치도청",
        "제주특별자치도의회",
        "제주특별자치도의회",
        JurisdictionType.SPECIAL_SELF_GOVERNING_PROVINCE,
    ),
]

GYEONGSANG_PARENT_REGIONS = {
    "부산광역시",
    "대구광역시",
    "울산광역시",
    "경상북도",
    "경상남도",
}

CHUNGCHEONG_PARENT_REGIONS = {
    "대전광역시",
    "세종특별자치시",
    "충청북도",
    "충청남도",
}

NON_CAPITAL_LEGAL_HOLD_BLOCKERS = {
    "광주시청": {
        "sourceUrl": "https://www.gwangju.go.kr/boardList.do?boardId=BD_0000000252&pageId=www101",
        "fileKinds": ["xls"],
        "pageParam": "movePage",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLS 다운로드 구조는 확인했습니다. 다만 상세 화면의 "
            "공공누리 표시가 '자유이용 불가'로 안내되어 있어 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "광주시의회": {
        "sourceUrl": "https://council.gwangju.go.kr/index.do?PID=168",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "pageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·다운로드 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    "부산시청": (
        "공식 업무추진비 목록(https://www.busan.go.kr/ghopen12?curPage=1&schBizNo=46&schCommand=Expense)은 "
        "확인했지만 목록 페이지에서 공공누리 유형 표시가 확인되지 않았고, 현재 로컬 수집 환경은 "
        "부산광역시 보안 장비 차단 화면으로 전환됩니다. 제1유형과 수집 접근성 확인 전까지 "
        "수집하지 않습니다."
    ),
    "부산시의회": (
        "공식 업무추진비 목록(https://council.busan.go.kr/council/infobbs0501)과 "
        "XLSX 첨부 구조는 확인했지만, 업무추진비 목록/상세 페이지에서 공공누리 유형 표시가 "
        "확인되지 않았습니다. 부산광역시의회 저작권 보호정책은 공공누리 표시가 부착된 "
        "저작물에 한해 자유이용 가능하다고 안내하므로, 제1유형 확인 전까지 수집하지 않습니다."
    ),
    "대구시청": (
        "공식 업무추진비 목록(https://www.daegu.go.kr/index.do?menu_id=00000084)과 XLSX 첨부 "
        "구조는 확인했지만 목록 페이지에서 공공누리 유형 표시가 확인되지 않았습니다. 대구광역시 "
        "공공저작물 이용안내는 공공누리 표시가 부착되지 않은 자료의 사용은 담당자와 사전 협의가 "
        "필요하다고 안내하므로, 제1유형 확인 전까지 수집하지 않습니다."
    ),
    "대구시의회": (
        "공식 업무추진비 목록(https://council.daegu.go.kr/kr/bbs?bbs_id=business)과 XLSX 첨부 "
        "구조는 확인했지만 목록 페이지에서 공공누리 유형 표시가 확인되지 않았습니다. "
        "대구광역시의회 저작권정책은 공공누리 표시가 부착된 공공저작물에 한해 자유이용 가능하다고 "
        "안내하므로, 제1유형 확인 전까지 수집하지 않습니다."
    ),
    "세종시청": {
        "sourceUrl": "https://www.sejong.go.kr/bbs/R0091/list.do",
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 상세 화면이 "
            "공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 표시되어 제1유형 원칙을 "
            "바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "세종시의회": {
        "sourceUrl": "https://council.sejong.go.kr/mnu/cap/businessExpenseList.do",
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 XLSX 첨부 구조는 확인했지만 목록/상세 페이지에서 "
            "공공누리 유형 표시가 확인되지 않았습니다. 제1유형 또는 명확한 자유이용 표시 "
            "확인 전까지 수집하지 않습니다."
        ),
    },
    "강원특별자치도청": {
        "sourceUrl": "https://state.gwd.go.kr/portal/administration/opendata/propulsionCost/governor",
        "extraListUrls": [
            "https://state.gwd.go.kr/portal/administration/opendata/propulsionCost/director"
        ],
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 도지사·부지사 업무추진비 목록과 실국과장·직속기관장 업무추진비 목록, "
            "상세·XLSX 다운로드 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 "
            "제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    "강원특별자치도의회": {
        "sourceUrl": "https://council.gangwon.kr/kr/infoBBS.do?flag=all&list_style=&page=1&schwrd=",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·PDF/XLS 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "전북특별자치도청": {
        "sourceUrl": "https://www.jeonbuk.go.kr/board/list.jeonbuk?boardId=BBS_0000029&listCel=1&listRow=10&menuCd=DOM_000000103005000000&paging=ok",
        "fileKinds": ["hwp", "hwpx", "xlsx", "xls", "pdf"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 상세·HWP/HWPX/XLSX/PDF 다운로드 구조는 확인했습니다. "
            "다만 목록/상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 "
            "표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "전북특별자치도의회": {
        "sourceUrl": "https://jbstatecouncil.jeonbuk.kr/jbassem/board/39/4",
        "fileKinds": ["xlsx", "pdf", "hwp"],
        "pageParam": "path",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 정보공개 목록과 상세·XLSX/PDF/HWP 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "전라남도의회": {
        "sourceUrl": "https://www.jnassembly.go.kr/jnassem/board/412",
        "extraListUrls": ["https://www.jnassembly.go.kr/jnassem/board/51/1/category8"],
        "fileKinds": ["pdf"],
        "pageParam": "path",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 의정활동 정보공개 업무추진비 목록과 사전정보공표 업무추진비 연결 목록, "
            "경로형 페이지네이션, 상세·PDF 다운로드 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "충청남도청": {
        "sourceUrl": "https://www.chungnam.go.kr/cnportal/bbs/B0000187/list.do?menuNo=500122",
        "fileKinds": ["hwp", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·HWP/PDF 다운로드 구조는 확인했습니다. 다만 상세 화면이 "
            "공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 표시되어 제1유형 "
            "원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "충청남도의회": {
        "sourceUrl": "https://council.chungnam.go.kr/kr/costBBS.do?flag=all&list_style=&page=1&schwrd=",
        "fileKinds": ["pdf", "hwp", "xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·PDF/HWP/XLS/XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "충청북도청": {
        "sourceUrl": "https://www.chungbuk.go.kr/www/selectBbsNttList.do?bbsNo=2&key=211",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "충청북도의회": {
        "sourceUrl": "https://council.chungbuk.kr/kr/memberCostBBS.do?flag=all&list_style=&page=1&publish=&schwrd=&th_sch=",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 상세·XLS/XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "경상북도청": {
        "sourceUrl": "https://www.gb.go.kr/Main/page.do?mnu_uid=7406&BD_CODE=openhjinfo_deptmoney&cmd=1",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "Start",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX/XLS/PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면이 공공누리 제3유형(출처표시+변경금지)으로 표시되어 "
            "제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "경상북도의회": {
        "sourceUrl": "https://council.gb.go.kr/kr/bbs?bbs_id=open",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "경상남도청": {
        "sourceUrl": (
            "https://www.gyeongnam.go.kr/board/list.gyeong?"
            "boardId=BBS_0000957&menuCd=DOM_000000138002012000&contentsSid=9918&cpath="
        ),
        "fileKinds": ["xlsx"],
        "pageParam": "pageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "상세 화면이 해당 저작물의 자유이용을 불가한다고 표시해 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    "경상남도의회": {
        "sourceUrl": (
            "https://council.gyeongnam.go.kr/kr/data/bbsExpense.do?"
            "flag=&keyword=&pageNum=1&reform=list"
        ),
        "fileKinds": ["pdf"],
        "pageParam": "pageNum",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    "울산시청": {
        "sourceUrl": "https://www.ulsan.go.kr/u/rep/transfer/chief/list.ulsan?mId=001003002005000000",
        "fileKinds": ["html"],
        "pageParam": "curPage",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서장 업무추진비 목록과 HTML 상세 표 구조는 확인했습니다. 상세 표는 "
            "사용일자·결제내용·결제방법·인원·금액·참석대상·장소를 제공하지만, 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 "
            "확인 전까지 수집하지 않습니다."
        ),
    },
    "울산시의회": {
        "sourceUrl": "https://council.ulsan.kr/cop/bbs/selectBoardList.do?bbsId=bizExpStatus",
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행 현황 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
}

NON_CAPITAL_REGIONAL_OFFICE_ATTACHMENT_BOARDS = {
    "대전시청": {
        "homepage": "https://www.daejeon.go.kr",
        "listUrl": "https://www.daejeon.go.kr/drh/open/drhDataOpen/drhDataOpenBoardView.do?boardSeq=747&menuSeq=4804",
        "fileKinds": ["xlsx"],
        "followDetail": True,
        "pageParam": "subPageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면 확인",
    },
    "전라남도청": {
        "homepage": "https://www.jeonnam.go.kr",
        "listUrl": "https://www.jeonnam.go.kr/M1925005/boardList.do?menuId=jeonnam0302050100",
        "fileKinds": ["hwp"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "제주특별자치도청": {
        "homepage": "https://www.jeju.go.kr",
        "listUrl": "https://www.jeju.go.kr/open/open/work/work2.htm?category=1409",
        "extraListUrls": [
            "https://www.jeju.go.kr/open/open/work/work1.htm?category=1003",
        ],
        "fileKinds": ["xlsx", "xls"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 재확인",
        "evidenceNote": (
            "공식 원문은 제주넷 정보공개 > 업무추진비 공개의 도 본청 업무추진비 "
            "(https://www.jeju.go.kr/open/open/work/work2.htm?category=1409)와 도지사·부지사 "
            "업무추진비(https://www.jeju.go.kr/open/open/work/work1.htm?category=1003)입니다. "
            "목록·상세에서 act=view 및 act=download XLS/XLSX 첨부 구조를 확인했습니다. "
            "제주특별자치도 공개 자료는 「지방자치단체 업무추진비 집행에 관한 규칙」과 "
            "「제주특별자치도 행정정보공개에 관한 조례」 제7조에 따라 월 1회 홈페이지 공개되는 "
            "행정정보이며, 제주넷 저작권보호정책(https://www.jeju.go.kr/help/policy/copyright.htm)과 "
            "공공저작물 이용안내(https://www.jeju.go.kr/open/publicmedia/use.htm)는 "
            "저작권법 제24조의2 및 공공누리 표시 공공저작물의 자유이용, 제1유형의 출처표시 "
            "자유이용을 안내합니다. 공무원맵은 출처표시 조건으로 법정 공개 사실 데이터만 "
            "정규화합니다."
        ),
    },
}

NON_CAPITAL_REGIONAL_COUNCIL_ATTACHMENT_BOARDS = {
    "대전시의회": {
        "homepage": "https://council.daejeon.go.kr",
        "listUrl": "https://council.daejeon.go.kr/svc/inf/OperatingExpenseList.do",
        "fileKinds": ["pdf"],
        "followDetail": True,
        "pageParam": "pageNo",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면 확인",
    },
    "제주특별자치도의회": {
        "homepage": "https://www.council.jeju.kr",
        "listUrl": "https://www.council.jeju.kr/clicknews/openpromotion.do",
        "extraListUrls": [
            "https://www.council.jeju.kr/notice/informationdisclosure/operations/expenses.do",
        ],
        "fileKinds": ["xlsx", "xls"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 재확인",
        "evidenceNote": (
            "공식 원문은 제주특별자치도의회 자료실 > 업무추진비공개 "
            "(https://www.council.jeju.kr/clicknews/openpromotion.do)와 알림마당 > 의정활동정보공개 "
            "> 의회운영 > 업무추진비 현황 "
            "(https://www.council.jeju.kr/notice/informationdisclosure/operations/expenses.do)입니다. "
            "목록 act=view, 상세 act=down XLS/XLSX 첨부 구조와 의장·부의장·전문위원 부서장 "
            "업무추진비, 의회운영업무추진비, 의정운영공통경비 파일을 확인했습니다. "
            "의회 이용약관(https://www.council.jeju.kr/help/terms.do)은 홈페이지 및 모바일서비스에 "
            "제주넷 이용약관이 적용된다고 안내하며, 제주넷 저작권보호정책과 공공저작물 "
            "이용안내는 저작권법 제24조의2 및 공공누리 표시 공공저작물의 자유이용, 제1유형의 "
            "출처표시 자유이용을 안내합니다. 공무원맵은 출처표시 조건으로 법정 공개 사실 "
            "데이터만 정규화합니다."
        ),
    },
}

JEJU_ADMINISTRATIVE_CITY_OFFICE_ATTACHMENT_BOARDS = {
    "제주시청": {
        "homepage": "https://www.jejusi.go.kr",
        "listUrl": "https://www.jejusi.go.kr/information/status/sijang.do",
        "extraListUrls": [
            "https://www.jejusi.go.kr/information/status/part.do",
        ],
        "fileKinds": ["xls", "xlsx"],
        "followDetail": True,
        "pageParam": "currentPageNo",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "evidenceNote": (
            "제주특별자치도 산하 행정시로 별도 지방의회는 없지만, 사용자 기준 제주 행정구역 "
            "공개 업무추진비를 포함하기 위해 P1 행정기관으로 등록합니다. 공식 원문은 제주시 "
            "정보공개 > 업무추진비 공개의 제주시장 업무추진비 공개 "
            "(https://www.jejusi.go.kr/information/status/sijang.do)와 부서별 업무추진비 공개 "
            "(https://www.jejusi.go.kr/information/status/part.do)입니다. 목록에서 "
            "mode=detail&notice_id 상세, 상세에서 /boardFileDown.ac?file_id= XLS/XLSX 첨부 "
            "구조를 확인했습니다. 부서별 업무추진비 공개 화면은 공개 근거를 "
            "「제주특별자치도 업무추진비 집행기준 및 공개에 관한 조례(2022.1.12.)」로 "
            "명시합니다. 제주시 저작권보호정책 "
            "(https://www.jejusi.go.kr/guide/copyrights.do)은 저작권법 제24조의2 및 공공누리 "
            "표시 공공저작물의 자유이용, 제1유형의 출처표시·상업적 이용 가능 조건을 안내합니다. "
            "공무원맵은 출처표시 조건으로 법정 공개 사실 데이터만 정규화합니다."
        ),
    },
    "서귀포시청": {
        "homepage": "https://www.seogwipo.go.kr",
        "listUrl": "https://www.seogwipo.go.kr/info/gov/open/expense.htm",
        "fileKinds": ["xls", "xlsx"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "evidenceNote": (
            "제주특별자치도 산하 행정시로 별도 지방의회는 없지만, 사용자 기준 제주 행정구역 "
            "공개 업무추진비를 포함하기 위해 P1 행정기관으로 등록합니다. 공식 원문은 서귀포시 "
            "시정공유 > 행정정보공개 > 사전정보공개 > 업무추진비공개 "
            "(https://www.seogwipo.go.kr/info/gov/open/expense.htm)입니다. 목록·상세에서 "
            "act=view 및 act=download&seq=&no= XLS/XLSX/PDF 첨부 구조를 확인했고, production "
            "경로는 PDF vision 리스크를 피하기 위해 XLS/XLSX 첨부만 처리합니다. 해당 화면은 "
            "공개 항목과 근거를 「제주특별자치도 업무추진비 집행기준 및 공개에 관한 조례」로 "
            "명시합니다. 서귀포시 저작권보호정책 "
            "(https://www.seogwipo.go.kr/help/copyright.htm)은 저작권법 제24조의2 및 공공누리 "
            "표시 공공저작물의 자유이용, 제1유형의 출처표시·상업적 이용 가능 조건을 안내합니다. "
            "공무원맵은 출처표시 조건으로 법정 공개 사실 데이터만 정규화합니다."
        ),
    },
}

NON_CAPITAL_BASIC_OFFICE_ATTACHMENT_BOARDS = {
    ("강원특별자치도", "영월군청"): {
        "homepage": "https://www.yw.go.kr",
        "listUrl": "https://www.yw.go.kr/www/selectBbsNttList.do?bbsNo=7&key=196",
        "fileKinds": ["xlsx"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("충청남도", "보령시청"): {
        "homepage": "https://www.brcn.go.kr",
        "listUrl": (
            "https://www.brcn.go.kr/cop/bbs/BBSMSTR_000000000386/selectBoardList.do?"
            "bbsId=BBSMSTR_000000000386"
        ),
        "fileKinds": ["xls", "xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("충청남도", "서산시청"): {
        "homepage": "https://www.seosan.go.kr",
        "listUrl": "https://www.seosan.go.kr/www/selectBbsNttList.do?bbsNo=114&key=1278",
        "fileKinds": ["hwp", "xlsx", "xls"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("경상북도", "구미시청"): {
        "homepage": "https://www.gumi.go.kr",
        "listUrl": (
            "https://www.gumi.go.kr/portal/board/post/list.do?"
            "bcIdx=164&mid=0303100000"
        ),
        "fileKinds": ["xlsx", "xls"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("경상남도", "밀양시청"): {
        "homepage": "https://www.miryang.go.kr",
        "listUrl": (
            "https://www.miryang.go.kr/twn/bbs/selectBoardList.do?"
            "bbsId=BBSMSTR_000000085910&mnNo=3040000&owd=sammun"
        ),
        "fileKinds": ["xlsx"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("경상남도", "창원시청"): {
        "homepage": "https://www.changwon.go.kr",
        "listUrl": "https://www.changwon.go.kr/cwportal/10312/10620/10629.web?gcode=1036",
        "fileKinds": ["xlsx", "pdf"],
        "followDetail": True,
        "pageParam": "cpage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("대구광역시", "군위군청"): {
        "homepage": "https://www.gunwi.go.kr",
        "listUrl": "https://www.gunwi.go.kr/ko/page.do?mnu_uid=160",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "followDetail": True,
        "pageParam": "pageNo",
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("전라남도", "곡성군청"): {
        "homepage": "https://www.gokseong.go.kr",
        "listUrl": (
            "https://www.gokseong.go.kr/kr/board/list.do?"
            "bbsId=BBS_000000000000540&menuNo=102006001000"
        ),
        "extraListUrls": [
            (
                "https://www.gokseong.go.kr/kr/board/list.do?"
                "bbsId=BBS_000000000000541&menuNo=102006002000"
            ),
            (
                "https://www.gokseong.go.kr/kr/board/list.do?"
                "bbsId=BBS_000000000000542&menuNo=102006003000"
            ),
        ],
        "fileKinds": ["pdf", "xlsx"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "jsDownloadPath": "/board/FileDown.do",
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    ("전라남도", "진도군청"): {
        "homepage": "https://www.jindo.go.kr",
        "listUrl": "https://www.jindo.go.kr/home/board/B0071.cs?m=52",
        "fileKinds": ["pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "userAgent": (
            "Mozilla/5.0 (compatible; PublicOfficerMapBot/0.1; "
            "+mailto:wylee0806@naver.com)"
        ),
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
}

NON_CAPITAL_BASIC_COUNCIL_ATTACHMENT_BOARDS = {
    ("전라남도", "곡성군의회"): {
        "homepage": "https://www.gokseong.go.kr",
        "listUrl": (
            "https://www.gokseong.go.kr/council/board/list.do?"
            "bbsId=BBS_000000000000380&menuNo=106005004000"
        ),
        "fileKinds": ["pdf"],
        "followDetail": True,
        "pageParam": "pageIndex",
        "jsDownloadPath": "/board/FileDown.do",
        "userAgent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
}

NON_CAPITAL_BASIC_LEGAL_HOLD_BLOCKERS = {
    ("강원특별자치도", "춘천시청"): {
        "sourceUrl": "https://www.chuncheon.go.kr/cityhall/information-disclosure/business-expenses/chuncheon-cityhall",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 춘천시청 업무추진비 집행내역 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "춘천시의회"): {
        "sourceUrl": "https://council.chuncheon.go.kr/basic/view.do?b=50&k=2479&n=682&pu=10&sortField=RGSDE",
        "fileKinds": ["pdf"],
        "pageParam": "p",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 춘천시의회 업무추진비 현황 상세와 PDF 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "원주시청"): {
        "sourceUrl": "https://www.wonju.go.kr/www/selectBbsNttList.do?bbsNo=1095&integrDeptCode=&key=5126&pageUnit=20",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 원주시청 업무추진비 공개 목록과 PDF/XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "원주시의회"): {
        "sourceUrl": "https://council.wonju.go.kr/content/info/releaseInformation.html",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 원주시의회 업무추진비 현황 목록과 분기별 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 All rights reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "강릉시청"): {
        "sourceUrl": "https://www.gn.go.kr/www/selectBbsNttList.do?bbsNo=4&key=20",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 강릉시청 업무추진비 목록과 첨부 구조는 확인했습니다. 다만 확인 가능한 "
            "저작권 표시는 공공누리 제4유형으로 상업적 이용이 금지되므로 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "강릉시의회"): {
        "sourceUrl": "https://www.gncl.go.kr/kr/bbs?bbs_id=open",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 강릉시의회 업무추진비/정보공개 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "동해시청"): {
        "sourceUrl": "https://www.dh.go.kr/www/selectBbsNttList.do?bbsNo=67&key=237",
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 동해시청 업무추진비 목록과 월별 PDF 첨부 구조는 확인했습니다. 다만 "
            "목록 원문에서 koglUseAt=N 및 koglTy=SITE_DEFAULT로 표시되고 푸터가 "
            "ALL RIGHTS RESERVED이므로 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "동해시의회"): {
        "sourceUrl": "https://www.dhcc.go.kr/content/public/infoOpen_council.html",
        "fileKinds": ["html", "pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 동해시의회 의정활동 정보공개 업무추진비 현황 경로는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 저작권 보유 표기 중심이므로 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "태백시청"): {
        "sourceUrl": "https://www.taebaek.go.kr/www/selectBbsNttList.do?bbsNo=132&key=1552",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 태백시청 업무추진비 목록과 PDF 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않아 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "태백시의회"): {
        "holdStatus": "legal_hold",
        "sourceUrl": "https://council.taebaek.go.kr/source/kr/news/info2.html",
        "detailUrl": "https://council.taebaek.go.kr/source/kr/news/info2.html?mode=view&number=112",
        "attachmentUrl": (
            "https://council.taebaek.go.kr/Mboard/download.html?"
            "table=board_official&column=userfile&uid=112"
        ),
        "copyrightUrl": "https://www.taebaek.go.kr/www/sub.do?key=590",
        "publicWorksPolicyUrl": "https://www.taebaek.go.kr/www/sub.do?key=590",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 재확인",
        "commercialUseStatus": "not_confirmed_without_kogl_mark",
        "derivativeUseStatus": "not_confirmed_without_kogl_mark",
        "blocker": (
            "공식 태백시의회 정보공개 업무추진비 현황 목록"
            "(https://council.taebaek.go.kr/source/kr/news/info2.html), 2026년 4월 상세"
            "(https://council.taebaek.go.kr/source/kr/news/info2.html?mode=view&number=112), "
            "XLSX 첨부 다운로드 구조는 확인했습니다. 다만 목록/상세 화면에 공공누리 "
            "제1유형 또는 명확한 상업적 자유이용 표시가 없고, 태백시 저작권정책"
            "(https://www.taebaek.go.kr/www/sub.do?key=590)은 공공누리가 부착되지 않은 "
            "자료는 자료관리부서 사전 협의 후 이용하라고 안내하며 의회 푸터도 ALL RIGHTS "
            "RESERVED로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "속초시청"): {
        "sourceUrl": "https://www.sokcho.go.kr/sc/portal/adminfo/disclosure/expense/mayor",
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": False,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 속초시청 시장·부시장 업무추진비 목록과 XLSX 직접 다운로드 구조는 확인했습니다. "
            "다만 목록 화면에 공공누리 표시가 없고, 저작권정책은 KOGL이 부착된 저작물만 "
            "자유이용 가능하다고 안내하므로 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "속초시의회"): {
        "sourceUrl": "https://www.sokchocl.go.kr/kr/news/bbsCost.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 속초시의회 업무추진비 공개 목록과 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않아 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "삼척시청"): {
        "sourceUrl": "https://www.samcheok.go.kr/02815.web?gcode=1321",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "cpage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 삼척시청 업무추진비 공개 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "삼척시의회"): {
        "sourceUrl": "https://www.sccl.go.kr/kr/bbs?bbs_id=business&flag=&keyword=&list_style=&page=1&reform=list&search_code=",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 삼척시의회 업무추진비 현황 목록과 첨부 구조는 확인했습니다. 다만 푸터가 "
            "All rights reserved로 표시되고 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "홍천군청"): {
        "sourceUrl": "https://www.hongcheon.go.kr/www/selectBbsNttList.do?bbsNo=61&key=175",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 홍천군청 업무추진비 목록과 XLS/XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "홍천군의회"): {
        "sourceUrl": "https://www.hccouncil.go.kr/council/kr/costBBS.do",
        "fileKinds": ["xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 홍천군의회 업무추진비 현황 목록과 XLS/PDF 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 ALL RIGHTS RESERVED로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "횡성군청"): {
        "sourceUrl": "https://www.hsg.go.kr/www/selectBbsNttList.do?bbsNo=79&key=909",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 횡성군청 업무추진비공개 목록과 최근 게시 구조는 확인했습니다. 다만 공공누리 "
            "영역이 비어 있고 푸터가 All rights reserved로 표시되어 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "횡성군의회"): {
        "holdStatus": "legal_hold",
        "sourceUrl": "https://www.hsg.go.kr/council/selectBbsNttList.do?bbsNo=41&key=1464&",
        "detailUrl": (
            "https://www.hsg.go.kr/council/selectBbsNttView.do?"
            "key=1464&bbsNo=41&nttNo=421094&pageUnit=10&searchCnd=all"
        ),
        "attachmentUrl": "https://www.hsg.go.kr/council/downloadBbsFile.do?atchmnflNo=547678",
        "copyrightUrl": "https://www.hsg.go.kr/www/contents.do?key=906",
        "publicWorksPolicyUrl": "https://www.hsg.go.kr/www/contents.do?key=906",
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 재확인",
        "commercialUseStatus": "not_confirmed_without_kogl_mark",
        "derivativeUseStatus": "not_confirmed_without_kogl_mark",
        "blocker": (
            "횡성군의회 공식 경로가 횡성군 통합 도메인"
            "(https://www.hsg.go.kr/council/index.do)으로 확인되었고, 통합검색의 "
            "업무추진비 집행 현황 메뉴"
            "(https://www.hsg.go.kr/council/selectBbsNttList.do?bbsNo=41&key=1464&)와 "
            "2026년 4월 상세, PDF 첨부 다운로드 구조를 확인했습니다. 다만 목록/상세 화면의 "
            "공공누리 영역이 비어 있고, 횡성군 공공저작물 자유이용 정책"
            "(https://www.hsg.go.kr/www/contents.do?key=906)은 공공누리가 부착되지 않은 "
            "자료는 담당자 사전 협의 후 이용하라고 안내하며 푸터가 All rights reserved로 "
            "표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "영월군의회"): {
        "sourceUrl": "https://council.yw.go.kr/content/news/info.html",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 영월군의회 정보공개 목록에서 분기별 업무추진비 및 의정운영공통경비 "
            "사용내역 게시글은 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 "
            "명확한 상업적 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "평창군청"): {
        "sourceUrl": "https://www.pc.go.kr/portal/info/info-finance/info-finance-history",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 평창군청 업무추진비 집행내역 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 저작권 보유 표기만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "평창군의회"): {
        "sourceUrl": "https://cl.happy700.or.kr/kr/activity/bbsCost.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 평창군의회 업무추진비 목록과 분기별 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 ALL RIGHTS RESERVED로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "정선군청"): {
        "sourceUrl": "https://www.jeongseon.go.kr/portal/admininfo/openinfo/expense",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 정선군청 업무추진비 공개 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "정선군의회"): {
        "sourceUrl": "https://assembly.jeongseon.go.kr/source/kr/info/info3.html?table=board_business",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 정선군의회 업무추진비 목록과 XLSX 첨부 구조는 확인했습니다. 다만 푸터가 "
            "all rights reserved로 표시되고 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "철원군청"): {
        "sourceUrl": "https://www.cwg.go.kr/www/selectBbsNttList.do?bbsNo=36&key=1595",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 철원군청 업무추진비 목록과 XLSX 첨부 구조는 확인했습니다. 다만 최근 12개월 "
            "게시 지속성과 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "철원군의회"): {
        "sourceUrl": "https://council.cwg.go.kr/council/selectBbsNttList.do?bbsNo=69&key=529",
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 철원군의회 업무추진비 사용내역 목록과 월별 PDF 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않고 푸터가 ALL RIGHT RESERVED로 표시되어 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "화천군청"): {
        "sourceUrl": "https://www.ihc.go.kr/www/selectBbsNttList.do?bbsNo=106&key=2424",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 화천군청 업무추진비 집행내역 목록과 첨부 구조는 확인했습니다. 다만 푸터가 "
            "ALL RIGHTS RESERVED로 표시되고 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "화천군의회"): {
        "sourceUrl": "https://council.ihc.go.kr/bbs/board.php?bo_table=sub06_7",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 화천군의회 업무추진비 사용내역 목록과 PDF 첨부 구조는 확인했습니다. 다만 "
            "푸터가 All rights reserved로 표시되고 공공누리 제1유형 또는 명확한 상업적 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "양구군청"): {
        "sourceUrl": "https://www.yanggu.go.kr/user_sub?gfnc=www&mu_idx=201",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 양구군청 업무추진비 공개 목록과 최근 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 All rights reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "양구군의회"): {
        "holdStatus": "no_recent_data",
        "sourceUrl": "http://www.ygcl.go.kr/portal/F50000/F50700/boardList",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 양구군의회 업무추진비 집행 현황 목록은 확인했지만 원문 기준 총 0개의 글로 "
            "최근 12개월 집행내역 게시글이 없습니다. 2020년 이후 확장 검색에서도 현행 "
            "업무추진비 메뉴는 동일한 빈 목록이며, 확인된 F80000/F80200/F80208 메뉴는 "
            "업무추진비가 아니라 의원별 회의 출석율 현황으로 확인되어 데이터가 공개될 때까지 "
            "수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "인제군청"): {
        "sourceUrl": "https://www.inje.go.kr/portal/adm/public/operatingexpense",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 인제군청 업무추진비 집행내역 목록과 XLSX 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "인제군의회"): {
        "sourceUrl": "https://www.injecl.go.kr/content/info/expense.html",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 인제군의회 업무추진비 공개 목록과 분기별 PDF 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 "
            "않고 푸터가 All rights reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "고성군청"): {
        "sourceUrl": "https://www.gwgs.go.kr/prog/bbsArticle/BBSMSTR_000000001005/list.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 고성군청 정보공개 예산정보 업무추진비 목록과 XLSX/PDF 첨부 구조는 확인했습니다. "
            "다만 목록 화면은 공공누리 유형 영역이 비어 있고 저작권정책은 공공누리가 부착되지 "
            "않은 자료는 담당자 사전 협의 후 이용하라고 안내하므로 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "고성군의회"): {
        "sourceUrl": "https://council.gwgs.go.kr/Home/H30000/H30500/boardList",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 고성군의회 정보공개 업무추진비 집행 현황 목록과 첨부 구조는 확인했습니다. "
            "다만 푸터가 ALL RIGHT RESERVED로 표시되고 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "양양군청"): {
        "sourceUrl": "https://yangyang.go.kr/gw/portal/yyc_opinfo_adinfo_disclosure",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 양양군청 업무추진비 공개 경로와 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않아 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("강원특별자치도", "양양군의회"): {
        "sourceUrl": "https://www.yangyangcouncil.go.kr/kr/costBBS.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 양양군의회 업무추진비공개 목록과 첨부 구조는 확인했습니다. 다만 푸터가 "
            "ALL RIGHTS RESERVED로 표시되고 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "동구청"): {
        "sourceUrl": "https://www.donggu.go.kr/dg/kor/article/senior",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 5급 이상 업무추진비 목록(https://www.donggu.go.kr/dg/kor/article/senior)과 "
            "단체장 업무추진비 목록(https://www.donggu.go.kr/dg/kor/article/secretBusiness), "
            "첨부 구조는 확인했습니다. 다만 업무추진비 목록 화면에는 공공누리 유형 표시가 "
            "직접 확인되지 않고, 대전 동구 공공누리 안내는 공공누리가 부착되지 않은 자료는 "
            "공공저작물 담당자와 사전 협의하라고 안내하므로 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "동구의회"): {
        "sourceUrl": (
            "https://council.donggu.go.kr/kr/open/bbs?"
            "bbs_id=cost&filter=latest&flag=&keyword=&list_style=&page=1&reform=list&search_code=council"
        ),
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 XLSX 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("대전광역시", "중구청"): {
        "sourceUrl": "https://www.djjunggu.go.kr/bbs/BBSMSTR_000000000105/list.do",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서별 업무추진비 목록과 XLSX 직접 다운로드 구조는 확인했습니다. 다만 목록 화면에는 "
            "공공누리 유형 표시가 직접 확인되지 않고, 대전 중구 저작권정책은 공공누리가 부착되지 "
            "않은 자료는 담당자와 사전 협의하라고 안내하므로 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "중구의회"): {
        "sourceUrl": "https://council.djjunggu.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행 현황 목록과 XLSX 직접 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "서구청"): {
        "sourceUrl": "https://www.seogu.go.kr/bbs/BBSMSTR_000000000263/list.do",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서별 업무추진비 목록과 XLSX 첨부 구조는 확인했습니다. 다만 업무추진비 목록 화면에는 "
            "공공누리 유형 표시가 직접 확인되지 않고, 대전 서구 공공저작물 개방 안내는 공공누리가 "
            "부착되지 않은 자료는 담당자와 사전 협의하라고 안내하므로 제1유형 확인 전까지 수집하지 "
            "않습니다."
        ),
    },
    ("대전광역시", "유성구청"): {
        "sourceUrl": "https://www.yuseong.go.kr/bbs/BBSMSTR_000000000111/list.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 단체장 업무추진비 목록(https://www.yuseong.go.kr/bbs/BBSMSTR_000000000111/list.do), "
            "부서별 업무추진비 목록(https://www.yuseong.go.kr/bbs/BBSMSTR_000000000115/list.do), "
            "PDF/XLSX 다운로드 구조는 확인했습니다. 다만 업무추진비 목록 화면에서 공공누리 제1유형 "
            "또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "유성구의회"): {
        "sourceUrl": (
            "https://yuseonggucouncil.go.kr/bbs/board.php?"
            "bo_table=0603&page=1&sod=asc&sop=and&sst=wr_datetime"
        ),
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 XLS/XLSX 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("대전광역시", "대덕구청"): {
        "sourceUrl": "https://www.daedeok.go.kr/dpt/dpt02/DPT02010401_cmmBoardList.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 단체장 업무추진비 목록(https://www.daedeok.go.kr/dpt/dpt02/DPT02010401_cmmBoardList.do), "
            "부서장 업무추진비 목록(https://www.daedeok.go.kr/dpt/dpt02/DPT02010404_cmmBoardList.do), "
            "PDF 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 "
            "자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대전광역시", "대덕구의회"): {
        "sourceUrl": "https://council.daedeok.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 XLSX 직접 다운로드 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "천안시청"): {
        "sourceUrl": "https://www.cheonan.go.kr/bbs/BBSMSTR_000000000050/list.do",
        "fileKinds": ["xlsx", "xls", "pdf", "hwp", "hwpx", "zip"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·XLSX/XLS/PDF/HWP/HWPX/ZIP 다운로드 구조는 "
            "확인했습니다. 다만 업무추진비 목록/상세 화면에서 공공누리 제1유형 또는 명확한 "
            "자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "천안시의회"): {
        "sourceUrl": "https://www.cheonancouncil.go.kr/svc/ctz/councilExpenseList.do",
        "fileKinds": ["xlsx"],
        "pageParam": "schPageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "공주시청"): {
        "sourceUrl": "https://www.gongju.go.kr/bbs/BBSMSTR_000000000793/list.do",
        "fileKinds": ["xlsx", "xls", "hwp"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·XLSX/XLS/HWP 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "공주시의회"): {
        "sourceUrl": "https://council.gongju.go.kr/bbs/BBSMSTR_000000000882/list.do",
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "부여군청"): {
        "sourceUrl": "https://www.buyeo.go.kr/_prog/_board/?code=service_010211&site_dvs_cd=kr&menu_dvs_cd=010211",
        "fileKinds": ["hwp"],
        "pageParam": "GotoPage",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·HWP 다운로드 링크 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 "
            "저작권정책 링크와 저작권 문구만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "부여군의회"): {
        "sourceUrl": "https://council.buyeo.go.kr/kr/open/bbsBusiness.do",
        "fileKinds": ["pdf", "zip"],
        "pageParam": "pageNum",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역 목록과 목록 ZIP 다운로드, 상세·PDF 다운로드 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않고 저작권 문구만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "논산시청"): {
        "sourceUrl": "https://www.nonsan.go.kr/kor/html/sub03/03080803.html?GotoPage=1&mode=L",
        "fileKinds": ["pdf", "hwp", "xlsx", "xls"],
        "pageParam": "GotoPage",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 상세·PDF/HWP/엑셀 첨부 구조는 확인했습니다. 다만 "
            "목록 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 "
            "저작권정책 링크만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "논산시의회"): {
        "sourceUrl": "https://www.nonsancl.go.kr/kr/activity/bbs?bbs_id=expense",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 첨부 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "보령시의회"): {
        "sourceUrl": "https://www.brcouncil.go.kr/kr/costBBS.do",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 12개월 게시물·PDF/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "아산시청"): {
        "sourceUrl": "https://www.asan.go.kr/main/cms/?m_mode=list&no=335&tb_nm=dep_expense",
        "fileKinds": ["xlsx", "hwpx", "pdf"],
        "pageParam": "PageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 12개월 게시물·XLSX/HWPX/PDF 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "계룡시청"): {
        "sourceUrl": "https://gyeryong.go.kr/kr/html/sub02/020204.html?GotoPage=1&mode=L",
        "fileKinds": ["xlsx", "pdf"],
        "pageParam": "GotoPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 12개월 게시물·XLSX/PDF 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "계룡시의회"): {
        "sourceUrl": "https://gyeryong.go.kr/council/html/sub04/040401.html?GotoPage=0&mode=L",
        "fileKinds": ["pdf"],
        "pageParam": "GotoPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역 목록과 최근 12개월 게시물·PDF 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "당진시청"): {
        "sourceUrl": "https://www.dangjin.go.kr/cop/bbs/BBSMSTR_000000000024/selectBoardList.do",
        "fileKinds": ["xlsx", "pdf", "hwp", "hwpx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 12개월 게시물·XLSX/PDF/HWP/HWPX 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "당진시의회"): {
        "sourceUrl": "https://council.dangjin.go.kr/content/data/businessOperatingExpense.html",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역 목록과 최근 12개월 게시물·XLSX/PDF 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "금산군의회"): {
        "sourceUrl": "https://www.geumsancouncil.go.kr/content/info/expenses.html",
        "extraListUrls": ["https://www.geumsancouncil.go.kr/content/council/chairmanMovements.html"],
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역과 의장 업무추진비 공개 경로, 최근 12개월 게시물·XLSX "
            "첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 "
            "명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "서천군청"): {
        "sourceUrl": "https://seocheon.go.kr/cop/bbs/BBSMSTR_000000000102/selectBoardList.do",
        "extraListUrls": [
            "https://seocheon.go.kr/cop/bbs/BBSMSTR_000000000673/selectBoardList.do"
        ],
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 군수 업무추진비와 부서장 업무추진비 공개 목록, 최근 12개월 게시물·PDF "
            "첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 "
            "명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "홍성군의회"): {
        "sourceUrl": "https://council.hongseong.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행현황 목록과 최근 12개월 게시물·XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "예산군청"): {
        "sourceUrl": "https://www.yesan.go.kr/bbs/BBSMSTR_000000000033/list.do",
        "extraListUrls": ["https://www.yesan.go.kr/bbs/BBSMSTR_000000000173/list.do"],
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역과 기관장 업무추진비 공개 목록, 최근 12개월 게시물·XLSX/PDF "
            "첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 "
            "명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "예산군의회"): {
        "sourceUrl": "https://www.councilyesan.go.kr/kr/activity/bbs?bbs_id=work",
        "fileKinds": ["xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 게시판과 최근 12개월 게시물·XLS 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청남도", "태안군청"): {
        "sourceUrl": "https://www.taean.go.kr/cop/bbs/BBSMSTR_000000000321/selectBoardList.do",
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 게시판과 최근 12개월 게시물·PDF 첨부 구조는 확인했습니다. "
            "다만 상세 화면이 공공누리 제4유형으로 표시되어 상업적 이용과 변경이 모두 "
            "제한되므로 수집하지 않습니다."
        ),
    },
    ("충청남도", "태안군의회"): {
        "sourceUrl": "https://council.taean.go.kr/main/index.php?m_cd=20",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 12개월 게시물·PDF/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "금정구청"): {
        "sourceUrl": (
            "https://www.geumjeong.go.kr/board/list.geumj?"
            "boardId=BBS_0000331&menuCd=DOM_000000124001011000&orderBy=REGISTER_DATE+DESC"
        ),
        "fileKinds": ["hwpx", "xlsx"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·HWPX/XLSX 첨부 구조는 확인했습니다. 다만 "
            "상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 "
            "표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "서구청"): {
        "holdStatus": "adapter_hold",
        "sourceUrl": "https://www.bsseogu.go.kr/index.bsseogu?menuCd=DOM_000001501004000000",
        "fileKinds": ["hwp"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·HWP 첨부 구조 및 목록 하단 공공누리 제1유형 "
            "표시는 확인했습니다. 다만 현재 pipeline은 HWP 본문 추출을 지원하지 않고 "
            "HWPX/XLS/XLSX/PDF만 처리하므로 HWP extractor 또는 변환 adapter가 구현되기 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "남구청"): {
        "sourceUrl": (
            "https://www.bsnamgu.go.kr/board/list.namgu?"
            "boardId=BBS_0000149&menuCd=DOM_000000105005009000"
        ),
        "extraListUrls": [
            (
                "https://www.bsnamgu.go.kr/board/list.namgu?"
                "boardId=BBS_0000342&menuCd=DOM_000000105005009000"
            )
        ],
        "fileKinds": ["xlsx"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서 업무추진비와 국장급 이상 업무추진비 목록, 상세·XLSX 다운로드 구조는 "
            "확인했습니다. 다만 업무추진비 목록/상세 자체에서는 공공누리 제1유형 또는 "
            "명확한 상업적 자유이용 표시가 확인되지 않고 푸터 저작권 문구만 확인되어 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "남구의회"): {
        "sourceUrl": "https://council.bsnamgu.go.kr/kr/activity/bbs?bbs_id=notice2",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 등 공개 목록과 최근 12개월 게시물·XLSX 첨부 구조는 확인했습니다. "
            "다만 목록 화면의 공공누리 영역에 유형 표시가 노출되지 않아 제1유형 또는 "
            "명확한 자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "동구청"): {
        "sourceUrl": "https://www.bsdonggu.go.kr/index.donggu?menuCd=DOM_000000103005011000",
        "fileKinds": ["pdf"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 2026년 게시물·PDF 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면이 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 "
            "표시되어 상업적 이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("부산광역시", "동구의회"): {
        "sourceUrl": (
            "https://www.bsdonggu.go.kr/council/board/list.donggu?"
            "boardId=BBS_0000260&contentsSid=1247&cpath=%2Fcouncil&"
            "menuCd=DOM_000000506004000000"
        ),
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 의장단 업무추진비 공개 목록과 최근 분기별 첨부 구조는 확인했습니다. "
            "다만 목록 화면이 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 "
            "표시되어 상업적 이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("부산광역시", "영도구청"): {
        "sourceUrl": "https://www.yeongdo.go.kr/00000/00067/00333.web",
        "extraListUrls": ["https://www.yeongdo.go.kr/00492/00493/00498.web"],
        "fileKinds": ["xls", "xlsx"],
        "pageParam": "cpage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서 업무추진비와 구청장 업무추진비 공개 목록, 최근 XLS/XLSX 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않고 푸터가 All Rights Reserved로 표시되어 제1유형 "
            "확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "부산진구청"): {
        "sourceUrl": (
            "https://www.busanjin.go.kr/board/list.busanjin?"
            "boardId=BBS_0000023&menuCd=DOM_000000109001003000&contentsSid=276"
        ),
        "fileKinds": ["xlsx"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 첨부 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않고 "
            "푸터가 All Rights Reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "동래구의회"): {
        "sourceUrl": "https://council.dongnae.go.kr/source/kr/news/business.html",
        "fileKinds": ["xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·XLS 첨부 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않고 "
            "푸터가 All Rights Reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "해운대구청"): {
        "sourceUrl": "https://www.haeundae.go.kr/index.do?menuCd=DOM_000000104004003000",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 2026년 게시물·첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않고 푸터가 All rights reserved로 표시되어 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("부산광역시", "사하구청"): {
        "sourceUrl": "https://www.saha.go.kr/portal/contents.do?mId=0302070000",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 게시물·첨부 구조는 확인했습니다. 다만 업무추진비 "
            "목록/상세에는 공공누리 제1유형 표시가 확인되지 않고, 저작권정책은 공공누리 "
            "부착 저작물만 이용조건 범위 안에서 자유이용 가능하다고 안내하므로 제1유형 "
            "확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "사하구의회"): {
        "sourceUrl": "https://www.saha.go.kr/council/contents.do?mId=0507000000",
        "fileKinds": ["xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 의회운영업무추진비 공개 목록과 분기별 XLS 첨부 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않고 저작권정책 링크만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "수영구청"): {
        "sourceUrl": (
            "https://www.suyeong.go.kr/welfare/board/list.suyeong?"
            "boardId=BBS_0000116&categoryCode1=9901000000000&"
            "menuCd=DOM_000000103004003000&paging=ok&startPage=1"
        ),
        "fileKinds": ["xlsx", "xls", "pdf", "html"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 2026년 게시물 구조는 확인했습니다. 다만 목록 화면이 "
            "공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 표시되어 상업적 "
            "이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("부산광역시", "사상구청"): {
        "sourceUrl": (
            "https://www.sasang.go.kr/board/list.sasang?"
            "boardId=BBS_0000175&menuCd=DOM_000000101002007000&"
            "orderBy=REGISTER_DATE+DESC&startPage=1"
        ),
        "extraListUrls": [
            (
                "https://www.sasang.go.kr/board/list.sasang?"
                "boardId=BBS_0000084&menuCd=DOM_000000101002011000&startPage=1"
            )
        ],
        "fileKinds": ["hwpx", "xlsx", "xls"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서 업무추진비와 구청장 업무추진비 공개 목록, 상세·HWPX 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않고 저작권 보호정책 링크만 확인되어 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "중구청"): {
        "sourceUrl": "https://www.bsjunggu.go.kr/index.junggu?menuCd=DOM_000000103003008000",
        "fileKinds": ["html"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 2026년 부서별 게시물 구조는 확인했습니다. "
            "다만 업무추진비 화면의 공공누리 영역이 비어 있고 푸터가 All rights reserved로 "
            "표시되어 제1유형 또는 명확한 상업적 자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "동래구청"): {
        "sourceUrl": "https://www.dongnae.go.kr/index.dongnae?menuCd=DOM_000000101009000000",
        "fileKinds": ["xlsx", "xls", "hwp"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 2026년 게시물 구조는 확인했습니다. 다만 "
            "업무추진비 화면의 공공누리 영역이 비어 있고 자유이용 불가 안내가 노출되어 "
            "제1유형 또는 명확한 상업적 자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "북구청"): {
        "sourceUrl": (
            "https://www.bsbukgu.go.kr/index.bsbukgu?"
            "menuCd=DOM_000000105010010000"
        ),
        "fileKinds": ["xlsx", "xls", "pdf", "hwp"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역 목록과 최근 2026년 부서별 게시물 구조는 확인했습니다. "
            "다만 업무추진비 화면에서 공공누리 제1유형 표시가 확인되지 않고 저작권 정책은 "
            "공공누리 미부착 자료의 사전 협의를 요구하므로 제1유형 확인 전까지 수집하지 "
            "않습니다."
        ),
    },
    ("부산광역시", "강서구청"): {
        "sourceUrl": "https://www.bsgangseo.go.kr/portal/contents.do?mid=0503030100",
        "extraListUrls": [
            "https://www.bsgangseo.go.kr/portal/contents.do?mid=0503030200"
        ],
        "fileKinds": ["xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서별·과장급 이상 업무추진비 사용내역 목록과 최근 2026년 XLS 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않고 푸터가 All Rights Reserved로 표시되어 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("부산광역시", "강서구의회"): {
        "sourceUrl": "https://www.bsgangseo.go.kr/portal/contents.do?mid=0503030300",
        "fileKinds": ["xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 의회 업무추진비 사용내역 목록과 최근 분기별 XLS 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 "
            "확인되지 않고 푸터가 All Rights Reserved로 표시되어 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("부산광역시", "연제구청"): {
        "sourceUrl": "https://www.yeonje.go.kr/portal/contents.do?mId=0401090000",
        "fileKinds": ["xls", "hwp"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 2026년 XLS/HWP 첨부 구조는 확인했습니다. 다만 "
            "업무추진비 화면에서 공공누리 제1유형 표시가 확인되지 않고 저작권 정책은 "
            "상업적 목적 사용 불가와 제4유형 조건을 안내하므로 수집하지 않습니다."
        ),
    },
    ("부산광역시", "기장군청"): {
        "sourceUrl": "https://www.gijang.go.kr/index.gijang?menuCd=DOM_000000101002014000",
        "fileKinds": ["html"],
        "pageParam": "startPage",
        "followDetail": False,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무 추진비 공개 HTML 표와 최근 2026년 사용일자·사용장소·목적·금액 "
            "행 구조는 확인했습니다. 다만 업무추진비 화면에서 공공누리 제1유형 표시가 "
            "확인되지 않고 저작권 정책은 공공누리 제4유형 및 상업적 이용·변경 금지를 "
            "안내하므로 수집하지 않습니다."
        ),
    },
    ("충청북도", "청주시청"): {
        "sourceUrl": (
            "https://www.cheongju.go.kr/www/selectBbsNttList.do?"
            "bbsNo=24&integrDeptCode=&key=128&pageIndex=1&searchCnd=all&searchCtgry=&searchKrwd="
        ),
        "extraListUrls": [
            (
                "https://www.cheongju.go.kr/www/selectBbsNttList.do?"
                "bbsNo=664&integrDeptCode=&key=7838&pageIndex=1&searchCnd=all&searchCtgry=&searchKrwd="
            )
        ],
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 부단체장 이상 업무추진비 사용내역 목록은 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "청주시의회"): {
        "sourceUrl": "https://council.cheongju.go.kr/content/community/operatingExpenseList.html",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역 목록과 2025년 업무추진비 게시물 경로는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "충주시의회"): {
        "sourceUrl": "https://council.chungju.go.kr/content/news/releaseInformation.html",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 자료공개 목록과 2025년 업무추진비 집행내역 게시물은 "
            "확인했습니다. 다만 화면 하단 저작권 문구만 확인되고 공공누리 제1유형 또는 "
            "명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "제천시청"): {
        "sourceUrl": (
            "https://www.jecheon.go.kr/www/selectBbsNttList.do?"
            "bbsNo=259&id=www_050301030000"
        ),
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 2025년 업무추진비 내역 게시물은 확인했습니다. 다만 "
            "화면 하단 저작권 문구만 확인되고 공공누리 제1유형 또는 명확한 자유이용 표시가 "
            "확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "옥천군청"): {
        "sourceUrl": "https://www.oc.go.kr/www/selectBbsNttList.do?bbsNo=16&key=124",
        "extraListUrls": ["https://www.oc.go.kr/www/selectBbsNttList.do?bbsNo=17&key=125"],
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행내역과 군수 업무추진비 목록, 최근 12개월 게시물·XLSX/XLS "
            "첨부 구조는 확인했습니다. 다만 상세 화면이 공공누리 제4유형으로 표시되어 "
            "상업적 이용과 변경이 모두 제한되므로 수집하지 않습니다."
        ),
    },
    ("충청북도", "영동군청"): {
        "sourceUrl": "https://www.yd21.go.kr/kr/html/sub03/030504.html?GotoPage=1&mode=L",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "GotoPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 12개월 게시물·XLSX/PDF 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "증평군의회"): {
        "sourceUrl": "https://council.jp.go.kr/source/korean/news/business.html",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 최근 12개월 게시물·XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "진천군의회"): {
        "sourceUrl": "https://council.jincheon.go.kr/council/selectBbsNttList.do?bbsNo=67&key=114",
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 12개월 게시물·XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "괴산군청"): {
        "sourceUrl": "https://goesan.go.kr/www/selectBbsNttList.do?bbsNo=202&integrDeptCode=&key=1731",
        "extraListUrls": [
            "https://www.goesan.go.kr/www/selectBbsNttList.do?bbsNo=351&integrDeptCode=&key=1729"
        ],
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 기관운영 업무추진비와 시책추진 업무추진비 목록, 최근 12개월 게시물·XLSX/XLS "
            "첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 "
            "명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "괴산군의회"): {
        "sourceUrl": "https://council.goesan.go.kr/kr/costBBS.do",
        "fileKinds": ["xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 12개월 게시물·XLS/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "음성군의회"): {
        "sourceUrl": "https://www.escouncil.go.kr/kr/news/bbsBusiness.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageNum",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 12개월 게시물·XLSX/PDF 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "단양군청"): {
        "sourceUrl": "https://www.danyang.go.kr/dy21/723?action=list&page_size=10",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 최근 12개월 게시물·PDF/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("충청북도", "단양군의회"): {
        "sourceUrl": "https://www.danyang.go.kr/dy21/723?action=list&page_size=10",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "단양군 공식 업무추진비 공개 목록에서 의회 관련 업무추진비 검색 경로와 최근 "
            "12개월 게시물·PDF/XLSX 첨부 구조를 함께 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("울산광역시", "남구청"): {
        "sourceUrl": "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=PrmtFee3",
        "extraListUrls": [
            "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=PrmtFee",
            "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=PrmtFee1",
            "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=PrmtFee2",
            "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=dongPrmtFee",
            "https://www.ulsannamgu.go.kr/cop/bbs/selectBoardList.do?bbsId=healthPrmtFee",
        ],
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 구청장·부구청장·국장·부서장·동장·보건소 탭, "
            "상세·PDF 다운로드 구조는 확인했습니다. 다만 목록/상세 화면에서 공공누리 "
            "제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("울산광역시", "울주군의회"): {
        "sourceUrl": "https://assembly.ulju.ulsan.kr/kr/bbs?bbs_id=business",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 집행 현황 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "동구청"): {
        "sourceUrl": "https://dong.daegu.kr/portal/board/post/list.do?bcIdx=557&mid=0501040000",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 PDF/XLS 첨부 구조는 확인했습니다. 다만 목록/상세 화면에서 "
            "공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않고 저작권정책 "
            "링크만 확인되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "남구청"): {
        "sourceUrl": "https://www.nam.daegu.kr/index.do?menu_id=00001247",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 2026년 XLS/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록 화면의 공공누리 영역이 비어 있고 저작권정책 링크만 확인되어 "
            "제1유형 또는 명확한 상업적 자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "북구청"): {
        "sourceUrl": "https://www.buk.daegu.kr/index.do?menu_id=00002422",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 최근 2026년 XLSX/PDF 첨부 구조는 확인했습니다. "
            "다만 목록 화면이 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 "
            "표시되어 상업적 이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("대구광역시", "수성구청"): {
        "sourceUrl": "https://www.suseong.kr/index.do?menu_id=00042650",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 2026년 업무추진비 공개 페이지와 구청장 월별 XLSX 다운로드 구조는 "
            "확인했습니다. 다만 공공누리 영역이 비어 있고 푸터가 All Rights Reserved로 "
            "표시되어 제1유형 또는 명확한 상업적 자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "서구청"): {
        "sourceUrl": "https://www.dgs.go.kr/portal/board/post/list.do?bcIdx=511&mid=0502030000",
        "fileKinds": ["xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 사전정보공표 업무추진비 공개 목록과 최근 2026년 XLS 첨부 구조는 "
            "확인했습니다. 다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 "
            "자유이용 표시가 확인되지 않고 저작권보호정책 링크가 비활성 주석으로만 남아 "
            "있어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "달서구청"): {
        "sourceUrl": "https://www.dalseo.daegu.kr/index.do?menu_id=10000202",
        "fileKinds": ["html"],
        "pageParam": "pageIndex",
        "followDetail": False,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 연도별 목록과 2026년 공개 경로는 확인했습니다. 다만 "
            "업무추진비 화면의 공공누리 영역이 비어 있고 저작권 정책은 공공누리 부착 "
            "저작물만 이용조건 범위 안에서 자유이용 가능하다고 안내하므로 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "달성군청"): {
        "sourceUrl": "https://www.dalseong.daegu.kr/index.do?menu_id=00001704",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 최근 2026년 XLS/XLSX 첨부 구조는 확인했습니다. "
            "다만 업무추진비 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 "
            "표시가 확인되지 않고 푸터가 All rights reserved로 표시되며 저작권정책 링크가 "
            "비활성 주석으로만 남아 있어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("대구광역시", "군위군청"): {
        "holdStatus": "pdf_vision_hold",
        "sourceUrl": "https://www.gunwi.go.kr/ko/page.do?mnu_uid=160",
        "fileKinds": ["pdf", "xlsx", "xls"],
        "pageParam": "pageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·PDF 첨부 구조, 공공누리 제1유형 표시는 확인했습니다. "
            "그러나 2026년 1분기 샘플 dry-run에서 posts_seen=10, posts_fetched=1 이후 "
            "scanned PDF vision extraction이 필요했고 현재 실행 환경에서 LLM vision 키가 없어 "
            "raw_parsed_rows=0으로 실패했습니다. PDF vision 처리 성공 전까지 production 적재하지 "
            "않습니다."
        ),
    },
    ("울산광역시", "동구청"): {
        "sourceUrl": "https://www.donggu.ulsan.kr/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000354",
        "extraListUrls": [
            "https://www.donggu.ulsan.kr/mayor/expense/list.do",
            "https://www.donggu.ulsan.kr/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000361",
            "https://www.donggu.ulsan.kr/cop/bbs/selectBoardList.do?bbsId=BBSMSTR_000000000362",
        ],
        "fileKinds": ["pdf"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 PDF 첨부 구조는 확인했습니다. 다만 상세 화면이 "
            "공공누리 제2유형(출처표시+상업적 이용금지)으로 표시되어 상업적 이용이 가능하지 "
            "않으므로 수집하지 않습니다."
        ),
    },
    ("경상북도", "포항시청"): {
        "sourceUrl": "https://pohang.go.kr/portal/contents.do?mid=0301040300",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상북도", "포항시의회"): {
        "sourceUrl": "https://council.pohang.go.kr/content/data/operatingExpenseList.html",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상북도", "문경시청"): {
        "sourceUrl": "https://www.gbmg.go.kr/portal/contents.do?mId=0201070000",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·PDF/XLS/XLSX 첨부 구조는 확인했습니다. 다만 "
            "상세 화면이 공공누리 제4유형(출처표시+상업용금지+변경금지)으로 표시되어 "
            "상업적 이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("경상북도", "경주시의회"): {
        "sourceUrl": "https://council.gyeongju.go.kr/kr/costBBS.do",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 분기별 PDF 첨부 구조는 확인했습니다. 다만 목록/상세 "
            "화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 표시가 확인되지 않고 "
            "푸터가 All Rights Reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상북도", "김천시청"): {
        "sourceUrl": "https://www.gc.go.kr/portal/contents.do?mId=1515000000",
        "fileKinds": ["xlsx", "xls", "html"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 XLS 첨부, 일부 상세 HTML 표 구조는 확인했습니다. 다만 "
            "업무추진비 목록/상세 화면에서 공공누리 제1유형 또는 명확한 상업적 자유이용 "
            "표시가 확인되지 않고 푸터가 All Rights Reserved로 표시되어 제1유형 확인 "
            "전까지 수집하지 않습니다."
        ),
    },
    ("경상북도", "안동시청"): {
        "sourceUrl": "https://www.andong.go.kr/portal/contents.do?mId=0503060300",
        "extraListUrls": [
            "https://www.andong.go.kr/portal/contents.do?mId=0503060200",
        ],
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 XLSX 첨부 구조는 확인했습니다. 다만 최근 상세 화면이 "
            "공공누리 자유이용 불가로 표시되거나 일부 게시물이 제4유형으로 표시되어 "
            "상업적 이용이 가능하지 않으므로 수집하지 않습니다."
        ),
    },
    ("경상남도", "진주시청"): {
        "sourceUrl": "https://www.jinju.go.kr/05638.web",
        "extraListUrls": ["https://www.jinju.go.kr/05637.web"],
        "fileKinds": ["xlsx"],
        "pageParam": "cpage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 과장급·국소장급 업무추진비 목록과 상세·XLSX 첨부 구조는 확인했습니다. "
            "다만 일부 상세는 공공누리 제1유형이지만 같은 업무추진비 보드의 다른 상세가 "
            "공공누리 제4유형으로 표시되어, 게시물별 라이선스 필터가 구현되기 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("경상남도", "창원시의회"): {
        "sourceUrl": "https://council.changwon.go.kr/svc/cns/OperatingExpenseList.do",
        "fileKinds": ["pdf"],
        "pageParam": "pageNo",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 진행 현황 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상남도", "김해시청"): {
        "sourceUrl": "https://www.gimhae.go.kr/00819.web",
        "extraListUrls": [
            "https://www.gimhae.go.kr/00820.web",
            "https://www.gimhae.go.kr/00821.web",
        ],
        "fileKinds": ["xlsx", "xls", "pdf"],
        "pageParam": "cpage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 시장·부시장, 실·국장급, 과장급 업무추진비 목록과 상세·XLS/XLSX/PDF "
            "다운로드 구조는 확인했습니다. 다만 업무추진비 상세의 공공누리 영역에 유형이 "
            "표시되지 않고 푸터가 All Rights Reserved로 표시되어 제1유형 확인 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("경상남도", "김해시의회"): {
        "sourceUrl": "https://council.gimhae.go.kr/cnts/bbs/boardList.php?bbsCd=opn&bbsSubCd=opn0104",
        "fileKinds": ["xlsx"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 현황 목록과 최근 12개월 게시물·XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상남도", "산청군청"): {
        "sourceUrl": "https://www.sancheong.go.kr/www/selectBbsNttList.do?bbsNo=259&key=5091",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 상세·PDF/XLS/XLSX 첨부 구조는 확인했습니다. 다만 "
            "업무추진비 상세 화면에서 실제 공공누리 제1유형 표시가 노출되지 않아 제1유형 "
            "확인 전까지 수집하지 않습니다."
        ),
    },
    ("경상남도", "거창군청"): {
        "sourceUrl": "https://www.geochang.go.kr/00107/00108/00150.web",
        "fileKinds": ["xlsx", "xls"],
        "pageParam": "cpage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 최근 분기별 XLS/XLSX 첨부 구조는 확인했습니다. "
            "다만 목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "여수시청"): {
        "sourceUrl": "https://www.yeosu.go.kr/www/pubinfo/announce/operating_expense",
        "fileKinds": ["pdf", "zip"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·PDF/ZIP 다운로드 구조는 확인했습니다. 다만 목록/상세 "
            "화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 표시되어 "
            "제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "목포시청"): {
        "sourceUrl": "https://www.mokpo.go.kr/www/open_data/open_operational_cost",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면의 공공누리 유형 표시가 비어 있어 제1유형 또는 명확한 "
            "자유이용 표시 확인 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "목포시의회"): {
        "sourceUrl": "https://council.mokpo.go.kr/kr/bbs?bbs_id=expenses",
        "fileKinds": ["pdf"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 게시판과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 "
            "않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "나주시청"): {
        "sourceUrl": "https://naju.go.kr/www/open_data/budget/expense",
        "extraListUrls": ["https://naju.go.kr/www/support/sitemap"],
        "fileKinds": ["html"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 예산살림 업무추진비 메뉴와 단체장업무추진비사용내역 목록은 확인했습니다. "
            "다만 현재 로컬 수집 환경에서는 본문이 0바이트로 내려오고, 목록/상세 화면의 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 제1유형과 수집 "
            "접근성 확인 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "광양시청"): {
        "sourceUrl": "https://gwangyang.go.kr/mayor/menu.es?mid=a20106014600",
        "fileKinds": ["html"],
        "pageParam": "role_and_quarter",
        "followDetail": False,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 열린시장실 업무추진비 공개 화면에서 시장·부시장·국장·소장 역할별 "
            "분기 선택 목록과 HTML 표 구조를 확인했습니다. 다만 화면 하단 공공누리 표시가 "
            "출처표시+상업적이용금지+변경금지 조합으로 확인되어 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "순천시청"): {
        "sourceUrl": (
            "https://sc.go.kr/kr/open/0001/0012?"
            "boardId=bbs_0000000000010158&mode=list&category=&pageIdx="
        ),
        "fileKinds": ["pdf", "hwpx"],
        "pageParam": "pageIdx",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록과 상세·PDF/HWPX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면이 공공누리 제4유형(출처표시-비상업적-변경금지)으로 표시되어 "
            "제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "구례군청"): {
        "sourceUrl": (
            "https://www.gurye.go.kr/board/list.do?"
            "bbsId=bbs_0000000000000055&menuNo=115002005000"
        ),
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 "
            "확인했습니다. 다만 목록/상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+"
            "변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 "
            "않습니다."
        ),
    },
    ("전라남도", "구례군의회"): {
        "sourceUrl": (
            "https://www.gurye.go.kr/board/list.do?"
            "bbsId=BBS_000000000000261&menuNo=162005000000"
        ),
        "fileKinds": ["xlsx"],
        "pageParam": "pageIndex",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·XLSX 다운로드 구조, 전체 ZIP 다운로드 구조를 "
            "확인했습니다. 다만 목록/상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+"
            "변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 "
            "않습니다."
        ),
    },
    ("전라남도", "고흥군청"): {
        "sourceUrl": "https://www.goheung.go.kr/boardList.do?boardId=BD_00107&pageId=www497",
        "fileKinds": ["pdf"],
        "pageParam": "movePage",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 사전정보공개 업무추진비 공개 목록과 상세·PDF 다운로드 구조는 확인했습니다. "
            "다만 목록/상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 "
            "표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전라남도", "고흥군의회"): {
        "sourceUrl": "https://council.goheung.go.kr/main/board/45/1/category7",
        "fileKinds": ["pdf"],
        "pageParam": "path",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 열린의회 정보공개 업무추진비 목록과 경로형 페이지네이션, 상세·PDF "
            "다운로드 구조는 확인했습니다. 다만 목록/상세 화면이 공공누리 제4유형"
            "(출처표시+상업적이용금지+변경금지)으로 표시되어 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "동구청"): {
        "sourceUrl": "https://www.donggu.kr/board.es?mid=a10301080400&bid=0270",
        "fileKinds": ["xlsx"],
        "pageParam": "nPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 부서장 업무추진비 목록에서 2026년 1분기·2025년 3~4분기 최근 게시물과 "
            "상세·XLSX 다운로드 구조는 확인했습니다. 다만 상세 화면이 공공누리 제4유형"
            "(출처표시+상업적 이용금지+변경금지)으로 표시되어 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "동구의회"): {
        "sourceUrl": "https://gjdc.donggu.kr/board.es?mid=a10801040000&bid=0020",
        "fileKinds": ["xlsx"],
        "pageParam": "nPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 의정활동 정보공개 업무추진비 현황 목록과 XLSX 첨부 다운로드 구조는 "
            "확인했습니다. 다만 목록 화면에서 공공누리 제1유형 또는 명확한 자유이용 "
            "표시가 확인되지 않아 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "서구청"): {
        "sourceUrl": "https://www.seogu.gwangju.kr/menu.es?mid=a10518030200",
        "fileKinds": ["xlsx"],
        "pageParam": "inline",
        "followDetail": False,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 국장급이상 업무추진비 공개 화면에서 2026년 1분기와 2025년 2~4분기 "
            "최근 자료 및 XLSX 다운로드 구조는 확인했습니다. 다만 업무추진비 화면에서 "
            "공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않고 푸터가 All "
            "Rights Reserved로 표시되어 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "서구의회"): {
        "holdStatus": "no_recent_data",
        "sourceUrl": "https://www.seogu.gwangju.kr/menu.es?mid=a10518030300",
        "fileKinds": ["xlsx"],
        "pageParam": "inline",
        "followDetail": False,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 지방의회 의원 업무추진비 사용내역 화면과 XLSX 다운로드 구조는 확인했습니다. "
            "다만 목록의 최신 등록일이 2023-08-29이고 실제 분기별 자료는 2021년 4분기 "
            "이전으로 확인되어 최근 12개월 적재 대상 데이터가 없습니다."
        ),
    },
    ("광주광역시", "남구청"): {
        "sourceUrl": "https://www.namgu.gwangju.kr/board.es?mid=a10304100000&bid=0007",
        "fileKinds": ["xlsx"],
        "pageParam": "nPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 공개 목록에서 2026년 1분기·2025년 4분기 최근 게시물과 "
            "상세·XLSX 다운로드 구조는 확인했습니다. 다만 상세 화면이 공공누리 제4유형"
            "(출처표시+상업적 이용금지+변경금지)으로 표시되어 제1유형 원칙을 바꾸는 "
            "ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "북구청"): {
        "sourceUrl": "http://bukgu.gwangju.kr/board.es?mid=a10502050000&bid=0004",
        "fileKinds": ["xlsx"],
        "pageParam": "nPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록에서 2026년 1~2분기 최근 게시물과 상세·XLSX "
            "다운로드 구조는 확인했습니다. 다만 상세 화면에 개별 공공누리 유형 표시가 "
            "확인되지 않고 저작권 보호정책상 공공누리 표시가 없는 자료는 사전 협의가 "
            "필요해 제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("광주광역시", "광산구청"): {
        "sourceUrl": "https://gwangsan.go.kr/contentsView.do?pageId=www159",
        "fileKinds": ["pdf", "xlsx"],
        "pageParam": "movePage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 사전정보공표 화면과 getInfoOpenList.do/getInfoOpenData.do "
            "내장 API, 최근 2026-05-29·2026-05-08 자료 및 PDF/XLSX 다운로드 구조는 "
            "확인했습니다. 다만 화면 하단이 공공누리 제4유형(출처표시+상업적 이용금지+"
            "변경금지)으로 표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 "
            "수집하지 않습니다."
        ),
    },
    ("전북특별자치도", "전주시청"): {
        "sourceUrl": (
            "https://www.jeonju.go.kr/planweb/board/list.9is?"
            "boardUid=ff8080818bad9295018badaa04e2005f&"
            "contentUid=ff8080818990c349018b041a97883a1d&page=1"
        ),
        "fileKinds": ["hwpx", "pdf", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비 목록과 상세·HWPX/PDF/XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면이 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 "
            "표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전북특별자치도", "군산시의회"): {
        "sourceUrl": "https://council.gunsan.go.kr/kr/open/bbsCost.do?flag=&keyword=&pageNum=1&reform=list",
        "fileKinds": ["pdf", "xls", "xlsx"],
        "pageParam": "pageNum",
        "followDetail": True,
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 업무추진비공개 목록과 상세·PDF/XLS/XLSX 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면에서 공공누리 제1유형 또는 명확한 자유이용 표시가 확인되지 않아 "
            "제1유형 확인 전까지 수집하지 않습니다."
        ),
    },
    ("전북특별자치도", "익산시의회"): {
        "sourceUrl": "https://council.iksan.go.kr/board/list.iksan?boardId=BBS_0000012&menuCd=DOM_000000107010000000",
        "fileKinds": ["pdf"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 열린의회 업무추진비 공개 목록과 상세·PDF 다운로드 구조는 확인했습니다. "
            "다만 공공누리 영역이 주석 처리되어 있고, 상세 화면의 확인 가능한 표시는 "
            "공공누리 제4유형(출처표시+상업적이용금지+변경금지)이므로 제1유형 원칙을 "
            "바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전북특별자치도", "남원시청"): {
        "sourceUrl": (
            "https://www.namwon.go.kr/board/post/list.do?"
            "boardUid=ff8080818eacb22f018ebb2ab0f900fc&"
            "menuUid=ff8080818e3beff0018e40d3b21d022c&page=1"
        ),
        "fileKinds": ["pdf", "hwp", "hwpx", "xlsx", "xls"],
        "pageParam": "page",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 정보공개 업무추진비공개 시장 목록과 첨부 구조는 확인했습니다. 다만 "
            "목록 화면이 공공누리 제4유형(출처표시+상업적 이용금지+변경금지)으로 표시되어 "
            "제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
    ("전북특별자치도", "장수군청"): {
        "sourceUrl": "https://www.jangsu.go.kr/mayor/board/list.jangsu?boardId=BBS_0000114&contentsSid=450&cpath=%2Fmayor&menuCd=DOM_000000302004000000",
        "fileKinds": ["pdf"],
        "pageParam": "startPage",
        "followDetail": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "공식 사이트 원격 확인",
        "blocker": (
            "공식 군수 업무추진비 목록과 상세·PDF 다운로드 구조는 확인했습니다. 다만 "
            "목록/상세 화면이 공공누리 제4유형(출처표시+상업적이용금지+변경금지)으로 "
            "표시되어 제1유형 원칙을 바꾸는 ADR·법적 결정 전까지 수집하지 않습니다."
        ),
    },
}

NON_CAPITAL_BASIC_REGION_GROUPS = [
    (
        "busan",
        "부산광역시",
        [
            ("중구", JurisdictionType.AUTONOMOUS_GU),
            ("서구", JurisdictionType.AUTONOMOUS_GU),
            ("동구", JurisdictionType.AUTONOMOUS_GU),
            ("영도구", JurisdictionType.AUTONOMOUS_GU),
            ("부산진구", JurisdictionType.AUTONOMOUS_GU),
            ("동래구", JurisdictionType.AUTONOMOUS_GU),
            ("남구", JurisdictionType.AUTONOMOUS_GU),
            ("북구", JurisdictionType.AUTONOMOUS_GU),
            ("해운대구", JurisdictionType.AUTONOMOUS_GU),
            ("사하구", JurisdictionType.AUTONOMOUS_GU),
            ("금정구", JurisdictionType.AUTONOMOUS_GU),
            ("강서구", JurisdictionType.AUTONOMOUS_GU),
            ("연제구", JurisdictionType.AUTONOMOUS_GU),
            ("수영구", JurisdictionType.AUTONOMOUS_GU),
            ("사상구", JurisdictionType.AUTONOMOUS_GU),
            ("기장군", JurisdictionType.GUN),
        ],
    ),
    (
        "daegu",
        "대구광역시",
        [
            ("중구", JurisdictionType.AUTONOMOUS_GU),
            ("동구", JurisdictionType.AUTONOMOUS_GU),
            ("서구", JurisdictionType.AUTONOMOUS_GU),
            ("남구", JurisdictionType.AUTONOMOUS_GU),
            ("북구", JurisdictionType.AUTONOMOUS_GU),
            ("수성구", JurisdictionType.AUTONOMOUS_GU),
            ("달서구", JurisdictionType.AUTONOMOUS_GU),
            ("달성군", JurisdictionType.GUN),
            ("군위군", JurisdictionType.GUN),
        ],
    ),
    (
        "gwangju",
        "광주광역시",
        [
            ("동구", JurisdictionType.AUTONOMOUS_GU),
            ("서구", JurisdictionType.AUTONOMOUS_GU),
            ("남구", JurisdictionType.AUTONOMOUS_GU),
            ("북구", JurisdictionType.AUTONOMOUS_GU),
            ("광산구", JurisdictionType.AUTONOMOUS_GU),
        ],
    ),
    (
        "daejeon",
        "대전광역시",
        [
            ("동구", JurisdictionType.AUTONOMOUS_GU),
            ("중구", JurisdictionType.AUTONOMOUS_GU),
            ("서구", JurisdictionType.AUTONOMOUS_GU),
            ("유성구", JurisdictionType.AUTONOMOUS_GU),
            ("대덕구", JurisdictionType.AUTONOMOUS_GU),
        ],
    ),
    (
        "ulsan",
        "울산광역시",
        [
            ("중구", JurisdictionType.AUTONOMOUS_GU),
            ("남구", JurisdictionType.AUTONOMOUS_GU),
            ("동구", JurisdictionType.AUTONOMOUS_GU),
            ("북구", JurisdictionType.AUTONOMOUS_GU),
            ("울주군", JurisdictionType.GUN),
        ],
    ),
    (
        "gangwon",
        "강원특별자치도",
        [
            ("춘천시", JurisdictionType.SI),
            ("원주시", JurisdictionType.SI),
            ("강릉시", JurisdictionType.SI),
            ("동해시", JurisdictionType.SI),
            ("태백시", JurisdictionType.SI),
            ("속초시", JurisdictionType.SI),
            ("삼척시", JurisdictionType.SI),
            ("홍천군", JurisdictionType.GUN),
            ("횡성군", JurisdictionType.GUN),
            ("영월군", JurisdictionType.GUN),
            ("평창군", JurisdictionType.GUN),
            ("정선군", JurisdictionType.GUN),
            ("철원군", JurisdictionType.GUN),
            ("화천군", JurisdictionType.GUN),
            ("양구군", JurisdictionType.GUN),
            ("인제군", JurisdictionType.GUN),
            ("고성군", JurisdictionType.GUN),
            ("양양군", JurisdictionType.GUN),
        ],
    ),
    (
        "chungbuk",
        "충청북도",
        [
            ("청주시", JurisdictionType.SI),
            ("충주시", JurisdictionType.SI),
            ("제천시", JurisdictionType.SI),
            ("보은군", JurisdictionType.GUN),
            ("옥천군", JurisdictionType.GUN),
            ("영동군", JurisdictionType.GUN),
            ("증평군", JurisdictionType.GUN),
            ("진천군", JurisdictionType.GUN),
            ("괴산군", JurisdictionType.GUN),
            ("음성군", JurisdictionType.GUN),
            ("단양군", JurisdictionType.GUN),
        ],
    ),
    (
        "chungnam",
        "충청남도",
        [
            ("천안시", JurisdictionType.SI),
            ("공주시", JurisdictionType.SI),
            ("보령시", JurisdictionType.SI),
            ("아산시", JurisdictionType.SI),
            ("서산시", JurisdictionType.SI),
            ("논산시", JurisdictionType.SI),
            ("계룡시", JurisdictionType.SI),
            ("당진시", JurisdictionType.SI),
            ("금산군", JurisdictionType.GUN),
            ("부여군", JurisdictionType.GUN),
            ("서천군", JurisdictionType.GUN),
            ("청양군", JurisdictionType.GUN),
            ("홍성군", JurisdictionType.GUN),
            ("예산군", JurisdictionType.GUN),
            ("태안군", JurisdictionType.GUN),
        ],
    ),
    (
        "jeonbuk",
        "전북특별자치도",
        [
            ("전주시", JurisdictionType.SI),
            ("군산시", JurisdictionType.SI),
            ("익산시", JurisdictionType.SI),
            ("정읍시", JurisdictionType.SI),
            ("남원시", JurisdictionType.SI),
            ("김제시", JurisdictionType.SI),
            ("완주군", JurisdictionType.GUN),
            ("진안군", JurisdictionType.GUN),
            ("무주군", JurisdictionType.GUN),
            ("장수군", JurisdictionType.GUN),
            ("임실군", JurisdictionType.GUN),
            ("순창군", JurisdictionType.GUN),
            ("고창군", JurisdictionType.GUN),
            ("부안군", JurisdictionType.GUN),
        ],
    ),
    (
        "jeonnam",
        "전라남도",
        [
            ("목포시", JurisdictionType.SI),
            ("여수시", JurisdictionType.SI),
            ("순천시", JurisdictionType.SI),
            ("나주시", JurisdictionType.SI),
            ("광양시", JurisdictionType.SI),
            ("담양군", JurisdictionType.GUN),
            ("곡성군", JurisdictionType.GUN),
            ("구례군", JurisdictionType.GUN),
            ("고흥군", JurisdictionType.GUN),
            ("보성군", JurisdictionType.GUN),
            ("화순군", JurisdictionType.GUN),
            ("장흥군", JurisdictionType.GUN),
            ("강진군", JurisdictionType.GUN),
            ("해남군", JurisdictionType.GUN),
            ("영암군", JurisdictionType.GUN),
            ("무안군", JurisdictionType.GUN),
            ("함평군", JurisdictionType.GUN),
            ("영광군", JurisdictionType.GUN),
            ("장성군", JurisdictionType.GUN),
            ("완도군", JurisdictionType.GUN),
            ("진도군", JurisdictionType.GUN),
            ("신안군", JurisdictionType.GUN),
        ],
    ),
    (
        "gyeongbuk",
        "경상북도",
        [
            ("포항시", JurisdictionType.SI),
            ("경주시", JurisdictionType.SI),
            ("김천시", JurisdictionType.SI),
            ("안동시", JurisdictionType.SI),
            ("구미시", JurisdictionType.SI),
            ("영주시", JurisdictionType.SI),
            ("영천시", JurisdictionType.SI),
            ("상주시", JurisdictionType.SI),
            ("문경시", JurisdictionType.SI),
            ("경산시", JurisdictionType.SI),
            ("의성군", JurisdictionType.GUN),
            ("청송군", JurisdictionType.GUN),
            ("영양군", JurisdictionType.GUN),
            ("영덕군", JurisdictionType.GUN),
            ("청도군", JurisdictionType.GUN),
            ("고령군", JurisdictionType.GUN),
            ("성주군", JurisdictionType.GUN),
            ("칠곡군", JurisdictionType.GUN),
            ("예천군", JurisdictionType.GUN),
            ("봉화군", JurisdictionType.GUN),
            ("울진군", JurisdictionType.GUN),
            ("울릉군", JurisdictionType.GUN),
        ],
    ),
    (
        "gyeongnam",
        "경상남도",
        [
            ("창원시", JurisdictionType.SI),
            ("진주시", JurisdictionType.SI),
            ("통영시", JurisdictionType.SI),
            ("사천시", JurisdictionType.SI),
            ("김해시", JurisdictionType.SI),
            ("밀양시", JurisdictionType.SI),
            ("거제시", JurisdictionType.SI),
            ("양산시", JurisdictionType.SI),
            ("의령군", JurisdictionType.GUN),
            ("함안군", JurisdictionType.GUN),
            ("창녕군", JurisdictionType.GUN),
            ("고성군", JurisdictionType.GUN),
            ("남해군", JurisdictionType.GUN),
            ("하동군", JurisdictionType.GUN),
            ("산청군", JurisdictionType.GUN),
            ("함양군", JurisdictionType.GUN),
            ("거창군", JurisdictionType.GUN),
            ("합천군", JurisdictionType.GUN),
        ],
    ),
]

GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD = {
    "homepage": "https://www.ggc.go.kr",
    "listUrl": "https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list",
    "fileKinds": ["xlsx", "xls", "pdf"],
    "followDetail": False,
    "pageParam": "cp",
    "verifiedAt": "2026-06-01",
    "verifiedBy": "공식 사이트 화면·원격 확인",
}

INCHEON_METRO_OFFICE_ATTACHMENT_BOARD = {
    "homepage": "https://www.incheon.go.kr",
    "listUrl": "https://www.incheon.go.kr/open/OPEN010305",
    "fileKinds": ["pdf", "xlsx", "xls"],
    "followDetail": True,
    "pageParam": "curPage",
    "verifiedAt": "2026-06-01",
    "verifiedBy": "공식 사이트 원격 확인",
}

INCHEON_OFFICE_ATTACHMENT_BOARDS = {
    "중구": {
        "homepage": "https://www.icjg.go.kr",
        "listUrl": "https://www.icjg.go.kr/krop0307c",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "curPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "동구": {
        "homepage": "https://www.icdonggu.go.kr",
        "listUrl": "https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 검색·원격 확인",
    },
    "서구": {
        "homepage": "https://www.seo.incheon.kr",
        "listUrl": "https://www.seo.incheon.kr/open_content/main/bbs/bbsMsgList.do?bcd=clean_cost",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "미추홀구": {
        "homepage": "https://www.michuhol.go.kr",
        "listUrl": "https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year=",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "연수구": {
        "homepage": "https://www.yeonsu.go.kr",
        "listUrl": "https://www.yeonsu.go.kr/main/administration/open_info/charge.asp",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "gotopage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "부평구": {
        "homepage": "https://www.icbp.go.kr",
        "listUrl": "https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면 확인",
    },
    "남동구": {
        "homepage": "https://biz.namdong.go.kr",
        "listUrl": "https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "계양구": {
        "homepage": "https://www.gyeyang.go.kr",
        "listUrl": "https://www.gyeyang.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=board_14&cate1=94",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "강화군": {
        "homepage": "https://www.ganghwa.go.kr",
        "listUrl": "https://www.ganghwa.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=operation",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "옹진군": {
        "homepage": "https://www.ongjin.go.kr",
        "listUrl": "https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
}

INCHEON_COUNCIL_ATTACHMENT_BOARDS = {
    "중구": {
        "homepage": "https://www.icjg.go.kr/council",
        "listUrl": "https://www.icjg.go.kr/council/cnac04b",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "curPage",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "동구": {
        "homepage": "https://council.icdonggu.go.kr",
        "listUrl": "https://council.icdonggu.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "연수구": {
        "homepage": "https://council.yeonsu.go.kr",
        "listUrl": "https://council.yeonsu.go.kr/kr/businessBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "남동구": {
        "homepage": "https://council.namdong.go.kr",
        "listUrl": "https://council.namdong.go.kr/kr/data/bbsBreakdown.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "pageNum",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 화면·원격 확인",
    },
    "부평구": {
        "homepage": "https://council.icbp.go.kr",
        "listUrl": "https://council.icbp.go.kr/kr/data/bbs?bbs_id=expense",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "계양구": {
        "homepage": "https://council.gyeyang.go.kr",
        "listUrl": "https://council.gyeyang.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "서구": {
        "homepage": "https://www.seo.incheon.kr",
        "listUrl": "https://www.seo.incheon.kr/open_content/council/activity/open.jsp",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": False,
        "pageParam": "pgno",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "강화군": {
        "homepage": "https://council.ganghwa.go.kr",
        "listUrl": "https://council.ganghwa.go.kr/kr/workBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
    "옹진군": {
        "homepage": "https://council.ongjin.go.kr",
        "listUrl": "https://council.ongjin.go.kr/kr/costBBS.do",
        "fileKinds": ["xlsx", "xls", "pdf"],
        "followDetail": True,
        "pageParam": "page",
        "verifiedAt": "2026-06-01",
        "verifiedBy": "공식 사이트 원격 확인",
    },
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
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SPECIAL_CITY,
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
            if gu in SEOUL_OFFICE_ATTACHMENT_PAGE_PARAMS:
                office_source_pattern["pageParam"] = SEOUL_OFFICE_ATTACHMENT_PAGE_PARAMS[gu]
            if gu in SEOUL_OFFICE_ATTACHMENT_PAGE_UNIT_PARAMS:
                office_source_pattern["pageUnitParam"] = SEOUL_OFFICE_ATTACHMENT_PAGE_UNIT_PARAMS[
                    gu
                ]
        elif gu in SEOUL_OFFICE_INLINE_TABLES:
            office_source_pattern = {
                "adapter": "inline_expense_table",
                "listUrl": SEOUL_OFFICE_INLINE_TABLES[gu],
                "rowsPerPage": 100,
                "pageParam": "cp" if gu == "서대문구" else "pageIndex",
                "pageUnitParam": "pageUnit",
            }
        agencies.append(
            Agency(
                id=agency_uuid(f"{gu}:office"),
                name=f"서울특별시 {gu}청",
                short_name=f"{gu}청",
                gov_tier=GovTier.BASIC,
                branch=GovBranch.ADMIN,
                jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
                parent_region="서울특별시",
                sub_region=gu,
                homepage=SEOUL_GU_HOMEPAGES.get(gu, f"https://www.{domain_slug}.go.kr"),
                source_pattern=office_source_pattern,
            )
        )
        agencies.append(
            Agency(
                id=agency_uuid(f"{gu}:council"),
                name=f"서울특별시 {gu}의회",
                short_name=f"{gu}의회",
                gov_tier=GovTier.BASIC,
                branch=GovBranch.COUNCIL,
                jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
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


def gyeonggi_agencies() -> list[Agency]:
    agencies: list[Agency] = [
        Agency(
            id=agency_uuid("gyeonggi:province:office"),
            name="경기도청",
            short_name="경기도청",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.PROVINCE,
            parent_region="경기도",
            sub_region=None,
            homepage=None,
            source_pattern={
                "adapter": "gyeonggi_admin_required",
                "searchKeyword": "경기도청 업무추진비",
                "status": "adapter_required",
                "holdStatus": "legal_hold",
                "blocker": GYEONGGI_OFFICE_PENDING_BLOCKERS["경기도청"],
            },
        ),
        Agency(
            id=agency_uuid("gyeonggi:province:council"),
            name="경기도의회",
            short_name="경기도의회",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.PROVINCE,
            parent_region="경기도",
            sub_region=None,
            homepage=GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["homepage"],
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["listUrl"],
                "fileKinds": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["fileKinds"],
                "followDetail": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["followDetail"],
                "pageParam": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["pageParam"],
                "verifiedAt": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["verifiedAt"],
                "verifiedBy": GYEONGGI_PROVINCE_COUNCIL_ATTACHMENT_BOARD["verifiedBy"],
            },
        ),
    ]

    for city in GYEONGGI_CITIES:
        office_board = GYEONGGI_OFFICE_ATTACHMENT_BOARDS.get(city)
        council_board = GYEONGGI_COUNCIL_ATTACHMENT_BOARDS.get(city)
        agencies.extend(
            [
                Agency(
                    id=agency_uuid(f"gyeonggi:{city}:office"),
                    name=f"경기도 {city}청",
                    short_name=f"{city}청",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.ADMIN,
                    jurisdiction_type=JurisdictionType.SI,
                    parent_region="경기도",
                    sub_region=city,
                    homepage=office_board["homepage"] if office_board else None,
                    source_pattern={
                        "adapter": "attachment_board",
                        "listUrl": office_board["listUrl"],
                        "fileKinds": office_board["fileKinds"],
                        "followDetail": office_board.get("followDetail", True),
                        "pageParam": office_board["pageParam"],
                        "verifiedAt": office_board["verifiedAt"],
                        "verifiedBy": office_board["verifiedBy"],
                        **(
                            {"extraListUrls": office_board["extraListUrls"]}
                            if "extraListUrls" in office_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": office_board["jsDownloadPath"]}
                            if "jsDownloadPath" in office_board
                            else {}
                        ),
                    }
                    if office_board
                    else {
                        "adapter": "gg_office_required",
                        "searchKeyword": f"{city}청 업무추진비",
                        "status": "adapter_required",
                        **(
                            {
                                "holdStatus": "legal_hold",
                                "blocker": GYEONGGI_OFFICE_PENDING_BLOCKERS[city],
                            }
                            if city in GYEONGGI_OFFICE_PENDING_BLOCKERS
                            else {}
                        ),
                    },
                ),
                Agency(
                    id=agency_uuid(f"gyeonggi:{city}:council"),
                    name=f"경기도 {city}의회",
                    short_name=f"{city}의회",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.COUNCIL,
                    jurisdiction_type=JurisdictionType.SI,
                    parent_region="경기도",
                    sub_region=city,
                    homepage=council_board["homepage"] if council_board else None,
                    source_pattern={
                        "adapter": "council_attachment_board",
                        "listUrl": council_board["listUrl"],
                        "fileKinds": council_board["fileKinds"],
                        "followDetail": council_board.get("followDetail", False),
                        "pageParam": council_board["pageParam"],
                        "verifiedAt": council_board["verifiedAt"],
                        "verifiedBy": council_board["verifiedBy"],
                        **(
                            {"defaultFileKind": council_board["defaultFileKind"]}
                            if "defaultFileKind" in council_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": council_board["jsDownloadPath"]}
                            if "jsDownloadPath" in council_board
                            else {}
                        ),
                    }
                    if council_board
                    else {
                        "adapter": "gg_council_required",
                        "searchKeyword": f"{city}의회 업무추진비",
                        "status": "adapter_required",
                        **(
                            {
                                "holdStatus": "legal_hold",
                                "blocker": GYEONGGI_COUNCIL_PENDING_BLOCKERS[city],
                            }
                            if city in GYEONGGI_COUNCIL_PENDING_BLOCKERS
                            else {}
                        ),
                    },
                ),
            ]
        )

    for county in GYEONGGI_COUNTIES:
        office_board = GYEONGGI_OFFICE_ATTACHMENT_BOARDS.get(county)
        council_board = GYEONGGI_COUNCIL_ATTACHMENT_BOARDS.get(county)
        agencies.extend(
            [
                Agency(
                    id=agency_uuid(f"gyeonggi:{county}:office"),
                    name=f"경기도 {county}청",
                    short_name=f"{county}청",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.ADMIN,
                    jurisdiction_type=JurisdictionType.GUN,
                    parent_region="경기도",
                    sub_region=county,
                    homepage=office_board["homepage"] if office_board else None,
                    source_pattern={
                        "adapter": "attachment_board",
                        "listUrl": office_board["listUrl"],
                        "fileKinds": office_board["fileKinds"],
                        "followDetail": office_board.get("followDetail", True),
                        "pageParam": office_board["pageParam"],
                        "verifiedAt": office_board["verifiedAt"],
                        "verifiedBy": office_board["verifiedBy"],
                        **(
                            {"extraListUrls": office_board["extraListUrls"]}
                            if "extraListUrls" in office_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": office_board["jsDownloadPath"]}
                            if "jsDownloadPath" in office_board
                            else {}
                        ),
                    }
                    if office_board
                    else {
                        "adapter": "gg_office_required",
                        "searchKeyword": f"{county}청 업무추진비",
                        "status": "adapter_required",
                    },
                ),
                Agency(
                    id=agency_uuid(f"gyeonggi:{county}:council"),
                    name=f"경기도 {county}의회",
                    short_name=f"{county}의회",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.COUNCIL,
                    jurisdiction_type=JurisdictionType.GUN,
                    parent_region="경기도",
                    sub_region=county,
                    homepage=council_board["homepage"] if council_board else None,
                    source_pattern={
                        "adapter": "council_attachment_board",
                        "listUrl": council_board["listUrl"],
                        "fileKinds": council_board["fileKinds"],
                        "followDetail": council_board.get("followDetail", False),
                        "pageParam": council_board["pageParam"],
                        "verifiedAt": council_board["verifiedAt"],
                        "verifiedBy": council_board["verifiedBy"],
                        **(
                            {"defaultFileKind": council_board["defaultFileKind"]}
                            if "defaultFileKind" in council_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": council_board["jsDownloadPath"]}
                            if "jsDownloadPath" in council_board
                            else {}
                        ),
                    }
                    if council_board
                    else {
                        "adapter": "gg_council_required",
                        "searchKeyword": f"{county}의회 업무추진비",
                        "status": "adapter_required",
                    },
                ),
            ]
        )

    return agencies


def incheon_agencies() -> list[Agency]:
    agencies: list[Agency] = [
        Agency(
            id=agency_uuid("incheon:metro:office"),
            name="인천광역시청",
            short_name="인천시청",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.METRO_CITY,
            parent_region="인천광역시",
            sub_region=None,
            homepage=INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["homepage"],
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["listUrl"],
                "fileKinds": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["fileKinds"],
                "followDetail": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["followDetail"],
                "pageParam": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["pageParam"],
                "verifiedAt": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["verifiedAt"],
                "verifiedBy": INCHEON_METRO_OFFICE_ATTACHMENT_BOARD["verifiedBy"],
            },
        ),
        Agency(
            id=agency_uuid("incheon:metro:council"),
            name="인천광역시의회",
            short_name="인천시의회",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.METRO_CITY,
            parent_region="인천광역시",
            sub_region=None,
            homepage="https://www.icouncil.go.kr",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.icouncil.go.kr/main/participate/expense_office.jsp",
                "extraListUrls": ["https://www.icouncil.go.kr/main/participate/expense.jsp"],
                "fileKinds": ["pdf"],
                "defaultFileKind": "pdf",
                "pageParam": "pgno",
                "verifiedAt": "2026-06-01",
                "verifiedBy": "공식 사이트 화면·원격 확인",
            },
        ),
    ]

    for district in INCHEON_GUS:
        office_board = INCHEON_OFFICE_ATTACHMENT_BOARDS.get(district)
        council_board = INCHEON_COUNCIL_ATTACHMENT_BOARDS.get(district)
        agencies.extend(
            [
                Agency(
                    id=agency_uuid(f"incheon:{district}:office"),
                    name=f"인천광역시 {district}청",
                    short_name=f"{district}청",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.ADMIN,
                    jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
                    parent_region="인천광역시",
                    sub_region=district,
                    homepage=office_board["homepage"] if office_board else None,
                    source_pattern={
                        "adapter": "attachment_board",
                        "listUrl": office_board["listUrl"],
                        "fileKinds": office_board["fileKinds"],
                        "followDetail": office_board["followDetail"],
                        "pageParam": office_board["pageParam"],
                        "verifiedAt": office_board["verifiedAt"],
                        "verifiedBy": office_board["verifiedBy"],
                        **(
                            {"extraListUrls": office_board["extraListUrls"]}
                            if "extraListUrls" in office_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": office_board["jsDownloadPath"]}
                            if "jsDownloadPath" in office_board
                            else {}
                        ),
                    }
                    if office_board
                    else {
                        "adapter": "ic_office_required",
                        "searchKeyword": f"인천 {district}청 업무추진비",
                        "status": "adapter_required",
                    },
                ),
                Agency(
                    id=agency_uuid(f"incheon:{district}:council"),
                    name=f"인천광역시 {district}의회",
                    short_name=f"{district}의회",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.COUNCIL,
                    jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
                    parent_region="인천광역시",
                    sub_region=district,
                    homepage=council_board["homepage"] if council_board else None,
                    source_pattern={
                        "adapter": "council_attachment_board",
                        "listUrl": council_board["listUrl"],
                        "fileKinds": council_board["fileKinds"],
                        "followDetail": council_board["followDetail"],
                        "pageParam": council_board["pageParam"],
                        "verifiedAt": council_board["verifiedAt"],
                        "verifiedBy": council_board["verifiedBy"],
                        **(
                            {"jsDownloadPath": council_board["jsDownloadPath"]}
                            if "jsDownloadPath" in council_board
                            else {}
                        ),
                    }
                    if council_board
                    else {
                        "adapter": "ic_council_required",
                        "searchKeyword": f"인천 {district}의회 업무추진비",
                        "status": "adapter_required",
                        **(
                            {
                                "holdStatus": "legal_hold",
                                "blocker": INCHEON_COUNCIL_PENDING_BLOCKERS[district],
                            }
                            if district in INCHEON_COUNCIL_PENDING_BLOCKERS
                            else {}
                        ),
                    },
                ),
            ]
        )

    for county in INCHEON_COUNTIES:
        office_board = INCHEON_OFFICE_ATTACHMENT_BOARDS.get(county)
        council_board = INCHEON_COUNCIL_ATTACHMENT_BOARDS.get(county)
        agencies.extend(
            [
                Agency(
                    id=agency_uuid(f"incheon:{county}:office"),
                    name=f"인천광역시 {county}청",
                    short_name=f"{county}청",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.ADMIN,
                    jurisdiction_type=JurisdictionType.GUN,
                    parent_region="인천광역시",
                    sub_region=county,
                    homepage=office_board["homepage"] if office_board else None,
                    source_pattern={
                        "adapter": "attachment_board",
                        "listUrl": office_board["listUrl"],
                        "fileKinds": office_board["fileKinds"],
                        "followDetail": office_board["followDetail"],
                        "pageParam": office_board["pageParam"],
                        "verifiedAt": office_board["verifiedAt"],
                        "verifiedBy": office_board["verifiedBy"],
                        **(
                            {"extraListUrls": office_board["extraListUrls"]}
                            if "extraListUrls" in office_board
                            else {}
                        ),
                        **(
                            {"jsDownloadPath": office_board["jsDownloadPath"]}
                            if "jsDownloadPath" in office_board
                            else {}
                        ),
                    }
                    if office_board
                    else {
                        "adapter": "ic_office_required",
                        "searchKeyword": f"인천 {county}청 업무추진비",
                        "status": "adapter_required",
                    },
                ),
                Agency(
                    id=agency_uuid(f"incheon:{county}:council"),
                    name=f"인천광역시 {county}의회",
                    short_name=f"{county}의회",
                    gov_tier=GovTier.BASIC,
                    branch=GovBranch.COUNCIL,
                    jurisdiction_type=JurisdictionType.GUN,
                    parent_region="인천광역시",
                    sub_region=county,
                    homepage=council_board["homepage"] if council_board else None,
                    source_pattern={
                        "adapter": "council_attachment_board",
                        "listUrl": council_board["listUrl"],
                        "fileKinds": council_board["fileKinds"],
                        "followDetail": council_board["followDetail"],
                        "pageParam": council_board["pageParam"],
                        "verifiedAt": council_board["verifiedAt"],
                        "verifiedBy": council_board["verifiedBy"],
                        **(
                            {"jsDownloadPath": council_board["jsDownloadPath"]}
                            if "jsDownloadPath" in council_board
                            else {}
                        ),
                    }
                    if council_board
                    else {
                        "adapter": "ic_council_required",
                        "searchKeyword": f"인천 {county}의회 업무추진비",
                        "status": "adapter_required",
                    },
                ),
            ]
        )

    return agencies


def _apply_legal_hold(
    source_pattern: dict[str, object],
    blocker: str | dict[str, object] | None,
) -> None:
    if not blocker:
        return
    if isinstance(blocker, dict):
        source_pattern.update({"holdStatus": "legal_hold", **blocker})
        return
    source_pattern.update({"holdStatus": "legal_hold", "blocker": blocker})


def _apply_gyeongsang_source_not_found(
    source_pattern: dict[str, object],
    parent_region: str,
) -> None:
    if parent_region not in GYEONGSANG_PARENT_REGIONS:
        return
    if source_pattern.get("status") != "adapter_required" or source_pattern.get("holdStatus"):
        return

    keyword = str(source_pattern.get("searchKeyword") or "").strip()
    searched_paths = [
        keyword,
        "기관 공식 홈페이지/의회 사이트 정보공개·사전정보공표·업무추진비 메뉴",
    ]
    source_pattern.update(
        {
            "holdStatus": "source_not_found",
            "searchedPaths": searched_paths,
            "blocker": (
                "경상도권 2차 source discovery에서 source_registry 검색어 "
                f"'{keyword}'와 기관 공식 홈페이지/의회 사이트의 정보공개·사전정보공표·"
                "업무추진비 메뉴를 확인 경로로 분류했지만, dry-run 가능한 공공누리 "
                "제1유형 또는 명확한 상업적 자유이용 업무추진비 목록 URL을 확정하지 "
                "못했습니다."
            ),
        }
    )


CHUNGCHEONG_SOURCE_NOT_FOUND_EVIDENCE: dict[tuple[str, str], list[str]] = {
    ("대전광역시", "서구의회"): [
        "site:council.seogu.go.kr 업무추진비",
        "site:council.seogu.go.kr 의장 업무추진비",
        "https://council.seogu.go.kr",
        "대전 서구의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청북도", "충주시청"): [
        "site:chungju.go.kr 업무추진비",
        "site:chungju.go.kr 기관장 업무추진비",
        "https://www.chungju.go.kr",
        "충주시청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청북도", "제천시의회"): [
        "site:council.jecheon.go.kr 업무추진비",
        "site:council.jecheon.go.kr 의장 업무추진비",
        "https://council.jecheon.go.kr",
        "제천시의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청북도", "보은군청"): [
        "site:boeun.go.kr 업무추진비",
        "site:boeun.go.kr 군수 업무추진비",
        "https://www.boeun.go.kr",
        "보은군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청북도", "보은군의회"): [
        "site:council.boeun.go.kr 업무추진비",
        "site:council.boeun.go.kr 의장 업무추진비",
        "https://council.boeun.go.kr",
        "보은군의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청북도", "옥천군의회"): [
        "site:council.oc.go.kr 업무추진비",
        "site:council.oc.go.kr 의장 업무추진비",
        "https://council.oc.go.kr",
        "옥천군의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청북도", "영동군의회"): [
        "site:council.yd21.go.kr 업무추진비",
        "site:council.yd21.go.kr 의장 업무추진비",
        "https://council.yd21.go.kr",
        "영동군의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청북도", "증평군청"): [
        "site:jp.go.kr 업무추진비",
        "site:jp.go.kr 군수 업무추진비",
        "https://www.jp.go.kr",
        "증평군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청북도", "진천군청"): [
        "site:jincheon.go.kr 업무추진비",
        "site:jincheon.go.kr 군수 업무추진비",
        "https://www.jincheon.go.kr",
        "진천군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청북도", "음성군청"): [
        "site:eumseong.go.kr 업무추진비",
        "site:eumseong.go.kr 군수 업무추진비",
        "https://www.eumseong.go.kr",
        "음성군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청남도", "아산시의회"): [
        "site:asancouncil.go.kr 업무추진비",
        "site:asancouncil.go.kr 의장 업무추진비",
        "https://www.asancouncil.go.kr",
        "아산시의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청남도", "서산시의회"): [
        "site:scc.go.kr 업무추진비",
        "site:scc.go.kr 의장 업무추진비",
        "https://www.scc.go.kr",
        "서산시의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청남도", "금산군청"): [
        "site:geumsan.go.kr 업무추진비",
        "site:geumsan.go.kr 군수 업무추진비",
        "https://www.geumsan.go.kr",
        "금산군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청남도", "서천군의회"): [
        "site:scouncil.go.kr 업무추진비",
        "site:scouncil.go.kr 의장 업무추진비",
        "https://www.scouncil.go.kr",
        "서천군의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청남도", "청양군청"): [
        "site:cheongyang.go.kr 업무추진비",
        "site:cheongyang.go.kr 군수 업무추진비",
        "https://www.cheongyang.go.kr",
        "청양군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
    ("충청남도", "청양군의회"): [
        "site:council.cheongyang.go.kr 업무추진비",
        "site:council.cheongyang.go.kr 의장 업무추진비",
        "https://council.cheongyang.go.kr",
        "청양군의회 공식 홈페이지 정보공개·의정활동·공지사항 메뉴",
    ],
    ("충청남도", "홍성군청"): [
        "site:hongseong.go.kr 업무추진비",
        "site:hongseong.go.kr 군수 업무추진비",
        "https://www.hongseong.go.kr",
        "홍성군청 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
    ],
}


def _apply_chungcheong_source_not_found(
    source_pattern: dict[str, object],
    parent_region: str,
    short_name: str,
) -> None:
    if parent_region not in CHUNGCHEONG_PARENT_REGIONS:
        return
    if source_pattern.get("status") != "adapter_required" or source_pattern.get("holdStatus"):
        return

    searched_paths = CHUNGCHEONG_SOURCE_NOT_FOUND_EVIDENCE.get((parent_region, short_name))
    if not searched_paths:
        return

    keyword = str(source_pattern.get("searchKeyword") or "").strip()
    source_pattern.update(
        {
            "holdStatus": "source_not_found",
            "searchedPaths": searched_paths,
            "blocker": (
                "충청도권 2차 source discovery에서 source_registry 검색어 "
                f"'{keyword}'와 기관 공식 홈페이지/의회 사이트의 정보공개·사전정보공표·"
                "업무추진비 메뉴를 확인했지만, 공식 업무추진비 후보 URL을 확정하지 "
                "못했습니다. 최근 12개월 자료 존재 여부도 공식 출처 미발견 상태에서는 "
                "확정할 수 없어 dry-run 및 production 적재를 진행하지 않습니다."
            ),
        }
    )


def non_capital_agencies() -> list[Agency]:
    agencies: list[Agency] = []
    for (
        region_key,
        parent_region,
        office_name,
        office_short_name,
        council_name,
        council_short_name,
        jurisdiction_type,
    ) in NON_CAPITAL_REGIONAL_GOVERNMENTS:
        office_board = NON_CAPITAL_REGIONAL_OFFICE_ATTACHMENT_BOARDS.get(office_short_name)
        office_source_pattern = (
            {
                "adapter": "attachment_board",
                "listUrl": office_board["listUrl"],
                "fileKinds": office_board["fileKinds"],
                "followDetail": office_board["followDetail"],
                "pageParam": office_board["pageParam"],
                "verifiedAt": office_board["verifiedAt"],
                "verifiedBy": office_board["verifiedBy"],
                **(
                    {"extraListUrls": office_board["extraListUrls"]}
                    if "extraListUrls" in office_board
                    else {}
                ),
                **(
                    {"userAgent": office_board["userAgent"]}
                    if "userAgent" in office_board
                    else {}
                ),
                **(
                    {"jsDownloadPath": office_board["jsDownloadPath"]}
                    if "jsDownloadPath" in office_board
                    else {}
                ),
                **(
                    {"evidenceNote": office_board["evidenceNote"]}
                    if "evidenceNote" in office_board
                    else {}
                ),
            }
            if office_board
            else {
                "adapter": "nationwide_office_required",
                "searchKeyword": f"{office_name} 업무추진비",
                "status": "adapter_required",
            }
        )
        if not office_board:
            office_blocker = NON_CAPITAL_LEGAL_HOLD_BLOCKERS.get(office_short_name)
            _apply_legal_hold(office_source_pattern, office_blocker)
            _apply_gyeongsang_source_not_found(office_source_pattern, parent_region)
            _apply_chungcheong_source_not_found(
                office_source_pattern,
                parent_region,
                office_short_name,
            )

        council_board = NON_CAPITAL_REGIONAL_COUNCIL_ATTACHMENT_BOARDS.get(council_short_name)
        council_source_pattern = (
            {
                "adapter": "council_attachment_board",
                "listUrl": council_board["listUrl"],
                "fileKinds": council_board["fileKinds"],
                "followDetail": council_board["followDetail"],
                "pageParam": council_board["pageParam"],
                "verifiedAt": council_board["verifiedAt"],
                "verifiedBy": council_board["verifiedBy"],
                **(
                    {"extraListUrls": council_board["extraListUrls"]}
                    if "extraListUrls" in council_board
                    else {}
                ),
                **(
                    {"userAgent": council_board["userAgent"]}
                    if "userAgent" in council_board
                    else {}
                ),
                **(
                    {"jsDownloadPath": council_board["jsDownloadPath"]}
                    if "jsDownloadPath" in council_board
                    else {}
                ),
                **(
                    {"evidenceNote": council_board["evidenceNote"]}
                    if "evidenceNote" in council_board
                    else {}
                ),
            }
            if council_board
            else {
                "adapter": "nationwide_council_required",
                "searchKeyword": f"{council_name} 업무추진비",
                "status": "adapter_required",
            }
        )
        if not council_board:
            council_blocker = NON_CAPITAL_LEGAL_HOLD_BLOCKERS.get(council_short_name)
            _apply_legal_hold(council_source_pattern, council_blocker)
            _apply_gyeongsang_source_not_found(council_source_pattern, parent_region)
            _apply_chungcheong_source_not_found(
                council_source_pattern,
                parent_region,
                council_short_name,
            )

        agencies.extend(
            [
                Agency(
                    id=agency_uuid(f"{region_key}:regional:office"),
                    name=office_name,
                    short_name=office_short_name,
                    gov_tier=GovTier.REGIONAL,
                    branch=GovBranch.ADMIN,
                    jurisdiction_type=jurisdiction_type,
                    parent_region=parent_region,
                    sub_region=None,
                    homepage=office_board["homepage"] if office_board else None,
                    source_pattern=office_source_pattern,
                ),
                Agency(
                    id=agency_uuid(f"{region_key}:regional:council"),
                    name=council_name,
                    short_name=council_short_name,
                    gov_tier=GovTier.REGIONAL,
                    branch=GovBranch.COUNCIL,
                    jurisdiction_type=jurisdiction_type,
                    parent_region=parent_region,
                    sub_region=None,
                    homepage=council_board["homepage"] if council_board else None,
                    source_pattern=council_source_pattern,
                ),
            ]
        )

    for local_name in ("제주시", "서귀포시"):
        office_short_name = f"{local_name}청"
        office_board = JEJU_ADMINISTRATIVE_CITY_OFFICE_ATTACHMENT_BOARDS[office_short_name]
        agencies.append(
            Agency(
                id=agency_uuid(f"jeju:{local_name}:administrative-city:office"),
                name=f"제주특별자치도 {office_short_name}",
                short_name=office_short_name,
                gov_tier=GovTier.BASIC,
                branch=GovBranch.ADMIN,
                jurisdiction_type=JurisdictionType.SI,
                parent_region="제주특별자치도",
                sub_region=local_name,
                homepage=office_board["homepage"],
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": office_board["listUrl"],
                    "fileKinds": office_board["fileKinds"],
                    "followDetail": office_board["followDetail"],
                    "pageParam": office_board["pageParam"],
                    "verifiedAt": office_board["verifiedAt"],
                    "verifiedBy": office_board["verifiedBy"],
                    "evidenceNote": office_board["evidenceNote"],
                    **(
                        {"extraListUrls": office_board["extraListUrls"]}
                        if "extraListUrls" in office_board
                        else {}
                    ),
                },
            )
        )

    for region_key, parent_region, local_governments in NON_CAPITAL_BASIC_REGION_GROUPS:
        for local_name, jurisdiction_type in local_governments:
            office_short_name = f"{local_name}청"
            council_short_name = f"{local_name}의회"
            office_board = NON_CAPITAL_BASIC_OFFICE_ATTACHMENT_BOARDS.get(
                (parent_region, office_short_name)
            )
            council_board = NON_CAPITAL_BASIC_COUNCIL_ATTACHMENT_BOARDS.get(
                (parent_region, council_short_name)
            )
            office_blocker = NON_CAPITAL_BASIC_LEGAL_HOLD_BLOCKERS.get(
                (parent_region, office_short_name)
            )
            council_blocker = NON_CAPITAL_BASIC_LEGAL_HOLD_BLOCKERS.get(
                (parent_region, council_short_name)
            )
            office_source_pattern = (
                {
                    "adapter": "attachment_board",
                    "listUrl": office_board["listUrl"],
                    "fileKinds": office_board["fileKinds"],
                    "followDetail": office_board.get("followDetail", True),
                    "pageParam": office_board["pageParam"],
                    "verifiedAt": office_board["verifiedAt"],
                    "verifiedBy": office_board["verifiedBy"],
                    **(
                        {"extraListUrls": office_board["extraListUrls"]}
                        if "extraListUrls" in office_board
                        else {}
                    ),
                    **(
                        {"userAgent": office_board["userAgent"]}
                        if "userAgent" in office_board
                        else {}
                    ),
                    **(
                        {"jsDownloadPath": office_board["jsDownloadPath"]}
                        if "jsDownloadPath" in office_board
                        else {}
                    ),
                }
                if office_board
                else {
                    "adapter": "nationwide_office_required",
                    "searchKeyword": f"{parent_region} {office_short_name} 업무추진비",
                    "status": "adapter_required",
                }
            )
            council_source_pattern = (
                {
                    "adapter": "council_attachment_board",
                    "listUrl": council_board["listUrl"],
                    "fileKinds": council_board["fileKinds"],
                    "followDetail": council_board["followDetail"],
                    "pageParam": council_board["pageParam"],
                    "verifiedAt": council_board["verifiedAt"],
                    "verifiedBy": council_board["verifiedBy"],
                    **(
                        {"extraListUrls": council_board["extraListUrls"]}
                        if "extraListUrls" in council_board
                        else {}
                    ),
                    **(
                        {"userAgent": council_board["userAgent"]}
                        if "userAgent" in council_board
                        else {}
                    ),
                    **(
                        {"jsDownloadPath": council_board["jsDownloadPath"]}
                        if "jsDownloadPath" in council_board
                        else {}
                    ),
                }
                if council_board
                else {
                    "adapter": "nationwide_council_required",
                    "searchKeyword": f"{parent_region} {council_short_name} 업무추진비",
                    "status": "adapter_required",
                }
            )
            if office_blocker:
                office_source_pattern.update({"holdStatus": "legal_hold", **office_blocker})
            if council_blocker and not council_board:
                council_source_pattern.update({"holdStatus": "legal_hold", **council_blocker})
            _apply_gyeongsang_source_not_found(office_source_pattern, parent_region)
            _apply_gyeongsang_source_not_found(council_source_pattern, parent_region)
            _apply_chungcheong_source_not_found(
                office_source_pattern,
                parent_region,
                office_short_name,
            )
            _apply_chungcheong_source_not_found(
                council_source_pattern,
                parent_region,
                council_short_name,
            )
            agencies.extend(
                [
                    Agency(
                        id=agency_uuid(f"{region_key}:{local_name}:office"),
                        name=f"{parent_region} {office_short_name}",
                        short_name=office_short_name,
                        gov_tier=GovTier.BASIC,
                        branch=GovBranch.ADMIN,
                        jurisdiction_type=jurisdiction_type,
                        parent_region=parent_region,
                        sub_region=local_name,
                        homepage=office_board["homepage"] if office_board else None,
                        source_pattern=office_source_pattern,
                    ),
                    Agency(
                        id=agency_uuid(f"{region_key}:{local_name}:council"),
                        name=f"{parent_region} {council_short_name}",
                        short_name=council_short_name,
                        gov_tier=GovTier.BASIC,
                        branch=GovBranch.COUNCIL,
                        jurisdiction_type=jurisdiction_type,
                        parent_region=parent_region,
                        sub_region=local_name,
                        homepage=council_board["homepage"] if council_board else None,
                        source_pattern=council_source_pattern,
                    ),
                ]
            )

    return agencies


def central_state_agencies() -> list[Agency]:
    agencies: list[Agency] = []
    for row in central_state_baseline():
        is_constitutional = row.institution_type == "헌법기관"
        is_independent = row.institution_type == "독립국가기관"
        agencies.append(
            Agency(
                id=agency_uuid(f"p2:{row.name}"),
                name=row.name,
                short_name=row.name,
                gov_tier=(
                    GovTier.CONSTITUTIONAL if is_constitutional else GovTier.NATIONAL
                ),
                branch=(
                    GovBranch.CONSTITUTIONAL if is_constitutional else GovBranch.ADMIN
                ),
                jurisdiction_type=(
                    JurisdictionType.CONSTITUTIONAL_INSTITUTION
                    if is_constitutional
                    else JurisdictionType.INDEPENDENT_STATE_AGENCY
                    if is_independent
                    else JurisdictionType.CENTRAL_ADMINISTRATIVE_AGENCY
                ),
                expansion_phase=ExpansionPhase.P2,
                parent_region="대한민국",
                sub_region=row.institution_type,
                homepage=None,
                source_pattern=_central_state_source_pattern(row.name, row.institution_type),
            )
        )
    return agencies


def _central_state_source_pattern(name: str, institution_type: str) -> dict[str, object]:
    keyword = f"{name} 업무추진비"
    searched_paths = [
        keyword,
        f"{name} 공식 홈페이지 정보공개·사전정보공표·업무추진비 메뉴",
        f"{name} 기관장 업무추진비",
        f"{name} 장차관 업무추진비",
        "정보공개포털(open.go.kr) 업무추진비 검색",
        "정부조직관리정보시스템 기준 기관명 대조",
    ]
    return {
        "adapter": "central_state_required",
        "searchKeyword": keyword,
        "status": "adapter_required",
        "holdStatus": "source_not_found",
        "searchedPaths": searched_paths,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "P2-P4 공공부문 확장 조사",
        "baselineSourceUrl": CENTRAL_STATE_BASELINE_SOURCE_URL,
        "baselineAdditionalUrls": [CENTRAL_STATE_CHART_URL],
        "baselineEvidence": (
            "P2 공식 기준: 정부조직관리정보시스템 2026 정부기구도에서 "
            f"{institution_type} 기관명 확인."
        ),
        "blocker": (
            f"{name}은 정부조직관리정보시스템 2026 정부기구도에서 P2 {institution_type} "
            "기준 기관으로 확인했지만, 이번 P2-P4 조사에서 기관별 공식 홈페이지 정보공개·"
            "사전정보공표·업무추진비 메뉴, 기관장/장차관 업무추진비 키워드, 정보공개포털 "
            "검색 경로를 확인 대상으로 두고도 공무원맵 place-level 적재에 필요한 공식 원문 "
            "URL·공공누리 제1유형 또는 동등한 자유이용 근거·첨부 접근성을 확정하지 "
            "못했습니다. source URL 미발견 상태로 보류합니다."
        ),
    }


def public_institution_agencies() -> list[Agency]:
    agencies: list[Agency] = []
    for row in public_institution_baseline():
        agencies.append(
            Agency(
                id=agency_uuid(f"p3:{row.alio_id}:{row.name}"),
                name=row.name,
                short_name=row.name,
                gov_tier=GovTier.PUBLIC,
                branch=GovBranch.PUBLIC,
                jurisdiction_type=JurisdictionType.PUBLIC_INSTITUTION,
                expansion_phase=ExpansionPhase.P3,
                parent_region=row.supervising_ministry,
                sub_region=row.public_institution_type,
                homepage=row.homepage,
                source_pattern=_public_institution_source_pattern(
                    name=row.name,
                    public_institution_type=row.public_institution_type,
                    supervising_ministry=row.supervising_ministry,
                    alio_id=row.alio_id,
                ),
            )
        )
    return agencies


def _public_institution_source_pattern(
    *,
    name: str,
    public_institution_type: str,
    supervising_ministry: str,
    alio_id: str,
) -> dict[str, object]:
    baseline_evidence = (
        "P3 공식 기준: 잡알리오 2026 공공기관 지정현황과 재정경제부 "
        f"2026년도 공공기관 지정 자료에서 {public_institution_type} "
        f"기관명·주무부처({supervising_ministry})·상세ID({alio_id}) 확인."
    )
    common = {
        "searchKeyword": f"{name} 업무추진비",
        "sourceUrl": ALIO_WORKCOST_SOURCE_URL,
        "listUrl": ALIO_WORKCOST_LIST_API_URL,
        "reportFormRootNo": "20701",
        "dataName": "기관장 업무추진비",
        "licenseUrl": ALIO_COPYRIGHT_URL,
        "officialCommonPortal": True,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "ALIO 20701 JSON/첨부 샘플 원격 확인",
        "baselineSourceUrl": PUBLIC_INSTITUTION_BASELINE_SOURCE_URL,
        "baselineAdditionalUrls": [PUBLIC_INSTITUTION_MOEF_SOURCE_URL, ALIO_COPYRIGHT_URL],
        "baselineEvidence": baseline_evidence,
    }
    if name in P3_ALIO_PLACE_LEVEL_CANDIDATES:
        return {
            **common,
            "adapter": "alio_item_disclosure",
            "alioAgencyName": name,
            "fileKinds": ["xlsx"],
            "evidenceNote": (
                "ALIO 경영공시 항목 20701(기관장 업무추진비)에서 2025년 XLSX 첨부를 확인했고, "
                "샘플 원문은 사용일자·사용처/장소·집행금액 place-level 행을 포함합니다. "
                "ALIO 저작권 정책을 근거로 출처표시 조건의 사실 데이터만 정규화합니다."
            ),
        }
    hold_status = "no_recent_data"
    file_kinds = ["xlsx"]
    blocker = (
        "잡알리오 기준 지정 공공기관으로 확인했고, ALIO 경영공시 항목 20701(기관장 "
        "업무추진비) 공식 목록과 2025년 첨부 후보를 확인했지만, 샘플 dry-run 분류에서 "
        "2025-06-01 이후 place-level 식당/장소 행이 검출되지 않았습니다. 최근 12개월 "
        "적재 대상 0건으로 보류합니다."
    )
    if name in P3_ALIO_RECENT_AGGREGATE_ONLY:
        blocker = (
            "ALIO 20701 첨부와 최근 12개월 원문은 확인했지만, 재검증한 XLSX 원문이 "
            "월/유형/건수/금액 집계표이며 사용처·장소·상호 place-level 열을 포함하지 "
            "않습니다. 공무원맵 적재 대상 place-level 최근 12개월 데이터 0건으로 보류합니다."
        )
    elif name in P3_ALIO_AMOUNT_THOUSANDS_NEEDS_PATCH:
        hold_status = "adapter_hold"
        blocker = (
            "ALIO 20701 첨부에서 최근 12개월 place-level 후보가 보이나 금액 헤더가 천원 "
            "단위이거나 단위 판정이 필요한 구조입니다. 원 단위 보정 없는 production write는 "
            "금액 오적재 위험이 있어 spreadsheet parser 단위 보정 패치 후 재검증해야 합니다."
        )
    elif name in P3_ALIO_PDF_VISION_HOLD:
        hold_status = "pdf_vision_hold"
        file_kinds = ["pdf"]
        blocker = (
            "ALIO 20701 첨부가 PDF입니다. text PDF와 scanned PDF를 분리하고 vision "
            "429/timeout 정책을 적용하는 공공기관 PDF 검증 전까지 production 적재하지 않습니다."
        )
    elif name in P3_ALIO_HWP_PARSER_HOLD:
        hold_status = "adapter_hold"
        file_kinds = ["hwp"]
        blocker = (
            "ALIO 20701 첨부가 HWP입니다. 현재 안전 dry-run 경로는 HWP 원문 추출을 보장하지 "
            "못하므로 HWP extractor/변환 adapter 패치 후 재검증해야 합니다."
        )
    elif name in P3_ALIO_DOWNLOAD_HOLD:
        hold_status = "adapter_hold"
        blocker = (
            "ALIO 20701 목록에는 기관장 업무추진비 항목이 있으나 샘플 다운로드에서 fileNo 누락, "
            "500 응답, 또는 파일 경로 매핑 실패가 확인됐습니다. ALIO 첨부 선택/다운로드 adapter "
            "보강 후 재검증해야 합니다."
        )
    elif name in P3_ALIO_XLS_PARSER_HOLD:
        hold_status = "adapter_hold"
        file_kinds = ["xls"]
        blocker = (
            "ALIO 20701 첨부가 XLS 중심입니다. 일부 파일은 place-level 가능성이 있으나 기관별 "
            "시트 구조와 최근 12개월 필터를 안정적으로 판정하는 XLS parser 보강 후 재검증해야 합니다."
        )
    return {
        **common,
        "adapter": "public_institution_required",
        "status": "adapter_required",
        "holdStatus": hold_status,
        "fileKinds": file_kinds,
        "blocker": blocker,
    }


def local_public_institution_agencies() -> list[Agency]:
    agencies: list[Agency] = []
    for index, row in enumerate(local_public_institution_baseline(), start=1):
        agencies.append(
            Agency(
                id=agency_uuid(f"p4:{index}:{row.parent_region}:{row.sub_region}:{row.name}"),
                name=row.name,
                short_name=row.short_name,
                gov_tier=GovTier.LOCAL_PUBLIC,
                branch=GovBranch.PUBLIC,
                jurisdiction_type=JurisdictionType.LOCAL_PUBLIC_INSTITUTION,
                expansion_phase=ExpansionPhase.P4,
                parent_region=row.parent_region,
                sub_region=row.sub_region,
                homepage=None,
                source_pattern=_local_public_institution_source_pattern(
                    name=row.name,
                    institution_type=row.institution_type,
                    institution_subtype=row.institution_subtype,
                ),
            )
        )
    return agencies


def _local_public_institution_source_pattern(
    *,
    name: str,
    institution_type: str,
    institution_subtype: str,
) -> dict[str, object]:
    is_public_enterprise = institution_type == "지방공기업"
    source_url = (
        CLEANEYE_PUBLIC_ENTERPRISE_WORKCOST_URL
        if is_public_enterprise
        else CLEANEYE_LOCAL_FOUNDATION_DISCLOSURE_URL
    )
    extra_urls = (
        [CLEANEYE_PUBLIC_ENTERPRISE_DISCLOSURE_URL]
        if is_public_enterprise
        else [CLEANEYE_PUBLIC_ENTERPRISE_WORKCOST_URL]
    )
    if name in P4_CLEANEYE_PLACE_LEVEL_CANDIDATES:
        cleaneye = P4_CLEANEYE_PLACE_LEVEL_CANDIDATES[name]
        return {
            "adapter": "cleaneye_owner_work_cost",
            "searchKeyword": f"{name} 업무추진비",
            "sourceUrl": CLEANEYE_PUBLIC_ENTERPRISE_OWNER_WORKCOST_URL,
            "extraListUrls": [CLEANEYE_PUBLIC_ENTERPRISE_DISCLOSURE_URL],
            "entId": cleaneye["entId"],
            "entKind": cleaneye["entKind"],
            "entName": cleaneye["entName"],
            "itemId": "ownerWorkCost",
            "dataName": "기관장 업무추진비",
            "fileKinds": ["xlsx"],
            "licenseUrl": CLEANEYE_COPYRIGHT_URL,
            "officialCommonPortal": True,
            "verifiedAt": "2026-06-02",
            "verifiedBy": "P2-P4 2차 CleanEye entId/file download dry-run 후보 검증",
            "baselineSourceUrl": LOCAL_PUBLIC_BASELINE_SOURCE_URL,
            "baselineAdditionalUrls": [
                CLEANEYE_PUBLIC_ENTERPRISE_WORKCOST_URL,
                CLEANEYE_COPYRIGHT_URL,
            ],
            "baselineEvidence": (
                "P4 공식 기준: 클린아이 정책자료의 2026.3.31 기준 첨부에서 "
                f"{institution_type}/{institution_subtype} 기관명 확인."
            ),
            "evidenceNote": (
                "CleanEye 기관별공시에서 entId/itemId=ownerWorkCost 상세 페이지와 "
                "fn_FileDown(/file/fileExists.do -> /file/FileDownload.do) XLSX 첨부를 "
                "확인했습니다. 2025년 2분기 원문은 사용일자·집행목적·장소·대상인원·"
                "지출금액(원) place-level 행을 포함합니다."
            ),
        }
    if name in P4_CLEANEYE_RECENT_AGGREGATE_ONLY:
        cleaneye = P4_CLEANEYE_RECENT_AGGREGATE_ONLY[name]
        return {
            "adapter": "local_public_institution_required",
            "searchKeyword": f"{name} 업무추진비",
            "status": "adapter_required",
            "holdStatus": "no_recent_data",
            "sourceUrl": CLEANEYE_PUBLIC_ENTERPRISE_DISCLOSURE_URL,
            "extraListUrls": [CLEANEYE_PUBLIC_ENTERPRISE_WORKCOST_URL],
            "entId": cleaneye["entId"],
            "entKind": cleaneye["entKind"],
            "entName": cleaneye["entName"],
            "dataName": "기관장 업무추진비",
            "fileKinds": ["xlsx"],
            "licenseUrl": CLEANEYE_COPYRIGHT_URL,
            "verifiedAt": "2026-06-02",
            "verifiedBy": "P2-P4 2차 CleanEye 첨부 구조 재검증",
            "baselineSourceUrl": LOCAL_PUBLIC_BASELINE_SOURCE_URL,
            "baselineAdditionalUrls": [CLEANEYE_COPYRIGHT_URL],
            "baselineEvidence": (
                "P4 공식 기준: 클린아이 정책자료의 2026.3.31 기준 첨부에서 "
                f"{institution_type}/{institution_subtype} 기관명 확인."
            ),
            "blocker": (
                "CleanEye 기관별공시에서 최근 12개월 XLSX 첨부는 확인했지만, 원문이 "
                "유형별/월별 건수·금액 집계표이며 사용처·장소·상호 place-level 열을 "
                "포함하지 않습니다. 공무원맵 적재 대상 최근 12개월 place-level 데이터 "
                "0건으로 보류합니다."
            ),
        }
    return {
        "adapter": "local_public_institution_required",
        "searchKeyword": f"{name} 업무추진비",
        "status": "adapter_required",
        "holdStatus": "adapter_hold",
        "sourceUrl": source_url,
        "extraListUrls": extra_urls,
        "dataName": "기관장 업무추진비",
        "fileKinds": ["xlsx", "hwpx", "pdf"],
        "licenseUrl": CLEANEYE_COPYRIGHT_URL,
        "verifiedAt": "2026-06-02",
        "verifiedBy": "CleanEye 기관장 업무추진비 공통 포털 조사",
        "baselineSourceUrl": LOCAL_PUBLIC_BASELINE_SOURCE_URL,
        "baselineAdditionalUrls": [CLEANEYE_COPYRIGHT_URL],
        "baselineEvidence": (
            "P4 공식 기준: 클린아이 정책자료의 2026.3.31 기준 첨부에서 "
            f"{institution_type}/{institution_subtype} 기관명 확인."
        ),
        "blocker": (
            "클린아이에서 기관장 업무추진비 공시/통계 및 공공데이터 자유활용 정책은 확인했습니다. "
            "다만 현 pipeline에는 CleanEye entId/itemId/itemNo 연계, 분기별 첨부 다운로드 "
            "fn_FileDown(/file/FileDownload.do), 기관명 정규화 매핑, aggregate 통계와 place-level "
            "세부내역 분리 로직이 없습니다. CleanEye adapter/parser 패치 후 dry-run 검증 전까지 "
            "production 적재하지 않습니다."
        ),
    }


SEOUL_AGENCIES = seoul_agencies()
GYEONGGI_AGENCIES = gyeonggi_agencies()
INCHEON_AGENCIES = incheon_agencies()
NON_CAPITAL_AGENCIES = non_capital_agencies()
CENTRAL_STATE_AGENCIES = central_state_agencies()
PUBLIC_INSTITUTION_AGENCIES = public_institution_agencies()
LOCAL_PUBLIC_INSTITUTION_AGENCIES = local_public_institution_agencies()
CAPITAL_AREA_AGENCIES = SEOUL_AGENCIES + GYEONGGI_AGENCIES + INCHEON_AGENCIES
LOCAL_GOVERNMENT_AGENCIES = CAPITAL_AREA_AGENCIES + NON_CAPITAL_AGENCIES
NATIONWIDE_AGENCIES = (
    LOCAL_GOVERNMENT_AGENCIES
    + CENTRAL_STATE_AGENCIES
    + PUBLIC_INSTITUTION_AGENCIES
    + LOCAL_PUBLIC_INSTITUTION_AGENCIES
)

assert len(SEOUL_AGENCIES) == 52
assert len(GYEONGGI_AGENCIES) == 64
assert len(INCHEON_AGENCIES) == 22
assert len(NON_CAPITAL_AGENCIES) == 350
assert len(LOCAL_GOVERNMENT_AGENCIES) == 488
assert len(CENTRAL_STATE_AGENCIES) == 60
assert len(PUBLIC_INSTITUTION_AGENCIES) == 342
assert len(LOCAL_PUBLIC_INSTITUTION_AGENCIES) == 1312
assert len(NATIONWIDE_AGENCIES) == 2202
assert SEOUL_AGENCIES[0].id == SEOUL_CITY_HALL_AGENCY_ID
assert len(CAPITAL_AREA_AGENCIES) == 138
