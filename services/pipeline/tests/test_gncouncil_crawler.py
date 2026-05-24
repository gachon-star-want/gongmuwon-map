from public_officer_pipeline.crawler.gncouncil import CouncilAttachmentCrawler, GangnamCouncilCrawler, _url_with_page
from public_officer_pipeline.models import Agency, AgencyKind


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


def test_council_attachment_crawler_extracts_cost_xlsx_refs_from_title_attribute() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="강서구의회",
            kind=AgencyKind.GU_COUNCIL,
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


def test_council_attachment_crawler_detects_vice_chair_before_chair() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="서초구의회",
            kind=AgencyKind.GU_COUNCIL,
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
            kind=AgencyKind.GU_COUNCIL,
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
    assert refs[0].url == "https://council.geumcheon.go.kr/council/kr/bbs/download.do?bbs_id=cost&uid=file1"
    assert refs[0].published_at.isoformat() == "2026-05-11"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_songpa_detail_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="송파구의회",
            kind=AgencyKind.GU_COUNCIL,
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
    assert details[0].url == "https://council.songpa.go.kr/kr/news/bbsCost.do?reform=view&key=abc&pageNum=1&flag=&keyword="
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
            kind=AgencyKind.GU_COUNCIL,
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
    assert refs[0].url == "https://www.ycc.go.kr/kr/news/bbs_process?reform=download&bbs_id=business&uid=2"
    assert refs[0].department_name == "양천구의회 사무국"
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_extensionless_bbs_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="중구의회",
            kind=AgencyKind.GU_COUNCIL,
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


def test_council_attachment_crawler_extracts_egov_list_links_and_filedown() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="종로구의회",
            kind=AgencyKind.GU_COUNCIL,
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
        "https://council.jongno.go.kr/portal/cmm/fms/FileDown.do"
        "?atchFileId=FILE_1&fileSn=1&bbsId="
    )
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_mboard_xls_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="서대문구의회",
            kind=AgencyKind.GU_COUNCIL,
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
            kind=AgencyKind.GU_COUNCIL,
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
        "https://sdcouncil.sd.go.kr/kr/data/bbs_process"
        "?reform=download&bbs_id=expenses&uid=21901"
    )
    assert refs[0].file_kind == "pdf"


def test_council_attachment_crawler_extracts_yeongdeungpo_downloads() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="영등포구의회",
            kind=AgencyKind.GU_COUNCIL,
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
            kind=AgencyKind.GU_OFFICE,
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
    assert refs[0].url == "https://www.gangdong.go.kr/web/newportal/file/download/uu/5390aaa366da4ba6b3e53339f927bfdb"
    assert refs[0].department_name == "강동구청 고덕1동"
    assert refs[0].file_kind == "pdf"


def test_attachment_crawler_extracts_egov_direct_downloads_from_list() -> None:
    crawler = CouncilAttachmentCrawler(
        Agency(
            short_name="구로구청",
            kind=AgencyKind.GU_OFFICE,
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
