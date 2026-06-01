import pytest

from public_officer_pipeline.agencies import GYEONGGI_AGENCIES, INCHEON_AGENCIES, SEOUL_AGENCIES
from public_officer_pipeline.models import Agency
from public_officer_pipeline.source_pattern import (
    AdapterRequiredPattern,
    SourcePatternError,
    parse_source_pattern,
)


def test_parse_source_patterns_for_all_seoul_agencies() -> None:
    for agency in SEOUL_AGENCIES:
        parse_source_pattern(agency)


def test_parse_gyeonggi_and_incheon_require_adapter_required_pattern() -> None:
    pending_agencies = [
        agency for agency in GYEONGGI_AGENCIES + INCHEON_AGENCIES
        if agency.short_name
        not in {
            "경기도의회",
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
            "안성시청",
            "수원시의회",
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
            "양평군청",
            "양평군의회",
            "광주시청",
            "가평군청",
            "인천시의회",
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
    ]
    for agency in pending_agencies:
        parsed = parse_source_pattern(agency)
        assert isinstance(parsed, AdapterRequiredPattern)
        assert parsed.status == "adapter_required"


def test_parse_verified_incheon_council_attachment_pattern() -> None:
    agency = next(agency for agency in INCHEON_AGENCIES if agency.short_name == "인천시의회")
    parsed = parse_source_pattern(agency)

    assert parsed.adapter == "council_attachment_board"
    assert parsed.listUrl == "https://www.icouncil.go.kr/main/participate/expense_office.jsp"
    assert parsed.extraListUrls == ["https://www.icouncil.go.kr/main/participate/expense.jsp"]
    assert parsed.defaultFileKind == "pdf"


def test_parse_verified_suwon_council_attachment_pattern() -> None:
    agency = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == "수원시의회")
    parsed = parse_source_pattern(agency)

    assert parsed.adapter == "council_attachment_board"
    assert parsed.listUrl == "https://council.suwon.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd="
    assert parsed.fileKinds == ["xls", "xlsx", "pdf"]
    assert parsed.pageParam == "page"


@pytest.mark.parametrize(
    ("short_name", "list_url", "page_param", "follow_detail"),
    [
        (
            "경기도의회",
            "https://www.ggc.go.kr/site/main/disclosureinfo/ParliaOper/duty/list?sortOrder=DT_USE_DT&listType=list",
            "cp",
            False,
        ),
        ("성남시의회", "https://www.sncouncil.go.kr/kr/news/bbsCost.do", "pageNum", True),
        (
            "의정부시의회",
            "https://www.ujbcl.go.kr/svc/bbs/BusinessList.do?bbsMnuCd=MNU002300000650400000666",
            "pageNo",
            True,
        ),
        ("동두천시의회", "https://council.ddc.go.kr/kr/news/bbsCost.do", "pageNum", True),
        ("광명시의회", "https://council.gm.go.kr/kr/costBBS.do", "page", True),
        ("고양시의회", "https://www.goyangcouncil.go.kr/kr/costBBS.do", "page", True),
        ("구리시의회", "https://www.gcc.or.kr/board/news/list.do?tbname=cost", "pageIndex", False),
        ("남양주시의회", "https://nyjc.go.kr/content/dataroom/propelclosed.html", "page", True),
        ("용인시의회", "https://council.yongin.go.kr/kr/costBBS.do", "page", True),
        ("부천시의회", "https://council.bucheon.go.kr/kr/intro/bbsInfo.do", "pageNum", True),
        ("안양시의회", "https://www.aycouncil.go.kr/kr/costBBSlist.do?page=1", "page", False),
        (
            "군포시의회",
            "https://www.gunpocouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
            "page",
            True,
        ),
        ("의왕시의회", "https://council.uiwang.go.kr/kr/news/bbsCost.do?flag=&keyword=", "pageNum", True),
        ("과천시의회", "https://www.gccouncil.go.kr/kr/costBBSlist.do?page=1", "page", True),
        ("오산시의회", "https://www.osancouncil.go.kr/kr/news/bbs?bbs_id=work", "page", True),
        ("시흥시의회", "https://www.siheungcouncil.go.kr/content/activity/business.html", "page", True),
        ("하남시의회", "https://council.hanam.go.kr/content/community/business.html", "page", True),
        ("파주시의회", "https://www.pajucouncil.go.kr/content/data/operatingExpense.html", "page", True),
        (
            "광주시의회",
            "https://www.gjcouncil.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
            "page",
            True,
        ),
        ("양주시의회", "https://yjcc.yangju.go.kr/yjcc/selectBbsNttList.do?bbsNo=302&key=2559", "pageIndex", True),
        (
            "이천시의회",
            "https://council.icheon.go.kr/content/information/businessOperatingExpense.html",
            "page",
            True,
        ),
        (
            "안성시의회",
            "https://www.anseongcl.go.kr/kr/costBBS.do?flag=all&list_style=&schwrd=",
            "page",
            False,
        ),
        (
            "김포시의회",
            "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702",
            "pageNo",
            True,
        ),
        (
            "화성시의회",
            "https://council.hscity.go.kr/cnts/bbs/boardList.php?bbsCd=cns&bbsSubCd=cns08",
            "pageNo",
            True,
        ),
        ("포천시의회", "https://council.pocheon.go.kr/kr/news/bbsBusiness.do", "page", True),
        ("여주시의회", "https://www.yeojucouncil.go.kr/kr/costBBS.do", "page", True),
        ("연천군의회", "https://www.yca21.go.kr/board/news/list.do?tbname=cost", "pageIndex", False),
        ("가평군의회", "https://www.gpassem.go.kr/kr/operations2BBS.do", "page", False),
        ("양평군의회", "https://www.ypcouncil.go.kr/main/selectBbsNttList.do?bbsNo=9&key=43", "pageIndex", True),
    ],
)
def test_parse_verified_gyeonggi_council_attachment_patterns(
    short_name: str,
    list_url: str,
    page_param: str,
    follow_detail: bool,
) -> None:
    agency = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == short_name)
    parsed = parse_source_pattern(agency)

    assert parsed.adapter == "council_attachment_board"
    assert parsed.listUrl == list_url
    assert parsed.followDetail is follow_detail
    assert parsed.pageParam == page_param


@pytest.mark.parametrize(
    ("short_name", "list_url", "page_param", "follow_detail"),
    [
        ("수원시청", "https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179", "page", True),
        (
            "성남시청",
            "https://www.seongnam.go.kr/city/1000199/30218/bbsList.do",
            "currentPage",
            True,
        ),
        (
            "평택시청",
            "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000",
            "page",
            True,
        ),
        (
            "안양시청",
            "https://www.anyang.go.kr/main/selectBbsNttList.do?bbsNo=43&key=218",
            "pageIndex",
            True,
        ),
        (
            "의정부시청",
            "https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25",
            "pageIndex",
            True,
        ),
        (
            "동두천시청",
            "https://www.ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122",
            "pageIndex",
            True,
        ),
        (
            "안산시청",
            "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471",
            "currentPage",
            True,
        ),
        (
            "부천시청",
            "https://www.bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002",
            "currentpage",
            True,
        ),
        (
            "고양시청",
            "https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do?q_publictClCode=3062&q_searchKeyTy=1001&q_searchVal=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84",
            "q_currPage",
            False,
        ),
        (
            "김포시청",
            "https://www.gimpo.go.kr/portal/selectBbsNttList.do?bbsNo=199&key=1110",
            "pageIndex",
            True,
        ),
        ("하남시청", "https://www.hanam.go.kr/www/selectBbsNttList.do?bbsNo=15&key=51", "pageIndex", True),
        (
            "광명시청",
            "https://www.gm.go.kr/pt/user/bbs/BD_selectBbsList.do?q_bbsCode=2472",
            "page",
            True,
        ),
        ("구리시청", "https://www.guri.go.kr/www/selectBbsNttList.do?bbsNo=14&key=331", "pageIndex", True),
        (
            "남양주시청",
            "https://www.nyj.go.kr/www/selectBbsNttList.do?key=2432&bbsNo=43",
            "pageIndex",
            True,
        ),
        (
            "오산시청",
            "https://www.osan.go.kr/portal/bbs/list.do?ptIdx=176&mId=0203010000",
            "page",
            True,
        ),
        (
            "군포시청",
            "https://www.gunpo.go.kr/www/selectBbsNttList.do?bbsNo=715&key=4276",
            "pageIndex",
            True,
        ),
        ("의왕시청", "https://www.uiwang.go.kr/UWKOROPEN0210", "curPage", True),
        (
            "용인시청",
            "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6",
            "q_currPage",
            True,
        ),
        (
            "파주시청",
            "https://www.paju.go.kr/user/policy_02/board/BD_board.list.do?bbsCd=1018",
            "page",
            True,
        ),
        ("양주시청", "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=30&key=234", "pageIndex", True),
        (
            "포천시청",
            "https://www.pocheon.go.kr/www/selectBbsNttList.do?bbsNo=214&key=3687",
            "pageIndex",
            True,
        ),
        (
            "연천군청",
            "https://www.yeoncheon.go.kr/www/selectBbsNttList.do?bbsNo=152&key=3352",
            "pageIndex",
            True,
        ),
        ("양평군청", "https://www.yp21.go.kr/www/selectBbsNttList.do?bbsNo=43&key=1597", "pageIndex", True),
        (
            "안성시청",
            "https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000",
            "page",
            False,
        ),
        (
            "과천시청",
            "https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000",
            "page",
            True,
        ),
        (
            "광주시청",
            "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53",
            "page",
            True,
        ),
        (
            "가평군청",
            "https://www.gp.go.kr/portal/selectBbsNttList.do?bbsNo=78&key=454",
            "pageIndex",
            True,
        ),
    ],
)
def test_parse_verified_gyeonggi_office_attachment_patterns(
    short_name: str,
    list_url: str,
    page_param: str,
    follow_detail: bool,
) -> None:
    agency = next(agency for agency in GYEONGGI_AGENCIES if agency.short_name == short_name)
    parsed = parse_source_pattern(agency)

    assert parsed.adapter == "attachment_board"
    assert parsed.listUrl == list_url
    assert parsed.followDetail is follow_detail
    assert parsed.pageParam == page_param


@pytest.mark.parametrize(
    ("short_name", "list_url", "adapter", "page_param", "follow_detail"),
    [
        ("인천시청", "https://www.incheon.go.kr/open/OPEN010305", "attachment_board", "curPage", True),
        ("중구청", "https://www.icjg.go.kr/krop0307c", "attachment_board", "curPage", True),
        (
            "계양구청",
            "https://www.gyeyang.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=board_14&cate1=94",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "서구청",
            "https://www.seo.incheon.kr/open_content/main/bbs/bbsMsgList.do?bcd=clean_cost",
            "attachment_board",
            "pgno",
            True,
        ),
        (
            "미추홀구청",
            "https://www.michuhol.go.kr/main/board/list.do?board_code=business_promotion&dept_sq=333&page=1&srchCate=&year=",
            "attachment_board",
            "page",
            True,
        ),
        (
            "연수구청",
            "https://www.yeonsu.go.kr/main/administration/open_info/charge.asp",
            "attachment_board",
            "gotopage",
            True,
        ),
        (
            "부평구청",
            "https://www.icbp.go.kr/main/bbs/bbsMsgList.do?bcd=cost",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "남동구청",
            "https://biz.namdong.go.kr/main/bbs/bbsMsgList.do?bcd=disclosure",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "동구청",
            "https://www.icdonggu.go.kr/main/bbs/bbsMsgList.do?bcd=notice&keyfield=title&keyword=%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "중구의회",
            "https://www.icjg.go.kr/council/cnac04b",
            "council_attachment_board",
            "curPage",
            True,
        ),
        (
            "남동구의회",
            "https://council.namdong.go.kr/kr/data/bbsBreakdown.do",
            "council_attachment_board",
            "pageNum",
            True,
        ),
        (
            "서구의회",
            "https://www.seo.incheon.kr/open_content/council/activity/open.jsp",
            "council_attachment_board",
            "pgno",
            False,
        ),
        (
            "동구의회",
            "https://council.icdonggu.go.kr/kr/costBBS.do",
            "council_attachment_board",
            "page",
            True,
        ),
        (
            "연수구의회",
            "https://council.yeonsu.go.kr/kr/businessBBS.do",
            "council_attachment_board",
            "page",
            True,
        ),
        (
            "부평구의회",
            "https://council.icbp.go.kr/kr/data/bbs?bbs_id=expense",
            "council_attachment_board",
            "page",
            True,
        ),
        (
            "계양구의회",
            "https://council.gyeyang.go.kr/kr/costBBS.do",
            "council_attachment_board",
            "page",
            True,
        ),
        (
            "강화군청",
            "https://www.ganghwa.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=operation",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "옹진군청",
            "https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1",
            "attachment_board",
            "pgno",
            False,
        ),
        (
            "강화군의회",
            "https://council.ganghwa.go.kr/kr/workBBS.do",
            "council_attachment_board",
            "page",
            True,
        ),
        (
            "옹진군의회",
            "https://council.ongjin.go.kr/kr/costBBS.do",
            "council_attachment_board",
            "page",
            True,
        ),
    ],
)
def test_parse_verified_incheon_attachment_patterns(
    short_name: str,
    list_url: str,
    adapter: str,
    page_param: str,
    follow_detail: bool,
) -> None:
    agency = next(agency for agency in INCHEON_AGENCIES if agency.short_name == short_name)
    parsed = parse_source_pattern(agency)

    assert parsed.adapter == adapter
    assert parsed.listUrl == list_url
    assert parsed.followDetail is follow_detail
    assert parsed.pageParam == page_param


def test_attachment_pattern_missing_list_url_raises() -> None:
    with pytest.raises(SourcePatternError):
        parse_source_pattern(
            Agency(
                source_pattern={
                    "adapter": "attachment_board",
                    "fileKinds": ["pdf"],
                }
            )
        )


def test_attachment_pattern_invalid_file_kind_raises() -> None:
    with pytest.raises(SourcePatternError):
        parse_source_pattern(
            Agency(
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "https://example.com/list",
                    "fileKinds": ["exe", "zip"],
                }
            )
        )
