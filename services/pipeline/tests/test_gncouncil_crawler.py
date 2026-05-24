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
