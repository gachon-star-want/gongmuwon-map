from datetime import date
from urllib.parse import parse_qs, urlsplit

import public_officer_pipeline.crawler.gncouncil as gncouncil
from public_officer_pipeline.crawler.gncouncil import (
    CouncilAttachmentCrawler,
    GangnamCouncilCrawler,
    _url_with_page,
)
from public_officer_pipeline.models import Agency, GovTier, GovBranch, JurisdictionType, PostRef


def test_gncouncil_crawler_extracts_pdf_refs() -> None:
    crawler = GangnamCouncilCrawler()

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>530</td>
            <td class="con"><a href="/kr/noticeBBSview.do?uid=post">2026.1.1. ~ 3.31. 강남구의회 의장단 및 교섭단체 업무추진비 사용내역</a></td>
            <td>강남구의회</td>
            <td>2026-04-07</td>
            <td>598</td>
            <td>
              <a href="/kr/bbs/download.do?bbs_id=notice&uid=file1"><span class="name">붙임1 (의장) 업무추진비 공개.pdf</span></a>
              <a href="/kr/bbs/download.do?bbs_id=notice&uid=file2"><span class="name">참고자료.png</span></a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.gncouncil.go.kr/kr/bbs/download.do?bbs_id=notice&uid=file1"
    assert refs[0].department_name == "강남구의회 의장"
    assert refs[0].file_kind == "pdf"


def test_url_with_page_preserves_existing_query_params() -> None:
    url = _url_with_page("https://www.ycc.go.kr/kr/news/bbs?bbs_id=business", 2)

    assert url == "https://www.ycc.go.kr/kr/news/bbs?bbs_id=business&page=2"


def test_url_with_page_supports_custom_pagination_params() -> None:
    url = _url_with_page(
        "https://www.jungnang.go.kr/portal/bbs/list/B0000143.do?menuNo=200432",
        2,
        page_param="pageIndex",
        page_unit_param="pageUnit",
        rows_per_page=10,
    )

    assert url == (
        "https://www.jungnang.go.kr/portal/bbs/list/B0000143.do"
        "?menuNo=200432&pageIndex=2&pageUnit=10"
    )


def test_council_attachment_crawler_uses_pattern_user_agent(monkeypatch) -> None:
    captured: dict[str, dict[str, str]] = {}

    class DummyClient:
        async def aclose(self) -> None:
            return None

    def fake_create_http_client(*, timeout, headers, follow_redirects):
        captured["headers"] = headers
        return DummyClient()

    monkeypatch.setattr(gncouncil, "create_http_client", fake_create_http_client)

    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="진도군청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="전라남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.jindo.go.kr/home/board/B0071.cs?m=52",
                "userAgent": "Mozilla/5.0 (compatible; PublicOfficerMapBot/0.1)",
            },
        )
    )

    assert crawler.user_agent == "Mozilla/5.0 (compatible; PublicOfficerMapBot/0.1)"
    assert captured["headers"]["User-Agent"] == crawler.user_agent


def test_council_attachment_crawler_extracts_cost_xlsx_refs_from_title_attribute() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="강서구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://gsc.gangseo.seoul.kr/kr/costBBS.do",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>92</td>
            <td class="con"><a href="/kr/costBBSview.do?uid=post">의장 업무추진비 지출내역(25.11.)</a></td>
            <td>강서구의회</td>
            <td>2026-01-15</td>
            <td>143</td>
            <td>
              <a href="/kr/bbs/download.do?bbs_id=cost&uid=file1" title="'의장 업무추진비 지출내역(25. 11월).xlsx' 파일 내려받기">
                <img class="attach" src="/images/board/file.gif" alt="첨부 파일" />
              </a>
              <a href="/kr/bbs/download.do?bbs_id=cost&uid=file2" title="'2026년 공통경비 집행내역.xlsx' 파일 내려받기">
                <img class="attach" src="/images/board/file.gif" alt="첨부 파일" />
              </a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == "https://gsc.gangseo.seoul.kr/kr/bbs/download.do?bbs_id=cost&uid=file1"
    assert refs[0].department_name == "강서구의회 의장"
    assert refs[0].file_kind == "xlsx"


def test_council_attachment_crawler_extracts_incheon_file_list_items() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="인천시의회",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.METRO_CITY,
            parent_region="인천광역시",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.icouncil.go.kr/main/participate/expense_office.jsp",
                "fileKinds": ["pdf"],
                "defaultFileKind": "pdf",
                "pageParam": "pgno",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <ul class="board_list">
          <li>
            <p class="title">
              <a href="/main/bbs/bbsMsgDetail.do?msg_seq=1331&amp;bcd=infordisc5_3">
                2026년 4월 산업경제수석전문위원 업무추진비 집행내역
              </a>
            </p>
            <div class="writer_info">
              <ul>
                <li class="writer" title="작성자">전문위원</li>
                <li class="center" title="작성일">2026.05.11</li>
                <li class="file">
                  <a href="/main/bbs/bbsMsgFileDown.do?bcd=infordisc5_3&amp;msg_seq=1331&amp;fileno=1">
                    <img src="/share/images/program/ic_file.gif" alt="첨부파일 다운받기" />
                  </a>
                </li>
              </ul>
            </div>
          </li>
        </ul>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.icouncil.go.kr/main/bbs/bbsMsgFileDown.do"
        "?bcd=infordisc5_3&msg_seq=1331&fileno=1"
    )
    assert refs[0].published_at.isoformat() == "2026-05-11"
    assert refs[0].department_name == "인천시의회 산업경제수석전문위원"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_seongnam_data_view_and_hwpx_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="성남시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.seongnam.go.kr/city/1000199/30218/bbsList.do",
                "fileKinds": ["hwpx"],
                "followDetail": True,
                "pageParam": "currentPage",
            },
        )
    )

    detail_refs = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>2524</td>
            <td><a href="#384094" onclick="dataView('384094');">2026년 4월 도시주택국 업무추진비 집행내역 공표</a></td>
            <td>회계과</td>
            <td>2026-05-15</td>
            <td>35</td>
            <td>첨부파일 있음</td>
          </tr>
        </tbody></table>
        """
    )
    assert len(detail_refs) == 1
    assert detail_refs[0].url == "https://www.seongnam.go.kr/city/1000199/30218/bbsView.do?idx=384094"

    download_refs = crawler._parse_detail_downloads(
        """
        <p class="attachfile">
          업무추진비 정보공표(4월) 도시주택국.hwpx
          <a href="#download"
             onclick="javascript:fileDownload('file-path','saved.hwpx','업무추진비 정보공표(4월) 도시주택국.hwpx'); return false;">내려받기</a>
        </p>
        """,
        detail_refs[0],
    )

    assert len(download_refs) == 1
    parsed_url = urlsplit(download_refs[0].url)
    assert parsed_url.path == "/fileDownload.do"
    assert parse_qs(parsed_url.query) == {
        "filePath": ["file-path"],
        "saveFileNm": ["saved.hwpx"],
        "oFileNm": ["업무추진비 정보공표(4월) 도시주택국.hwpx"],
    }
    assert download_refs[0].file_kind == "hwpx"


def test_attachment_crawler_extracts_jindo_cms_downloads_from_detail_page() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="진도군청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="전라남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.jindo.go.kr/home/board/B0071.cs?m=52",
                "fileKinds": ["pdf"],
                "followDetail": True,
                "pageParam": "pageIndex",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url=(
            "https://www.jindo.go.kr/home/board/B0071.cs?"
            "act=read&articleId=186489&categoryId=0&m=52&pageIndex=1"
        ),
        title="2026년 1분기 안전생활지원과 업무추진비 집행내역",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <ul class="board_file">
          <li class="file_ico file_pdf">
            <a href="/viewer/indexDown.jsp?enc=1&amp;sdoc=encoded&amp;stype=pdf">
              <span class="blind">pdf 파일</span>
              <em>업무추진비집행내역(안전생활지원과).pdf (pdf,81.1KByte)</em>
            </a>
            <a href="/cms/download.cs?atchFile=encoded" class="down">
              <img src="/themes/home/images/content/bv_file_down_btn.gif" alt="다운로드" />
            </a>
          </li>
        </ul>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.jindo.go.kr/cms/download.cs?atchFile=encoded"
    assert refs[0].file_kind == "pdf"
    assert refs[0].department_name == "진도군청 안전생활지원과"


def test_council_attachment_crawler_extracts_pyeongtaek_fnact_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="평택시의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.ptcouncil.go.kr/coun/cost/reportList.do",
                "fileKinds": ["xls"],
                "followDetail": True,
                "pageParam": "pageCurNo",
            },
        )
    )

    detail_refs = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr class="pnc" onclick='fnActDetail("39F4CF15C892FF2ADD9BFBEB399003451B45918FA9FF3F83255F1804AA7DDFD81")'>
            <td>1</td>
            <td class="left">2026년 의장단 업무추진비 사용내역(4월)</td>
            <td>평택시의회</td>
            <td>2026.05.06</td>
            <td>24</td>
          </tr>
        </tbody></table>
        """
    )
    assert len(detail_refs) == 1
    assert detail_refs[0].url == (
        "https://www.ptcouncil.go.kr/coun/cost/reportView.do"
        "?viewNo=39F4CF15C892FF2ADD9BFBEB399003451B45918FA9FF3F83255F1804AA7DDFD81"
    )

    download_refs = crawler._parse_detail_downloads(
        """
        <span onclick=''>
          <a href='javascript:void(0);' onclick='previewAjax("/rept_cost/2026/05/1778044024279.xls")'>바로보기</a>
          <span onclick='fnActDownload("0D4DDA5DCB4C52E14F73E51A8E928B333C19DFA2F2712E10B6777E35E5030714")'>
            2026년 4월 의장단 업무추진비 집행내역.xls
          </span>
        </span>
        """,
        detail_refs[0],
    )

    assert len(download_refs) == 1
    parsed_url = urlsplit(download_refs[0].url)
    assert parsed_url.path == "/cmmn/FileDown.do"
    assert parse_qs(parsed_url.query) == {
        "fileID": ["0D4DDA5DCB4C52E14F73E51A8E928B333C19DFA2F2712E10B6777E35E5030714"]
    }
    assert download_refs[0].file_kind == "xls"


def test_attachment_crawler_extracts_daejeon_file_download_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="대전시청",
            gov_tier=GovTier.REGIONAL,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.METRO_CITY,
            parent_region="대전광역시",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.daejeon.go.kr/drh/open/drhDataOpen/drhDataOpenBoardView.do?boardSeq=747&menuSeq=4804",
                "fileKinds": ["xlsx"],
                "followDetail": True,
                "pageParam": "subPageIndex",
            },
        )
    )

    detail_refs = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>1723</td>
            <td><a href="/drh/open/drhDataOpen/drhDataOpenBoardArticleView.do?menuSeq=4804&amp;boardSeq=747&amp;articleSeq=14142&amp;subPageIndex=1">2026년 5월 업무추진비 집행내역(환경국)</a></td>
            <td>2026-05-31</td>
            <td>환경정책과</td>
            <td>첨부파일</td>
          </tr>
        </tbody></table>
        """
    )
    assert len(detail_refs) == 1
    assert detail_refs[0].url == (
        "https://www.daejeon.go.kr/drh/open/drhDataOpen/drhDataOpenBoardArticleView.do"
        "?menuSeq=4804&boardSeq=747&articleSeq=14142&subPageIndex=1"
    )

    download_refs = crawler._parse_detail_downloads(
        """
        <a href="javascript:fileDownLoad('FileUpload/DRH/202605/20260531110246550.xlsx', '업무추진비 공개(2026.5월)_환경국장.xlsx');">
          업무추진비 공개(2026.5월)_환경국장.xlsx (15.8KB)
        </a>
        """,
        detail_refs[0],
    )

    assert len(download_refs) == 1
    parsed_url = urlsplit(download_refs[0].url)
    assert parsed_url.path == "/cmm/Download.do"
    assert parse_qs(parsed_url.query) == {
        "filePath": ["FileUpload/DRH/202605/20260531110246550.xlsx"],
        "fileName": ["업무추진비 공개(2026.5월)_환경국장.xlsx"],
    }
    assert download_refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_changwon_amode_detail_and_cmsfile_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="창원시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경상남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.changwon.go.kr/cwportal/10312/10620/10629.web?gcode=1036",
                "fileKinds": ["xlsx", "pdf"],
                "followDetail": True,
                "pageParam": "cpage",
            },
        )
    )

    detail_refs = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>878668</td>
            <td><a href="?gcode=1036&amp;idx=878668&amp;amode=view&amp;" class="cv3">
              (자치행정국 자치행정과) 2026년 5월 업무추진비 집행내역
            </a></td>
            <td>자치행정과</td>
            <td>2026-06-01</td>
            <td>첨부</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(detail_refs) == 1
    assert detail_refs[0].url == (
        "https://www.changwon.go.kr/cwportal/10312/10620/10629.web"
        "?gcode=1036&idx=878668&amode=view&"
    )
    assert detail_refs[0].published_at.isoformat() == "2026-06-01"

    download_refs = crawler._parse_detail_downloads(
        """
        <a href="/cwportal/cmsfile/download.do?idx=477022&amp;&amp;fsiz=88770" class="filename">
          업무추진비 집행내역(2026.5.).pdf(86.7 KB)
        </a>
        """,
        detail_refs[0],
    )

    assert len(download_refs) == 1
    assert download_refs[0].url == (
        "https://www.changwon.go.kr/cwportal/cmsfile/download.do?idx=477022&&fsiz=88770"
    )
    assert download_refs[0].file_kind == "pdf"
    assert download_refs[0].department_name == "창원시청 자치행정국 자치행정과"


def test_council_attachment_crawler_removes_decorative_new_badge_from_titles() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="옹진군청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="인천광역시",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.ongjin.go.kr/open_content/main/bbs/bbsMsgList.do?bcd=opendata1",
                "fileKinds": ["xlsx"],
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table>
          <thead><tr><th>번호</th><th>제목</th><th>첨부</th><th>작성자</th><th>작성일</th></tr></thead>
          <tbody><tr>
            <td>2176</td>
            <td><a href="/open_content/main/bbs/bbsMsgDetail.do?msg_seq=2176&amp;bcd=opendata1">
              2026년 5월 업무추진비 집행내역(민원지적과) <span class="new_tag">NEW</span>
            </a></td>
            <td><a href="/open_content/main/bbs/bbsMsgFileDown.do?bcd=opendata1&amp;msg_seq=2176&amp;fileno=1">
              <img alt="2026년_5월_업무추진비_집행내역(민원지적과).xlsx 다운받기" />
            </a></td>
            <td>민원지적과</td>
            <td>2026.06.01</td>
          </tr></tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].title.startswith("2026년 5월 업무추진비 집행내역(민원지적과) - ")
    assert " NEW " not in f" {refs[0].title} "


def test_council_attachment_crawler_detects_vice_chair_before_chair() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="서초구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.sdc.seoul.kr/kr/news/bbsBusiness.do",
            },
        )
    )

    refs = crawler._parse_detail_downloads(
        """
        <ul class="attach">
          <li class="file">
            <a href="/bbsAttachDownload.do?key=file1">
              <span class="name">2026년 4월 부의장 업무추진비.pdf</span>
            </a>
          </li>
        </ul>
        """,
        crawler._parse_detail_links(
            """
            <table><tbody><tr>
              <td>67</td>
              <td><a href="?reform=view&key=post">2026년 4월 의장, 부의장 및 상임위원장 업무추진비 공개</a></td>
              <td>서초구의회</td><td>2026.05.15</td><td>11</td><td></td>
            </tr></tbody></table>
            """
        )[0],
    )

    assert refs[0].department_name == "서초구의회 부의장"


def test_council_attachment_crawler_supports_four_column_cost_tables() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="금천구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://council.geumcheon.go.kr/council/kr/costBBS.do",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>74</td>
            <td><a href="/council/kr/costBBSview.do?uid=post">2026년 4월 의회사무국 업무추진비 사용내역</a></td>
            <td>2026-05-11</td>
            <td>
              <a href="/council/kr/bbs/download.do?bbs_id=cost&amp;uid=file1" title="[붙임1] 4월 업무추진비 사용내역 공개(의회사무국장).pdf">
                <span class="name">[붙임1] 4월 업무추진비 사용내역 공개(의회사무국장).pdf</span>
              </a>
              <a href="/council/kr/bbs/download.do?bbs_id=cost&amp;uid=file2" title="[붙임2] 4월 업무추진비 사용내역 공개(의회사무국).pdf">
                <span class="name">[붙임2] 4월 업무추진비 사용내역 공개(의회사무국).pdf</span>
              </a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 2
    assert (
        refs[0].url
        == "https://council.geumcheon.go.kr/council/kr/bbs/download.do?bbs_id=cost&uid=file1"
    )
    assert refs[0].published_at.isoformat() == "2026-05-11"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_songpa_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="송파구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://council.songpa.go.kr/kr/news/bbsCost.do",
                "followDetail": True,
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>97</td>
            <td class="con">
              <a href="?reform=view&key=abc&pageNum=1&flag=&keyword=">2026. 1월 재정복지위원장 업무추진비 공개</a>
            </td>
            <td class="author">송파구의회</td>
            <td class="date">2026.04.10</td>
            <td>105</td>
            <td class="last-child"><img class="attach" src="/images/board/file.gif" alt="첨부" /></td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert (
        details[0].url
        == "https://council.songpa.go.kr/kr/news/bbsCost.do?reform=view&key=abc&pageNum=1&flag=&keyword="
    )
    assert details[0].published_at.isoformat() == "2026-04-10"

    refs = crawler._parse_detail_downloads(
        """
        <ul class="attach">
          <li class="file">
            <a href="/bbsAttachDownload.do?key=file1" target="_blank">
              <img src="/images/board/ico_pdf.gif" alt="재정복지위원장 업무추진비 사용내역(2026. 1.).pdf" />
              <span class="name">재정복지위원장 업무추진비 사용내역(2026. 1.).pdf</span>
            </a>
          </li>
        </ul>
        """,
        details[0],
    )

    assert len(refs) == 1
    assert refs[0].url == "https://council.songpa.go.kr/bbsAttachDownload.do?key=file1"
    assert refs[0].department_name == "송파구의회 위원장"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_bbs_process_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="양천구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.ycc.go.kr/kr/news/bbs?bbs_id=business",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>21</td>
            <td><a href="?bbs_id=business&amp;reform=view&amp;uid=post">양천구의회 2026년 1분기 업무추진비 공개</a></td>
            <td>양천구의회</td><td>2026-04-16</td><td>46</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <div class="files">
          <a href="/kr/news/bbs_process?reform=download&amp;bbs_id=business&amp;uid=1"
             title="2026년_1분기_의정운영공통경비_집행내역.pdf 파일 내려받기">
             2026년_1분기_의정운영공통경비_집행내역.pdf
          </a>
          <a href="/kr/news/bbs_process?reform=download&amp;bbs_id=business&amp;uid=2"
             title="2026년_1분기_의회사무국_업무추진비_집행내역.pdf 파일 내려받기">
             2026년_1분기_의회사무국_업무추진비_집행내역.pdf
          </a>
        </div>
        """,
        detail,
    )

    assert len(refs) == 1
    assert (
        refs[0].url
        == "https://www.ycc.go.kr/kr/news/bbs_process?reform=download&bbs_id=business&uid=2"
    )
    assert refs[0].department_name == "양천구의회 사무국"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_extensionless_bbs_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="중구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://council.junggu.seoul.kr/kr/bbs?bbs_id=cost",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>40</td>
            <td><a href="/kr/bbs?reform=view&amp;uid=post&amp;bbs_id=cost">2026년 4월 의회운영업무추진비 사용내역</a></td>
            <td>서울중구의회</td><td>2026-05-08</td><td>10</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/kr/bbs/download?bbs_id=cost&amp;uid=file"
           title="2026년_4월_의장단_업무추진비_사용내역.pdf 파일 내려받기">
           2026년_4월_의장단_업무추진비_사용내역.pdf
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://council.junggu.seoul.kr/kr/bbs/download?bbs_id=cost&uid=file"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_business_file_download_proc() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="의정부시의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.ujbcl.go.kr/svc/bbs/BusinessList.do?bbsMnuCd=MNU002300000650400000666",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>26</td>
            <td><a href="/svc/bbs/BusinessView.do?bbsSn=28578&amp;bbsMnuCd=MNU002300000650400000666">2026년 1분기 의정부시의회 업무추진비 집행내역</a></td>
            <td>의정부시의회</td><td>2026-04-10</td><td>27</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/svc/bbs/FileDownLoadProc.do?flSn=123"
           title="2026년 1분기 의정부시의회 업무추진비 집행내역.xlsx">
           다운로드
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.ujbcl.go.kr/svc/bbs/FileDownLoadProc.do?flSn=123"
    assert refs[0].file_kind == "xlsx"


def test_council_attachment_crawler_extracts_board_news_direct_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="연천군의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.yca21.go.kr/board/news/list.do?tbname=cost",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>75</td>
            <td><a href="/board/news/view.do?tbname=cost&amp;idx=75">2026년 5월 의장 업무추진비 사용내역</a></td>
            <td>연천군의회</td>
            <td>2026-05-20</td>
            <td>
              <a href="/board/news/download.do?fileName=news_cost_75_01.xlsx"
                 title="2026년 5월 의장 업무추진비 사용내역.xlsx">첨부</a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.yca21.go.kr/board/news/download.do?fileName=news_cost_75_01.xlsx"
    )
    assert refs[0].file_kind == "xlsx"


def test_council_attachment_crawler_extracts_pg_vv_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="이천시의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://council.icheon.go.kr/content/information/businessOperatingExpense.html",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <div>
          <a href="?fidx=5892&amp;pg=vv&amp;page=1">2026년 5월 의장 업무추진비 사용내역</a>
        </div>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/gtb_download.php?gtid=chujin&amp;fid=5892"
           title="2026년 5월 의장 업무추진비 사용내역.pdf">첨부파일</a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://council.icheon.go.kr/gtb_download.php?gtid=chujin&fid=5892"
    )
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_egov_list_links_and_filedown() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="종로구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://council.jongno.go.kr/council/bbs/BBSMSTR_000000000061/list.do?menuNo=401070",
                "followDetail": True,
            },
        )
    )
    details = crawler._parse_detail_links(
        """
        <div>
          <a href="/council/bbs/BBSMSTR_000000000061/view.do?nttId=35&amp;menuNo=401070">
            의회운영업무추진비 공개
          </a>
        </div>
        """
    )
    refs = crawler._parse_detail_downloads(
        """
        <a href="/portal/cmm/fms/FileDown.do?atchFileId=FILE_1&amp;fileSn=1&amp;bbsId=">
          종로구의회 의회운영업무추진비 사용내역(202604).pdf [89.3K]
        </a>
        """,
        details[0],
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://council.jongno.go.kr/council/bbs/BBSMSTR_000000000061/view.do"
        "?nttId=35&menuNo=401070"
    )
    assert len(refs) == 1
    assert refs[0].url == (
        "https://council.jongno.go.kr/portal/cmm/fms/FileDown.do?atchFileId=FILE_1&fileSn=1&bbsId="
    )
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_bd_select_bbs_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="용인시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6",
                "followDetail": True,
            },
        )
    )
    details = crawler._parse_detail_links(
        """
        <div>
          <a href="/user/bbs/BD_selectBbs.do?q_bbsCode=1001&amp;q_bbscttSn=1234">
            2026년 5월 업무추진비 집행내역(도시정책과)
          </a>
        </div>
        """
    )
    refs = crawler._parse_detail_downloads(
        """
        <a href="/component/file/ND_fileDownload.do?q_fileSn=506307&amp;q_fileId=file">
          2026년 5월 업무추진비 집행내역(도시정책과).xlsx
        </a>
        """,
        details[0],
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1001&q_bbscttSn=1234"
    )
    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.yongin.go.kr/component/file/ND_fileDownload.do?q_fileSn=506307&q_fileId=file"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_uses_title_for_generic_xls_download_label() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="파주시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.paju.go.kr/user/policy_02/board/BD_board.list.do?bbsCd=1018",
                "fileKinds": ["xls", "xlsx"],
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table>
          <thead>
            <tr>
              <th>번호</th>
              <th>제목</th>
              <th>부서명</th>
              <th>등록일</th>
              <th>첨부</th>
              <th>조회수</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>4471</td>
              <td>2026년 1분기 업무추진비 집행내역(문화예술과)</td>
              <td>문화예술과</td>
              <td>2026/05/04</td>
              <td>
                <a href="/component/file/ND_fileDownload.do?id=13fd97d2-c11f-40ba-99b1-6024aca87c5e">
                  xls 첨부파일 다운로드
                </a>
              </td>
              <td>23</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.paju.go.kr/component/file/ND_fileDownload.do"
        "?id=13fd97d2-c11f-40ba-99b1-6024aca87c5e"
    )
    assert refs[0].department_name == "파주시청 문화예술과"
    assert refs[0].file_kind == "xls"


def test_attachment_crawler_extracts_bd_board_js_view_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="수원시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.suwon.go.kr/web/board/BD_board.list.do?bbsCd=1179",
                "followDetail": True,
            },
        )
    )

    refs = crawler._parse_detail_links(
        """
        <table>
          <tbody>
            <tr>
              <td>6804</td>
              <td>
                <a href="#" onclick="jsView('1179', '20260601210528273', 'Y', 'Y'); return false;">
                  2026년 5월 아동돌봄과 업무추진비 집행내역 공개
                </a>
              </td>
              <td>왕혜영</td>
              <td>2026/06/01</td>
              <td>2</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.suwon.go.kr/web/board/BD_board.view.do"
        "?bbsCd=1179&seq=20260601210528273"
    )
    assert refs[0].published_at and refs[0].published_at.isoformat() == "2026-06-01"
    assert refs[0].file_kind == "html"


def test_attachment_crawler_extracts_michuhol_and_yeonsu_download_paths() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="연수구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            parent_region="인천광역시",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yeonsu.go.kr/main/administration/open_info/charge.asp",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.yeonsu.go.kr/main/administration/open_info/charge.asp?page=v&idx=11571",
        title="2026년 5월 업무추진비 집행내역(송도건강생활지원센터)",
        published_at=None,
        department_name="연수구청 송도건강생활지원센터",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/other/file_down.do?sq=1214696&amp;key=22D57C1BD1">
          부서운영업무추진비+집행내역(2026년+5월).xlsx
        </a>
        <a href="/shareEtc/download_utf.asp?filename=2026%EB%85%84_5%EC%9B%94_%EC%97%85%EB%AC%B4%EC%B6%94%EC%A7%84%EB%B9%84.xlsx&amp;filepath=etc_account">
          2026년_5월_업무추진비_집행내역(송도건강생활지원센터).xlsx
        </a>
        """,
        detail,
    )

    assert len(refs) == 2
    assert refs[0].url == "https://www.yeonsu.go.kr/other/file_down.do?sq=1214696&key=22D57C1BD1"
    assert refs[0].file_kind == "xlsx"
    assert refs[1].url.startswith("https://www.yeonsu.go.kr/shareEtc/download_utf.asp?")
    assert refs[1].file_kind == "xlsx"


def test_attachment_crawler_extracts_view_path_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="부천시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://bucheon.go.kr/site/program/board/basicboard/list?boardid=1192347&boardtypeid=26716&menuid=148004005002",
                "followDetail": True,
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <div>
          <a href="./view?menuid=148004005002&amp;boardtypeid=26716&amp;encid=abc">
            2026년 5월 정보통신과 업무추진비 집행내역 공개
          </a>
        </div>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://bucheon.go.kr/site/program/board/basicboard/view"
        "?menuid=148004005002&boardtypeid=26716&encid=abc"
    )


def test_attachment_crawler_ignores_placeholder_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="군포시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gunpo.go.kr/www/selectBbsNttList.do?bbsNo=715&key=4276",
                "followDetail": True,
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>1</td>
            <td><a href="/void(0)">2026년 1분기 업무추진비 집행내역</a></td>
            <td>군포시청</td><td>2026-04-20</td><td>1</td>
          </tr>
        </tbody></table>
        """
    )

    assert details == []


def test_attachment_crawler_handles_empty_download_title_attributes() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="용인시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yongin.go.kr/user/bbs/BD_selectBbsList.do?q_bbsCode=1001&q_clCode=6",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbscttSn=1234",
        title="2026년 5월 업무추진비 집행내역(도시정책과)",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/component/file/ND_fileDownload.do?q_fileSn=506307&amp;q_fileId=file" title="">
          <span>2026년 5월 업무추진비 집행내역(도시정책과).xlsx</span>
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].file_kind == "xlsx"


def test_council_attachment_crawler_extracts_mboard_xls_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="서대문구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.sdmcouncil.go.kr/source/korean/partake/business.html",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>168</td>
            <td><a href="?mode=view&amp;page=1&amp;number=171">2026년 3월 의장단 업무추진비 집행내역</a></td>
            <td>서대문구의회</td><td>2026.04.10.</td><td>57</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/Mboard/download.html?table=council_business&amp;column=userfile&amp;uid=171">
          의장단업무추진비집행내역(202603).xls
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.sdmcouncil.go.kr/Mboard/download.html"
        "?table=council_business&column=userfile&uid=171"
    )
    assert refs[0].file_kind == "xls"


def test_council_attachment_crawler_extracts_seongdong_policy_expense_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="성동구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://sdcouncil.sd.go.kr/kr/data/bbs?bbs_id=expenses",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>90</td>
            <td><a href="?bbs_id=expenses&amp;reform=view&amp;uid=post">의회사무국 시책추진비 집행내역(2026. 1분기)</a></td>
            <td>성동구의회</td><td>2026-04-30</td><td>142</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/kr/data/bbs_process?reform=download&amp;bbs_id=expenses&amp;uid=21901"
           title="업무추진비(2026_1_~3_).pdf 파일 내려받기">
          업무추진비(2026_1_~3_).pdf
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://sdcouncil.sd.go.kr/kr/data/bbs_process?reform=download&bbs_id=expenses&uid=21901"
    )
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_yeongdeungpo_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="영등포구의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://www.ydpc.go.kr/content/news/bbsCost.html",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>106</td>
            <td><a href="?fidx=eeeeeBcagc&amp;pg=vv&amp;sid=1000&amp;page=1">2026년 4월 업무추진비 사용내역 공개</a></td>
            <td>영등포구의회</td><td>2026-05-06</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/gtb_download.php?gtid=work&amp;fid=182739"
           title="Array 첨부파일을 다운받습니다.">
          2026년 4월 업무추진비 사용내역.pdf
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.ydpc.go.kr/gtb_download.php?gtid=work&fid=182739"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_gangdong_office_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="강동구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gangdong.go.kr/web/newportal/bbs/b_054",
                "followDetail": True,
            },
        )
    )
    detail = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>156336</td>
            <td><a href="/web/newportal/bbs/b_054/156336?cp=1">2026년 4월 고덕1동 업무추진비 집행내역 공개</a></td>
            <td>강동구청</td><td>2026-05-24</td><td>19</td>
          </tr>
        </tbody></table>
        """
    )[0]

    refs = crawler._parse_detail_downloads(
        """
        <a href="/web/newportal/file/download/uu/5390aaa366da4ba6b3e53339f927bfdb" title="다운로드" class="dl_file">
          2026.4월+업무추진비(고덕1동).pdf (45.1KB)
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert (
        refs[0].url
        == "https://www.gangdong.go.kr/web/newportal/file/download/uu/5390aaa366da4ba6b3e53339f927bfdb"
    )
    assert refs[0].department_name == "강동구청 고덕1동"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_egov_direct_downloads_from_list() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="구로구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.guro.go.kr/www/selectBbsNttList.do?bbsNo=655&key=1732",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>10628</td>
            <td><a href="./selectBbsNttView.do?bbsNo=655&amp;nttNo=234115&amp;key=1732">2026년 4월 주차관리과 시책추진업무추진비 집행내역 공개</a></td>
            <td>주차기획팀</td>
            <td>2026.05.13</td>
            <td>15</td>
            <td>
              <a title="첨부파일 다운로드 새창" target="_blank"
                 href="downloadBbsFile.do?atchmnflNo=351295&amp;bbsNo=655&amp;nttNo=234115&amp;key=1732">
                <span class="p-icon p-icon__pdf">pdf파일첨부</span>
              </a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.guro.go.kr/www/downloadBbsFile.do"
        "?atchmnflNo=351295&bbsNo=655&nttNo=234115&key=1732"
    )
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_egov_detail_downloads_with_generic_download_label() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="양주시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yangju.go.kr/www/selectBbsNttList.do?bbsNo=30&key=234",
                "fileKinds": ["xlsx"],
                "followDetail": True,
                "pageParam": "pageIndex",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url=(
            "https://www.yangju.go.kr/www/selectBbsNttView.do"
            "?key=234&bbsNo=30&nttNo=204968&pageIndex=1"
        ),
        title="시민안전과 업무추진비 집행내역(2026년 5월)",
        department_name="양주시청 시민안전과",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <li>
          <div class="down_view">
            <span><img src="/common/images/board/file/ico_xlsx.gif" alt="xlsx파일첨부" />
              업무추진비 집행내역(시민안전과)_2026년 5월.xlsx
            </span>
            <a href="/www/downloadBbsFile.do?key=234&amp;bbsNo=30&amp;atchmnflNo=198345"
               title="파일 다운로드" class="file_down">다운로드</a>
            <a href="/www/previewUrl.do?key=234&amp;bbsNo=30&amp;atchmnflNo=198345"
               class="file_view">미리보기</a>
          </div>
        </li>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.yangju.go.kr/www/downloadBbsFile.do?key=234&bbsNo=30&atchmnflNo=198345"
    )
    assert refs[0].file_kind == "xlsx"
    assert refs[0].department_name == "양주시청 시민안전과"


def test_attachment_crawler_extracts_gangbuk_office_direct_download_table() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="강북구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://child.gangbuk.go.kr/portal/intgty/deptJobPrtnCt/list.do?menuNo=200155",
                "pageParam": "pageIndex",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table>
          <thead>
            <tr><th>번호</th><th>년도</th><th>월</th><th>작성부서</th><th>구분</th><th>파일</th><th>작성일</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>100</td><td>2026</td><td>4</td><td>기획예산과</td><td>시책추진</td>
              <td><a href="./fileDownLoad.do?streFileNm=20260522054258444.pdf&amp;menuNo=200155">첨부파일</a></td>
              <td>2026년 05월 22일</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://child.gangbuk.go.kr/portal/intgty/deptJobPrtnCt/fileDownLoad.do"
        "?streFileNm=20260522054258444.pdf&menuNo=200155"
    )
    assert refs[0].department_name == "강북구청 기획예산과"
    assert refs[0].published_at and refs[0].published_at.isoformat() == "2026-05-22"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_yangcheon_javascript_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="양천구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397",
                "followDetail": True,
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>7248</td>
            <td>
              <a href="#view" onclick="doBbsFView('397','310210','16010100','310210');return false;">
                <script>document.write(wdigm_title('2026년 4월 업무추진비 집행내역 공개'));</script>
              </a>
            </td>
            <td>기획예산과</td>
            <td>2026.05.13</td>
            <td></td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert (
        details[0].url
        == "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/View.do?cbIdx=397&bcIdx=310210"
    )
    assert details[0].title == "2026년 4월 업무추진비 집행내역 공개"


def test_attachment_crawler_ignores_yangcheon_download_view_previews() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="양천구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/List.do?cbIdx=397",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.yangcheon.go.kr/site/yangcheon/ex/bbs/View.do?cbIdx=397&bcIdx=310813",
        title="2026년 5월 업무추진비 집행내역 공개",
        published_at=date(2026, 6, 1),
        department_name="양천구청 가족정책과",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/common/board/Download.do?bcIdx=310813&amp;cbIdx=397&amp;streFileNm=aaaa.xlsx">
          2026._5월_업무추진비_사용내역(가족정책과).xlsx
        </a>
        <a href="/common/board/DownloadView.do;jsessionid=abc?bcIdx=310813&amp;cbIdx=397&amp;streFileNm=aaaa.xlsx">
          바로보기
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.yangcheon.go.kr/common/board/Download.do"
        "?bcIdx=310813&cbIdx=397&streFileNm=aaaa.xlsx"
    )


def test_attachment_crawler_ignores_synap_and_convert_previews() -> None:
    assert gncouncil._is_download_href("/www/downloadBbsFile.do?atchmnflNo=1131437")
    assert gncouncil._is_download_href(
        "/cwsboard/board.do?mode=download&bid=179&cid=1451405704&filename=145140.xlsx"
    )
    assert not gncouncil._is_download_href(
        "/common/program/synap.jsp?fileName=%2FDATA%2Fbbs%2F715%2Fpreview.xlsx"
    )
    assert not gncouncil._is_download_href(
        "/convert.jsp?bid=179&cid=1451405704&fileName=145140.xlsx"
    )


def test_attachment_crawler_extracts_nowon_direct_downloads_and_department_cell() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="노원구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.nowon.kr/www/user/bbs/BD_selectBbsList.do?q_bbsCode=1012",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td class="cell-no">9880</td>
            <td class="cell-subject">
              <a href="/component/file/ND_fileDownload.do?q_fileSn=299137&amp;q_fileId=866"
                 title="2026년 4월 시책추진 업무추진비 사용내역(건강증진과).pdf Download">
                2026년 4월 업무추진비 사용내역 공개
              </a>
            </td>
            <td class="cell-part">건강증진과</td>
            <td class="cell-date">2026-05-11</td>
            <td class="cell-hit">5</td>
            <td class="cell-file">
              <a href="/component/file/ND_fileDownload.do?q_fileSn=299137&amp;q_fileId=866"
                 title="2026년 4월 시책추진 업무추진비 사용내역(건강증진과).pdf Download">첨부파일</a>
            </td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert (
        refs[0].url
        == "https://www.nowon.kr/component/file/ND_fileDownload.do?q_fileSn=299137&q_fileId=866"
    )
    assert refs[0].file_kind == "pdf"
    assert refs[0].department_name == "노원구청 건강증진과"


def test_attachment_crawler_extracts_gangseo_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="강서구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gangseo.seoul.kr/gs030325",
                "followDetail": True,
            },
        )
    )
    refs = crawler._parse_detail_downloads(
        """
        <div class="file-element">
          <a href="/comm/getFile?srvcId=BBSTY1&amp;upperNo=abc&amp;fileTy=ATTACH&amp;fileNo=def" class="btn">
            <span class="sr-only">공원녹지과 업무추진비 집행내역(2026년 4월).pdf</span>다운로드
          </a>
        </div>
        """,
        detail=PostRef(
            agency_id=crawler.agency.id,
            url="https://www.gangseo.seoul.kr/gs030325/320760",
            title="2026년 4월 공원녹지과 업무추진비 집행 내역 공개",
            department_name="강서구청 공원녹지과",
            file_kind="html",
        ),
    )

    assert len(refs) == 1
    assert refs[0].url.startswith("https://www.gangseo.seoul.kr/comm/getFile?")
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_yongsan_downloads_outside_last_cell() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="용산구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.yongsan.go.kr/portal/bbs/B0000030/list.do?menuNo=200140",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <td>7421</td>
            <td><a href="/portal/bbs/B0000030/view.do?nttId=746850">2026년 4월 보건위생과 업무추진비 집행내역 공개</a></td>
            <td>보건위생과</td>
            <td>
              <a href="/portal/cmmn/file/fileDown.do?menuNo=200140&amp;atchFileId=abc&amp;fileSn=1"
                 title="업무추진비 집행내역(2026.4월).pdf" class="file-download"></a>
            </td>
            <td>2026-05-22</td>
            <td>13</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url.startswith("https://www.yongsan.go.kr/portal/cmmn/file/fileDown.do?")
    assert refs[0].department_name == "용산구청 보건위생과"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_dongjak_detail_filename_from_parent() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="동작구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.dongjak.go.kr/portal/bbs/B0000591/list.do?menuNo=200209",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.dongjak.go.kr/portal/bbs/B0000591/view.do?nttId=10751788",
        title="2026년 4월 업무추진비 집행내역 공개(복지국장, 복지정책과)",
        department_name="동작구청 복지정책과",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <dd>
          <a href="/portal/singl/convert/convertToHtml.do?atchFileId=abc&amp;fileSn=1" class="file">
            2026년 4월 업무추진비 집행내역 공개(복지정책과).pdf
          </a>
          <a href="/portal/cmmn/file/fileDown.do?atchFileId=abc&amp;fileSn=1" class="btn btn-download">다운로드</a>
        </dd>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_dobong_wdb_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="도봉구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.dobong.go.kr/Contents.asp?code=10008860",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.dobong.go.kr/bbs.asp?bmode=D&pcode=12743392&code=10008860",
        title="2026년 4월 창3동주민센터 업무추진비 집행내역 공개",
        department_name="도봉구청 창3동",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/WDB_common/include/download.asp?fcode=13595472&amp;bcode=387"
           title="(붙임) 업무추진비 집행내역(창3동)(2026.04).xlsx 다운로드">
          (붙임) 업무추진비 집행내역(창3동)(2026.04).xlsx
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert (
        refs[0].url
        == "https://www.dobong.go.kr/WDB_common/include/download.asp?fcode=13595472&bcode=387"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_junggu_cwsboard_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="중구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.junggu.seoul.kr/content.do?cmsid=15383&exclude=Y",
                "followDetail": True,
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.junggu.seoul.kr/content.do?cmsid=15383&exclude=Y&mode=view&cid=144933281",
        title="2026년 4월 업무추진비 집행내역(소공동)",
        department_name="중구청 소공동",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/cwsboard/board.do?mode=download&amp;bid=179&amp;cid=144933281&amp;fileIndex=1&amp;filename=144933.xlsx">
          게시용_업추비_2026. 4월_소공동.xlsx
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.junggu.seoul.kr/cwsboard/board.do"
        "?mode=download&bid=179&cid=144933281&fileIndex=1&filename=144933.xlsx"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_jungnang_rows_with_th_number_cell() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="중랑구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.jungnang.go.kr/portal/bbs/list/B0000143.do?menuNo=200432",
                "pageParam": "pageIndex",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table><tbody>
          <tr>
            <th scope="col">8290</th>
            <td class="tit">
              <a href="/portal/bbs/view/B0000143/166122.do?menuNo=200432&pageIndex=1">
                2026년 4월 업무추진비 집행내역(도시기반조성과)
              </a>
            </td>
            <td>도시기반조성과</td>
            <td class="attach_file">
              <a href="/portal/cmm/fms/FileDown.do?atchFileId=FILE_1&amp;fileSn=1&amp;bbsId="
                 title="2026년 4월 업무추진비 집행내역(도시기반조성과).pdf">
                2026년 4월 업무추진비 집행내역(도시기반조성과).pdf
              </a>
            </td>
            <td>2026-05-22</td>
            <td>8</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(refs) == 1
    assert (
        refs[0].url
        == "https://www.jungnang.go.kr/portal/cmm/fms/FileDown.do?atchFileId=FILE_1&fileSn=1&bbsId="
    )
    assert refs[0].department_name == "중랑구청 도시기반조성과"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_jongno_responsive_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="종로구청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.AUTONOMOUS_GU,
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": (
                    "https://www.jongno.go.kr/portal/bbs/selectBoardList.do"
                    "?bbsId=BBSMSTR_000000001167&menuId=110210&menuNo=110210"
                ),
            },
        )
    )

    refs = crawler._parse_list(
        """
        <ul class="respon-td">
          <li><span>년도</span><em><a href="javascript:viewMove('256840');">2026</a></em></li>
          <li><span>해당 월</span><em><a href="javascript:viewMove('256840');">04</a></em></li>
          <li><span>작성부서</span><em><a href="javascript:viewMove('256840');">보건정책과</a></em></li>
          <li><span>구분</span><em><a href="javascript:viewMove('256840');">시책추진</a></em></li>
          <li><span>파일</span><em><a href="/cmm/fms/FileDown.do?atchFileId=FILE_1&amp;fileSn=1">파일</a></em></li>
          <li><span>작성일</span><em>2026년 05월 15일</em></li>
        </ul>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.jongno.go.kr/cmm/fms/FileDown.do?atchFileId=FILE_1&fileSn=1"
    assert refs[0].department_name == "종로구청 보건정책과"
    assert refs[0].published_at and refs[0].published_at.isoformat() == "2026-05-15"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_header_mapped_download_table() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="고양시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.goyang.go.kr/www/publict/ntt/BD_selectPublictNttList.do",
                "pageParam": "q_currPage",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table class="table table-list">
          <thead>
            <tr>
              <th>제목</th>
              <th>담당부서</th>
              <th>작성일</th>
              <th>파일</th>
              <th>조회수</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <a href="BD_selectPublictNtt.do?publictNttSn=286202">
                  2026년 1분기 기관 및 시책운영업무추진비 사용내역(덕양구보건소 보건행정과)
                </a>
              </td>
              <td>덕양구보건소 &gt; 보건행정과</td>
              <td>2026.05.24</td>
              <td>
                <a href="/component/file/ND_fileDownload.do?q_fileSn=198664&amp;q_fileId=file"
                   title="기관 및 시책추진업무추진비 사용내역(2026년 1분기)(덕양구보건소 보건행정과).xlsx">
                  <span>기관 및 시책추진업무추진비 사용내역(2026년 1분기)(덕양구보건소 보건행정과).xlsx</span>
                </a>
              </td>
              <td>10</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == "https://www.goyang.go.kr/component/file/ND_fileDownload.do?q_fileSn=198664&q_fileId=file"
    assert refs[0].department_name == "고양시청 덕양구보건소 보건행정과"
    assert refs[0].published_at and refs[0].published_at.isoformat() == "2026-05-24"
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_portal_bbs_go_to_view_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="광주시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53",
                "pageParam": "page",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>6698</td>
            <td>
              <a href="#" onclick="goTo.view('list','344861','53','0311000000'); return false;">
                건강증진과 업무추진비 사용내역(2026년 5월)
              </a>
            </td>
            <td><img src="/common/img/board/xls.gif" alt="xls 파일"/></td>
            <td>건강증진과</td>
            <td>2026-05-31</td>
            <td>0</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.gjcity.go.kr/portal/bbs/view.do?bIdx=344861&ptIdx=53&mId=0311000000"
    )
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-05-31"


def test_attachment_crawler_extracts_same_board_numeric_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="의왕시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.uiwang.go.kr/UWKOROPEN0210",
                "followDetail": True,
                "pageParam": "curPage",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>2294</td>
            <td>담당관</td>
            <td>
              <a href="/UWKOROPEN0210/7001175/?curPage=1" class="tit">
                5월 시책추진업무추진비 사용내역(도시주택국, 도시정책과)
                <span class="btn attach" title="첨부파일">첨부파일</span>
              </a>
            </td>
            <td>2026-06-01</td>
            <td>6</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == "https://www.uiwang.go.kr/UWKOROPEN0210/7001175/?curPage=1"
    assert details[0].title == "5월 시책추진업무추진비 사용내역(도시주택국, 도시정책과)"
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-06-01"


def test_attachment_crawler_extracts_yhlib_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="광주시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gjcity.go.kr/portal/bbs/list.do?mId=0311000000&ptIdx=53",
                "pageParam": "page",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.gjcity.go.kr/portal/bbs/view.do?bIdx=344861&ptIdx=53&mId=0311000000",
        title="건강증진과 업무추진비 사용내역(2026년 5월)",
        department_name="광주시청 건강증진과",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a title="첨부파일(업무추진비+공개(건강증진과+5월).xlsx) 파일 다운로드" href="#"
           onclick=" yhLib.file.download('attach-id','file-sn'); return false;" class="download">
          <span>업무추진비+공개(건강증진과+5월).xlsx</span>
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.gjcity.go.kr/common/file/download.do?atchFileId=attach-id&fileSn=file-sn"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_board_view_renewal_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="평택시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/list.do?bcIdx=264&mid=0110000000",
                "followDetail": True,
                "pageParam": "page",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>10714</td>
            <td class="taL col_title">
              <a href="#" title="게시글 상세 열람"
                 onclick="boardViewRenewal('listForm', '김인옥', 'Y', '264', '353878', '0110000000', '1'); return false;">
                2026년 5월 업무추진비 집행내역(반도체AI과)
              </a>
            </td>
            <td class="col_writer">반도체AI과</td>
            <td class="col_date">2026.05.29</td>
            <td class="tbl_hidden col_file"><img src="/legacy/_guide/img/ext/ext_xls.svg" alt=""/></td>
            <td class="tbl_hidden col_hit">6</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.pyeongtaek.go.kr/pyeongtaek/board/post/view.do?mid=0110000000&bcIdx=264&idx=353878"
    )
    assert details[0].department_name == "평택시청 반도체AI과"
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-05-29"


def test_attachment_crawler_extracts_uijeongbu_board_view_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="의정부시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.ui4u.go.kr/portal/bbs/list.do?mId=0114010300&ptIdx=25",
                "fileKinds": ["xlsx", "pdf"],
                "followDetail": True,
                "pageParam": "pageIndex",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>4578</td>
            <td>
              <a href="#" title="2026년 5월 업무추진비 사용내역 공개(도시재생과)"
                 onclick="boardView('portal', 'listForm', 'EUNA7', 'Y', '363518', '25', '0114010300', '1'); return false;">
                2026년 5월 업무추진비 사용내역 공개(도시재생과)
              </a>
            </td>
            <td>첨부</td>
            <td>2026.06.01</td>
            <td>2</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.ui4u.go.kr/portal/bbs/view.do?mId=0114010300&bIdx=363518&ptIdx=25"
    )
    assert details[0].department_name == "의정부시청 도시재생과"
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-06-01"


def test_attachment_crawler_extracts_inline_post_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="이천시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.icheon.go.kr/portal/onnara/bpc/list.do?mid=0304080000",
                "followDetail": True,
                "pageParam": "currentPageNo",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>179</td>
            <td>부서</td>
            <td class="taL">
              <a href="javascript:void(0);" onclick="yhLib.inline.post(this)"
                 data-req-action="/portal/onnara/bpc/view.do?mid=0304080000"
                 data-req-form-id="view"
                 data-req-merge-form-id="list"
                 data-req-p-bid="16868">2026년 4월 업무추진비 집행내역(체육진흥과)</a>
            </td>
            <td>자치행정국 체육진흥과</td>
            <td>1</td>
            <td>2026.05.29</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.icheon.go.kr/portal/onnara/bpc/view.do?mid=0304080000&bid=16868"
    )
    assert details[0].department_name == "이천시청 체육진흥과"
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-05-29"

    refs = crawler._parse_detail_downloads(
        """
        <a href="javascript:void(0)"
           onclick="yhLib.file.download('955825F0DF697C801BA5C410499533351C5637586E1A0AD90A6243DB5CFA4C53', '125EB0AE64ED2AE7001CFD6CFA9E31E8'); return false;">
          2026년 4월 업무추진비 집행내역_체육진흥과.xlsx
        </a>
        """,
        details[0],
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.icheon.go.kr/common/file/download.do"
        "?atchFileId=955825F0DF697C801BA5C410499533351C5637586E1A0AD90A6243DB5CFA4C53"
        "&fileSn=125EB0AE64ED2AE7001CFD6CFA9E31E8"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_inline_post_idx_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="구미시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경상북도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gumi.go.kr/portal/board/post/list.do?bcIdx=164&mid=0303100000",
                "followDetail": True,
                "pageParam": "page",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>8843</td>
            <td class="list_tit">
              <a href="#" title="게시글 상세 열람"
                 onclick="yhLib.inline.post(this); return false;"
                 data-req-form-id="viewForm"
                 data-req-merge-form-id="listForm"
                 data-req-get-p-idx="836663">
                2026년 5월 업무추진비 집행내역(신산업정책과)
              </a>
            </td>
            <td class="list_file"><img src="/common/img/board/xls.gif" alt="엑셀 파일"/></td>
            <td class="list_write">신산업정책과</td>
            <td class="list_date">2026-06-01(Mon)</td>
            <td class="list_hit">1</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.gumi.go.kr/portal/board/post/view.do?bcIdx=164&mid=0303100000&idx=836663"
    )
    assert details[0].department_name == "구미시청 신산업정책과"
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-06-01"


def test_attachment_crawler_extracts_page_list_bbs_fn_go_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="안산시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471",
                "pageParam": "currentPage",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>1673286</td>
            <td>
              <a href="#" onclick="fnGoDetail( 1673286 ); return false;">
                의정법무과 업무추진비 집행내역(2026년 5월)
              </a>
            </td>
            <td>의정법무과</td>
            <td>2026.05.31</td>
            <td>1</td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.ansan.go.kr/www/common/bbs/selectBbsDetail.do?bbs_seq=1673286&bbs_code=B0471"
    )
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-05-31"


def test_attachment_crawler_extracts_fn_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="안산시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.ansan.go.kr/www/common/bbs/selectPageListBbs.do?bbs_code=B0471",
                "pageParam": "currentPage",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.ansan.go.kr/www/common/bbs/selectBbsDetail.do?bbs_seq=1673286&bbs_code=B0471",
        title="의정법무과 업무추진비 집행내역(2026년 5월)",
        department_name="안산시청 의정법무과",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="#" onclick="fnFileDownLoad('178022271498381VO1PO0KT25VLAWL0H1A0ZF9'); return false;">
          <span class="p-icon p-icon__xls">xls 문서</span>
          <span>업무추진비 집행내역(2026. 5월)-의정법무과.xls</span>
          <i>파일 다운로드 버튼</i>
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.ansan.go.kr/common/file/FileDown.do?file_id=178022271498381VO1PO0KT25VLAWL0H1A0ZF9"
    )
    assert refs[0].file_kind == "xls"


def test_attachment_crawler_extracts_egov_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="과천시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.gccity.go.kr/portal/bbs/list.do?ptIdx=225&mId=0203080000",
                "pageParam": "page",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://www.gccity.go.kr/portal/bbs/view.do?bIdx=192261&ptIdx=225&mId=0203080000",
        title="2026년 4월 별양동 업무추진비 사용내역 공개",
        department_name="과천시청 별양동",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="#"
           onclick="fn_egov_downFile('148c15d19a358e7fd81799db36f4771c6893f071240e83f00b0a5032296b537b','f9a1967c526603d17ab488b9d2747cda'); return false;">
          <span>2026년 4월 별양동 업무추진비 집행내역.xlsx</span>
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.gccity.go.kr/cmm/fms/FileDown.do?atchFileId=148c15d19a358e7fd81799db36f4771c6893f071240e83f00b0a5032296b537b&fileSn=f9a1967c526603d17ab488b9d2747cda"
    )
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_configured_egov_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="곡성군청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="전라남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": (
                    "https://www.gokseong.go.kr/kr/board/list.do?"
                    "bbsId=BBS_000000000000540&menuNo=102006001000"
                ),
                "fileKinds": ["pdf"],
                "followDetail": True,
                "pageParam": "pageIndex",
                "jsDownloadPath": "/board/FileDown.do",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url=(
            "https://www.gokseong.go.kr/kr/board/view.do?"
            "bbsId=BBS_000000000000540&nttId=139858"
        ),
        title="26년 1분기 시책추진업무추진비 집행내역",
        department_name="곡성군청 군수",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="javascript:fn_egov_downFile('FILE_000000014480507','0')"
           title="26년 1분기 시책추진업무추진비 집행내역(군수).pdf">
          26년 1분기 시책추진업무추진비 집행내역(군수).pdf
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.gokseong.go.kr/board/FileDown.do"
        "?atchFileId=FILE_000000014480507&fileSn=0"
    )
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_egov_download_path_from_detail_script() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="곡성군청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.GUN,
            parent_region="전라남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": (
                    "https://www.gokseong.go.kr/kr/board/list.do?"
                    "bbsId=BBS_000000000000540&menuNo=102006001000"
                ),
                "fileKinds": ["pdf"],
                "followDetail": True,
                "pageParam": "pageIndex",
                "jsDownloadPath": "/board/FileDown.do",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url=(
            "https://www.gokseong.go.kr/kr/board/view.do;jsessionid=ABC?"
            "bbsId=BBS_000000000000540&nttId=109056"
        ),
        title="2026년 시책업무추진비 집행현황(1분기)",
        department_name="곡성군청 군수",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <script>
          function fn_egov_downFile(atchFileId, fileSn){
            window.open("/board/FileDown.do;jsessionid=ABC?atchFileId="+atchFileId+"&fileSn="+fileSn+"");
          }
        </script>
        <a href="javascript:fn_egov_downFile('FILE_000000014480507','0')">
          26년 1분기 시책추진업무추진비 집행내역(군수).pdf
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.gokseong.go.kr/board/FileDown.do;jsessionid=ABC"
        "?atchFileId=FILE_000000014480507&fileSn=0"
    )
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_data_column_egov_download_tables() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="안성시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://www.anseong.go.kr/portal/businessExpense/list.do?mId=0402050000",
                "pageParam": "page",
            },
        )
    )

    refs = crawler._parse_list(
        """
        <table class="minwonDownList">
          <thead>
            <tr>
              <th data-column="연도">연</th>
              <th data-column="연도">월</th>
              <th data-column="제목">구분</th>
              <th data-column="첨부파일">사용내역</th>
              <th data-column="작성일">작성일</th>
              <th data-column="조회수">조회수</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td data-column="연도">2026</td>
              <td data-column="연도">5</td>
              <td data-column="제목">문화관광과</td>
              <td data-column="첨부파일">
                <a href="#"
                   onclick="fn_egov_downFile('66b36f0301985151457a8e447a81c142d7fa74aa843983a1132a890f9a3a0430', 'f9a1967c526603d17ab488b9d2747cda'); return false;"
                   title="XLSX 파일 다운로드">
                  <img src="/common/img/board/xls.gif" alt="XLSX 파일"/>
                </a>
              </td>
              <td data-column="작성일">2026-05-31</td>
              <td data-column="조회수">1</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.anseong.go.kr/cmm/fms/FileDown.do"
        "?atchFileId=66b36f0301985151457a8e447a81c142d7fa74aa843983a1132a890f9a3a0430"
        "&fileSn=f9a1967c526603d17ab488b9d2747cda"
    )
    assert refs[0].title == "2026년 05월 문화관광과 업무추진비 공개내역 - 문화관광과 업무추진비.xlsx"
    assert refs[0].department_name == "안성시청 문화관광과"
    assert refs[0].published_at and refs[0].published_at.isoformat() == "2026-05-31"
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_treats_file_download_labels_as_generic() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="동두천시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": "https://ddc.go.kr/ddc/selectBbsNttList.do?bbsNo=38&key=122",
                "pageParam": "pageIndex",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://ddc.go.kr/ddc/selectBbsNttView.do?key=122&bbsNo=38&nttNo=157009",
        title="2026년 5월 시설사업소 업무추진비 집행내역",
        department_name="동두천시청 시설사업소",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <span><img src="/common/images/board/file/ico_xlsx.gif" alt=""/>2026년 5월 업무추진비 집행내역(시설사업소).xlsx</span>
        <a href="/ddc/downloadBbsFile.do?atchmnflNo=215537" class="file_down">xlsx 파일 다운로드<i></i></a>
        <a href="/common/program/synep.jsp?fn=/DATA/bbs/38/preview.xlsx">xlsx 파일 미리보기</a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://ddc.go.kr/ddc/downloadBbsFile.do?atchmnflNo=215537"
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_php_go_view_page_detail_links() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="김포시의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702",
                "pageParam": "pageNo",
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table><tbody>
          <tr>
            <td>24</td>
            <td><a href="javascript:goViewPage('748294');" onclick="goViewPage('748294');">
              2026년 1/4분기 김포시의회 의장단 업무추진비 공개
            </a></td>
            <td>김포시의회</td>
            <td>2026.04.29.</td>
            <td><img src="/images/ext/xlsx.gif" alt="첨부파일" /></td>
          </tr>
        </tbody></table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://gimpocouncil.go.kr/cnts/bbs/infoView.php?bbsCd=act&bbsSubCd=act0702&bbsSn=748294"
    )
    assert details[0].published_at and details[0].published_at.isoformat() == "2026-04-29"


def test_attachment_crawler_extracts_configured_php_file_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="김포시의회",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.COUNCIL,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경기도",
            source_pattern={
                "adapter": "council_attachment_board",
                "listUrl": "https://gimpocouncil.go.kr/cnts/bbs/infoList.php?bbsCd=act&bbsSubCd=act0702",
                "pageParam": "pageNo",
                "jsDownloadPath": "/sma/utl/FileDownLoad.php",
            },
        )
    )
    detail = PostRef(
        agency_id=crawler.agency.id,
        url="https://gimpocouncil.go.kr/cnts/bbs/infoView.php?bbsCd=act&bbsSubCd=act0702&bbsSn=748294",
        title="2026년 1/4분기 김포시의회 의장단 업무추진비 공개",
        department_name="김포시의회 의장단",
        file_kind="html",
    )

    refs = crawler._parse_detail_downloads(
        """
        <a class="tit" href="javascript:fileDownLoad('18771','act0702');"
           onclick="fileDownLoad('18771','act0702'); return false;">
          (공개)의장단업무추진비_2026년1분기.xlsx
        </a>
        """,
        detail,
    )

    assert len(refs) == 1
    assert refs[0].url == "https://gimpocouncil.go.kr/sma/utl/FileDownLoad.php?flSn=18771&flCd=act0702"
    assert refs[0].file_kind == "xlsx"


def test_attachment_crawler_extracts_miryang_board_detail_and_file_web_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="밀양시청",
            gov_tier=GovTier.BASIC,
            branch=GovBranch.ADMIN,
            jurisdiction_type=JurisdictionType.SI,
            parent_region="경상남도",
            source_pattern={
                "adapter": "attachment_board",
                "listUrl": (
                    "https://www.miryang.go.kr/twn/bbs/selectBoardList.do?"
                    "bbsId=BBSMSTR_000000085910&mnNo=3040000&owd=sammun"
                ),
                "fileKinds": ["xlsx"],
                "pageParam": "pageIndex",
                "followDetail": True,
            },
        )
    )

    details = crawler._parse_detail_links(
        """
        <table>
          <tbody>
            <tr>
              <td>42</td>
              <td>
                <a href="/twn/bbs/selectBoardDetail.do;jsessionid=ABC.was1?mnNo=3040000&amp;owd=sammun&amp;bbsId=BBSMSTR_000000085910&amp;nttId=191938&amp;pageIndex=1">
                  <span class="txt">2026년 업무추진비 집행내역(5월)</span>
                </a>
              </td>
              <td>삼문동</td>
              <td>2026-05-29</td>
              <td>12</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(details) == 1
    assert details[0].url == (
        "https://www.miryang.go.kr/twn/bbs/selectBoardDetail.do;jsessionid=ABC.was1"
        "?mnNo=3040000&owd=sammun&bbsId=BBSMSTR_000000085910&nttId=191938&pageIndex=1"
    )

    refs = crawler._parse_detail_downloads(
        """
        <a href="/cmm/fms/FileWebDown.do?atchFileId=FILE_000000000082328&amp;fileSn=0"
           title="2026년 업무추진비 집행내역(5월).xlsx">
          <span class="F-nme">2026년 업무추진비 집행내역(5월).xlsx</span>
        </a>
        """,
        details[0],
    )

    assert len(refs) == 1
    assert refs[0].url == (
        "https://www.miryang.go.kr/cmm/fms/FileWebDown.do?"
        "atchFileId=FILE_000000000082328&fileSn=0"
    )
    assert refs[0].file_kind == "xlsx"
