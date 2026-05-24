from pathlib import Path

from public_officer_pipeline.extractor import extract_expense_rows


def test_extracts_opengov_expense_table() -> None:
    html = (Path(__file__).parent / "fixtures" / "opengov_expense_sample.html").read_text()

    rows = extract_expense_rows(html)

    assert len(rows) == 2
    assert rows[0].department_name == "기획조정실 정책기획관"
    assert rows[0].amount == 87000
    assert rows[0].place_text.startswith("창고43")
