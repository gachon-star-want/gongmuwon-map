from pathlib import Path

from public_officer_pipeline.agencies import SEOUL_AGENCIES
from public_officer_pipeline.crawler.seoul_opengov import SeoulOpenGovCrawler
from public_officer_pipeline.extractor import extract_expense_rows


def test_extracts_opengov_expense_table() -> None:
    html = (Path(__file__).parent / "fixtures" / "opengov_expense_sample.html").read_text()

    rows = extract_expense_rows(html)

    assert len(rows) == 2
    assert rows[0].department_name == "기획조정실 정책기획관"
    assert rows[0].amount == 87000
    assert rows[0].place_text.startswith("창고43")


def test_extracts_key_value_expense_tables() -> None:
    rows = extract_expense_rows(
        """
        <table class="view">
          <caption>업무추진비 상세정보 보기</caption>
          <tbody>
            <tr>
              <th scope="row">비목</th><td>부서운영</td>
              <th scope="row">집행부서</th><td>교통행정과</td>
              <th scope="row">집행일시</th><td colspan="5">2026-05-22&nbsp;&nbsp;&nbsp;&nbsp;11:53</td>
            </tr>
            <tr>
              <th scope="row">집행내역</th><td colspan="4">차량관리팀 업무간담회</td>
              <th scope="row">결제방법</th><td colspan="4">신용카드</td>
            </tr>
            <tr>
              <th scope="row">사용자</th><td>교통행정과장</td>
              <th scope="row">대상인원수(명)</th><td>6</td>
              <th scope="row">집행장소</th><td colspan="3">상무초밥(관악구 관악로168, 1층)</td>
              <th scope="row">집행금액(원)</th><td>77,400</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(rows) == 1
    assert rows[0].department_name == "교통행정과"
    assert rows[0].used_at.isoformat() == "2026-05-22T11:53:00"
    assert rows[0].place_text == "상무초밥(관악구 관악로168, 1층)"
    assert rows[0].purpose == "차량관리팀 업무간담회"
    assert rows[0].amount == 77400
    assert rows[0].user_text == "교통행정과장 6명"


def test_opengov_crawler_uses_agency_title_filter() -> None:
    agency = next(item for item in SEOUL_AGENCIES if item.short_name == "서울시의회")
    crawler = SeoulOpenGovCrawler(agency=agency)

    refs = crawler._parse_list(
        """
        <a href="/expense/1">2026년 4월 의회사무처 의정국 운영지원과 업무추진비 - 부서운영</a>
        <a href="/expense/2">2026년 4월 서울시본청 기획조정실 업무추진비 - 부서운영</a>
        """
    )

    assert len(refs) == 1
    assert refs[0].agency_id == agency.id
    assert refs[0].title.startswith("2026년 4월 의회사무처")
