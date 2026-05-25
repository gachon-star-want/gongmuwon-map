import pytest

from public_officer_pipeline.agencies import GYEONGGI_AGENCIES, INCHEON_AGENCIES, SEOUL_AGENCIES
from public_officer_pipeline.models import Agency
from public_officer_pipeline.source_pattern import (
    AdapterRequiredPattern,
    SourcePatternError,
    parse_source_pattern,
)


def test_parse_source_patterns_for_all_seoul_agencies() -> None:
    for agency in SEOUL_AGENCIES:
        parse_source_pattern(agency)


def test_parse_gyeonggi_and_incheon_require_adapter_required_pattern() -> None:
    for agency in GYEONGGI_AGENCIES + INCHEON_AGENCIES:
        parsed = parse_source_pattern(agency)
        assert isinstance(parsed, AdapterRequiredPattern)
        assert parsed.status == "adapter_required"


def test_attachment_pattern_missing_list_url_raises() -> None:
    with pytest.raises(SourcePatternError):
        parse_source_pattern(
            Agency(
                source_pattern={
                    "adapter": "attachment_board",
                    "fileKinds": ["pdf"],
                }
            )
        )


def test_attachment_pattern_invalid_file_kind_raises() -> None:
    with pytest.raises(SourcePatternError):
        parse_source_pattern(
            Agency(
                source_pattern={
                    "adapter": "attachment_board",
                    "listUrl": "https://example.com/list",
                    "fileKinds": ["exe", "zip"],
                }
            )
        )
