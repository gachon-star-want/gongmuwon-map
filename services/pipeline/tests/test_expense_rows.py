from datetime import datetime

from public_officer_pipeline.extractor.rows import (
    RawExpenseFields,
    build_expense_row,
    format_place_text,
    parse_amount,
    parse_party_size,
    parse_used_at,
)


def test_parse_amount_strips_thousands_and_currency_text() -> None:
    assert parse_amount("1,234,567") == 1234567
    assert parse_amount("1 234") == 1234
    assert parse_amount("₩55,000") == 55000


def test_parse_amount_invalid_inputs_return_none() -> None:
    assert parse_amount(None) is None
    assert parse_amount("") is None
    assert parse_amount("N/A") is None


def test_parse_party_size_parses_digit_text() -> None:
    assert parse_party_size("12") == 12
    assert parse_party_size("12명") == 12
    assert parse_party_size(0) is None


def test_parse_used_at_merges_date_and_time() -> None:
    assert parse_used_at("2026-04-05", "13:45:30") == datetime(2026, 4, 5, 13, 45, 30)


def test_parse_used_at_prefers_explicit_short_year_rule() -> None:
    assert parse_used_at("26.04.30", None) == datetime(2026, 4, 30)
    assert parse_used_at("70.01.01", None) == datetime(1970, 1, 1)


def test_format_place_text_prefers_explicit_when_already_formatted() -> None:
    assert (
        format_place_text(
            name="카페",
            address="서울 강남구",
            place_text="오션뷰(서울 강남구)",
        )
        == "오션뷰(서울 강남구)"
    )


def test_build_expense_row_uses_fallback_department_and_sanitizes_raw_excerpt() -> None:
    row = build_expense_row(
        RawExpenseFields(
            date_text="2026-04-30",
            time_text="11:11:11",
            place_name="카페",
            address="서울 강남구",
            purpose="회의",
            amount="12,000",
            party_size="4",
            user_text="이충현 과장",
            payment_method="카드",
            raw_values=["이충현 과장", "2026-04-30", "카페", "12,000", "회의"],
        ),
        fallback_department="강남구청",
    )

    assert row is not None
    assert row.department_name == "강남구청"
    assert row.place_text == "카페(서울 강남구)"
    assert row.amount == 12000
    assert row.user_text == "이충현 과장 4명"
    assert "이충현" not in row.raw_excerpt


def test_build_expense_row_rejects_invalid_rows() -> None:
    assert (
        build_expense_row(
            RawExpenseFields(
                date_text=None,
                place_name="카페",
                amount="12000",
            ),
            fallback_department="강남구청",
        )
        is None
    )
    assert (
        build_expense_row(
            RawExpenseFields(
                date_text="2026-04-30",
                place_name="",
                amount="12000",
            ),
            fallback_department="강남구청",
        )
        is None
    )
