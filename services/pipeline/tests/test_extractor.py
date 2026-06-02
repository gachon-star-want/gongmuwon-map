from datetime import date
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


def test_extracts_inline_district_expense_table_aliases() -> None:
    rows = extract_expense_rows(
        """
        <table>
          <thead>
            <tr>
              <th>연번</th><th>부서명</th><th>사용자</th><th>대상인원</th>
              <th>사용일자(일시)</th><th>사용장소(가맹점명)</th><th>사용목적(내역)</th>
              <th>사용금액(원)</th><th>사용방법</th><th>비목</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>172452</td><td>생활복지과</td><td>주무관</td><td>5</td>
              <td>2026-05-22 12:00</td><td>울릉도</td><td>간담회</td>
              <td>75,000</td><td>카드</td><td>시책</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(rows) == 1
    assert rows[0].department_name == "생활복지과"
    assert rows[0].place_text == "울릉도"
    assert rows[0].amount == 75000
    assert rows[0].user_text == "주무관 5명"
    assert rows[0].payment_method == "카드"


def test_extracts_seodaemun_key_value_table_with_thousand_amounts() -> None:
    rows = extract_expense_rows(
        """
        <table>
          <tbody>
            <tr>
              <th scope="row">구분</th><td>시책</td>
              <th scope="row">집행부서</th><td>행정지원과</td>
              <th scope="row">집행일</th><td>2026-05-18</td>
            </tr>
            <tr>
              <th scope="row">집행유형</th><td colspan="3">업무추진을 위한 회의</td>
              <th scope="row">집행구분</th><td>식사</td>
            </tr>
            <tr>
              <th scope="row">집행대상</th><td colspan="3">행정자치국 직원</td>
              <th scope="row">집행액(천원)</th><td>84</td>
            </tr>
            <tr>
              <th scope="row">집행인원</th><td>4</td>
              <th scope="row">결제방법</th><td>카드</td>
              <th scope="row">장소</th><td>연희녹두삼계탕</td>
            </tr>
          </tbody>
        </table>
        """
    )

    assert len(rows) == 1
    assert rows[0].department_name == "행정지원과"
    assert rows[0].place_text == "연희녹두삼계탕"
    assert rows[0].amount == 84000
    assert rows[0].user_text == "행정자치국 직원 4명"
    assert rows[0].expense_category == "식사"


def test_extracts_ulsan_daily_detail_table_with_fallback_date() -> None:
    rows = extract_expense_rows(
        """
        <table class="tbl_bd_list txt_c valg_m">
          <thead>
            <tr>
              <th>번호</th><th>결제내용</th><th>결제방법</th><th>인원(수량)</th>
              <th>금액(천원)</th><th>참석대상</th><th>장소</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>1</td><td>재난대응과 부서운영업무추진비 집행(서울주소방서)</td>
              <td>카드</td><td>12</td><td>316</td><td>재난대응과 직원 12</td><td>농도</td>
            </tr>
          </tbody>
        </table>
        """,
        fallback_date=date(2026, 6, 1),
    )

    assert len(rows) == 1
    assert rows[0].used_at.isoformat() == "2026-06-01T00:00:00"
    assert rows[0].place_text == "농도"
    assert rows[0].purpose == "재난대응과 부서운영업무추진비 집행(서울주소방서)"
    assert rows[0].amount == 316000
    assert rows[0].user_text == "재난대응과 직원 12 12명"
    assert rows[0].payment_method == "카드"


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
