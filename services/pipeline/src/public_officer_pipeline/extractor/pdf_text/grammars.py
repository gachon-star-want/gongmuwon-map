from __future__ import annotations

from collections.abc import Callable
from typing import Any

from public_officer_pipeline.models import ParsedExpenseRow
from public_officer_pipeline.extractor.pdf_text.parser import (
    LINE_GRAMMAR_ORDER,
    WHOLE_TEXT_FALLBACK_ORDER,
    PdfTextGrammar,
)
from public_officer_pipeline.extractor.pdf_text import text_parser


class LineGrammar(PdfTextGrammar):
    def __init__(self, name: str, parse_fn: Callable[[str, str], ParsedExpenseRow | None]) -> None:
        self.name = name
        self._parse_fn = parse_fn

    def parse(self, text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
        parsed = self._parse_fn(text, fallback_department)
        if parsed is None:
            return []
        return [parsed]


class WholeTextGrammar(PdfTextGrammar):
    def __init__(self, name: str, parse_fn: Callable[[str, str], list[ParsedExpenseRow]]) -> None:
        self.name = name
        self._parse_fn = parse_fn

    def parse(self, text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
        return self._parse_fn(text, fallback_department=fallback_department)


def _build_default_line_grammars() -> list[PdfTextGrammar]:
    def _to_parse_fn(fn: Any) -> Callable[[str, str], ParsedExpenseRow | None]:
        return lambda text, fallback_department: fn(text, fallback_department=fallback_department)

    return [
        LineGrammar("user_address", _to_parse_fn(text_parser._parse_pdf_text_user_address_line)),
        LineGrammar("date_user_amount_place", _to_parse_fn(text_parser._parse_pdf_text_date_user_amount_place_line)),
        LineGrammar("purpose_place_amount", _to_parse_fn(text_parser._parse_pdf_text_purpose_place_amount_line)),
        LineGrammar(
            "date_purpose_party_amount_place",
            _to_parse_fn(text_parser._parse_pdf_text_date_purpose_party_amount_place_line),
        ),
        LineGrammar(
            "region_amount_place_purpose",
            _to_parse_fn(text_parser._parse_pdf_text_region_amount_place_purpose_line),
        ),
        LineGrammar(
            "optional_user_place_purpose_amount",
            _to_parse_fn(text_parser._parse_pdf_text_optional_user_place_purpose_amount_line),
        ),
        LineGrammar(
            "user_amount_place_address_purpose",
            _to_parse_fn(text_parser._parse_pdf_text_user_amount_place_address_purpose_line),
        ),
        LineGrammar("council_user_place", _to_parse_fn(text_parser._parse_pdf_text_council_user_place_line)),
        LineGrammar("user_place_purpose_amount", _to_parse_fn(text_parser._parse_pdf_text_user_place_purpose_amount_line)),
        LineGrammar(
            "user_place_purpose_category",
            _to_parse_fn(text_parser._parse_pdf_text_user_place_purpose_category_line),
        ),
        LineGrammar(
            "compact_date_purpose_place",
            _to_parse_fn(text_parser._parse_pdf_text_compact_date_purpose_place_line),
        ),
        LineGrammar("user_amount_purpose", _to_parse_fn(text_parser._parse_pdf_text_user_amount_purpose_line)),
        LineGrammar("user_no_address", _to_parse_fn(text_parser._parse_pdf_text_user_no_address_line)),
        LineGrammar("purpose_first", _to_parse_fn(text_parser._parse_pdf_text_purpose_first_line)),
        LineGrammar(
            "date_time_place_purpose_party_amount",
            _to_parse_fn(text_parser._parse_pdf_text_date_time_place_purpose_party_amount_line),
        ),
        LineGrammar(
            "user_date_place_purpose_amount_party",
            _to_parse_fn(text_parser._parse_pdf_text_user_date_place_purpose_amount_party_line),
        ),
        LineGrammar(
            "purpose_amount_party_place_date_user",
            _to_parse_fn(text_parser._parse_pdf_text_purpose_amount_party_place_date_user_line),
        ),
        LineGrammar(
            "datetime_purpose_amount_method_place",
            _to_parse_fn(text_parser._parse_pdf_text_datetime_purpose_amount_method_place_line),
        ),
        LineGrammar(
            "generic_text_row",
            _to_parse_fn(text_parser._parse_pdf_text_generic_row),
        ),
    ]


def _build_default_whole_text_grammars() -> list[PdfTextGrammar]:
    return [
        WholeTextGrammar(
            "month_day_office",
            lambda text, fallback_department: text_parser._parse_month_day_office_pdf_text(
                text,
                fallback_department=fallback_department,
            ),
        ),
        WholeTextGrammar(
            "yearless_council_amount",
            lambda text, fallback_department: text_parser._parse_yearless_council_amount_pdf_text(
                text,
                fallback_department=fallback_department,
            ),
        ),
        WholeTextGrammar(
            "user_place_purpose_layout",
            lambda text, fallback_department: text_parser._parse_user_place_purpose_layout_pdf_text(
                text,
                fallback_department=fallback_department,
            ),
        ),
        WholeTextGrammar(
            "layout_office",
            lambda text, fallback_department: text_parser._parse_layout_office_pdf_text(
                text,
                fallback_department=fallback_department,
            ),
        ),
        WholeTextGrammar(
            "segmented_office",
            lambda text, fallback_department: text_parser._parse_segmented_office_pdf_text(
                text,
                fallback_department=fallback_department,
            ),
        ),
    ]


def build_default_grammars() -> tuple[list[PdfTextGrammar], list[PdfTextGrammar]]:
    line_grammars = [g for g in _build_default_line_grammars() if g.name in LINE_GRAMMAR_ORDER]
    whole_text_grammars = [
        g for g in _build_default_whole_text_grammars() if g.name in WHOLE_TEXT_FALLBACK_ORDER
    ]
    return line_grammars, whole_text_grammars


__all__ = [
    "PdfTextGrammar",
    "LineGrammar",
    "WholeTextGrammar",
    "build_default_grammars",
]
