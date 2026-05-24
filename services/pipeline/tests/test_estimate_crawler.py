from datetime import date

from public_officer_pipeline.crawler.estimate import EstimateListCrawler, _page_count
from public_officer_pipeline.models import Agency, AgencyKind


def test_estimate_crawler_counts_pages() -> None:
    assert _page_count('<div class="count">건수 : <em>6,145</em>건수</div>', 10) == 615


def test_estimate_crawler_builds_filtered_page_refs() -> None:
    crawler = EstimateListCrawler(
        Agency(
            short_name="관악구청",
            kind=AgencyKind.GU_OFFICE,
            source_pattern={
                "adapter": "estimate_list_html",
                "listUrl": "https://www.gwanak.go.kr/site/gwanak/estimate/estimateList.do",
                "rowsPerPage": 10,
            },
        )
    )
    ref = crawler._ref_for_page(
        3,
        crawler._url_for_page(3, since=date(2026, 1, 1)),
        date(2026, 1, 1),
    )

    assert ref.file_kind == "html"
    assert "pageIndex=3" in ref.url
    assert "searchCondition3=2026-01-01" in ref.url
    assert ref.title.startswith("관악구청 업무추진비 공개")
