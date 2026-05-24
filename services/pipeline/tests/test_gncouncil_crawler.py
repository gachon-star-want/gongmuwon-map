from public_officer_pipeline.crawler.gncouncil import CouncilAttachmentCrawler, GangnamCouncilCrawler
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
