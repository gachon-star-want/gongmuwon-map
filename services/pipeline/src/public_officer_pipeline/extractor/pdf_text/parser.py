from __future__ import annotations

from typing import Protocol, Sequence

from pydantic import BaseModel

from public_officer_pipeline.models import ParsedExpenseRow


class PdfParseDiagnostic(BaseModel):
    grammar_name: str
    row_count: int = 0
    failed_reason: str | None = "no rows matched this grammar"


class PdfParseResult(BaseModel):
    rows: list[ParsedExpenseRow]
    diagnostics: list[PdfParseDiagnostic]


class PdfTextGrammar(Protocol):
    name: str

    def parse(self, text: str, *, fallback_department: str) -> list[ParsedExpenseRow]:
        ...


LINE_GRAMMAR_ORDER: tuple[str, ...] = (
    "user_address",
    "date_user_amount_place",
    "purpose_place_amount",
    "date_purpose_party_amount_place",
    "region_amount_place_purpose",
    "optional_user_place_purpose_amount",
    "user_amount_place_address_purpose",
    "council_user_place",
    "user_place_purpose_amount",
    "user_place_purpose_category",
    "compact_date_purpose_place",
    "user_amount_purpose",
    "user_no_address",
    "purpose_first",
    "generic_text_row",
)

WHOLE_TEXT_FALLBACK_ORDER: tuple[str, ...] = (
    "user_place_purpose_layout",
    "layout_office",
    "segmented_office",
)


def parse_pdf_text_with_diagnostics(
    text: str,
    *,
    fallback_department: str,
    line_grammars: Sequence[PdfTextGrammar],
    whole_text_grammars: Sequence[PdfTextGrammar],
) -> PdfParseResult:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    diagnostics = [PdfParseDiagnostic(grammar_name=name) for name in LINE_GRAMMAR_ORDER]
    diagnostics.extend(PdfParseDiagnostic(grammar_name=name) for name in WHOLE_TEXT_FALLBACK_ORDER)
    diagnostic_by_name = {diagnostic.grammar_name: diagnostic for diagnostic in diagnostics}

    rows: list[ParsedExpenseRow] = []
    line_by_name = {grammar.name: grammar for grammar in line_grammars}
    line_names = [name for name in LINE_GRAMMAR_ORDER if name in line_by_name]
    for line in lines:
        for name in line_names:
            grammar = line_by_name[name]
            parsed = grammar.parse(line, fallback_department=fallback_department)
            if parsed:
                diagnostic = diagnostic_by_name[name]
                diagnostic.row_count += len(parsed)
                diagnostic.failed_reason = None
                rows.extend(parsed)
                break

    if rows:
        return PdfParseResult(rows=rows, diagnostics=diagnostics)

    whole_by_name = {grammar.name: grammar for grammar in whole_text_grammars}
    whole_text_names = [name for name in WHOLE_TEXT_FALLBACK_ORDER if name in whole_by_name]
    for name in whole_text_names:
        grammar = whole_by_name[name]
        parsed = grammar.parse(text, fallback_department=fallback_department)
        if parsed:
            diagnostic = diagnostic_by_name[name]
            diagnostic.row_count += len(parsed)
            diagnostic.failed_reason = None
            rows.extend(parsed)
            break
        diagnostic_by_name[name].row_count = 0

    return PdfParseResult(rows=rows, diagnostics=diagnostics)
