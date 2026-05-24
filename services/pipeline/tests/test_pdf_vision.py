from public_officer_pipeline.extractor.pdf_vision import rows_from_vision_payload
from public_officer_pipeline.normalizer.llm import _loads_json_response


def test_rows_from_vision_payload_parses_expense_rows() -> None:
    rows = rows_from_vision_payload(
        {
            "rows": [
                {
                    "department_name": "강남구의회 의장",
                    "used_at": "2026-01-05T13:23:00",
                    "place_text": "반가안동국시(서울 강남구 광평로46길 5)",
                    "purpose": "원활한 의정활동을 위한 간담회",
                    "amount": "336,000",
                    "user_text": "구의원 12명",
                    "payment_method": "카드",
                    "raw_excerpt": "2026-01-05 | 반가안동국시 | 336,000",
                }
            ]
        },
        fallback_department="강남구의회",
    )

    assert len(rows) == 1
    assert rows[0].department_name == "강남구의회 의장"
    assert rows[0].place_text == "반가안동국시(서울 강남구 광평로46길 5)"
    assert rows[0].amount == 336000


def test_loads_fenced_json_with_nested_rows() -> None:
    parsed = _loads_json_response(
        """```json
{"rows":[{"place_text":"반가안동국시","amount":336000}]}
```"""
    )

    assert parsed["rows"][0]["place_text"] == "반가안동국시"
