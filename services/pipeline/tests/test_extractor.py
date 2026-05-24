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
