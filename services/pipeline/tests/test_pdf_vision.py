from public_officer_pipeline.extractor.pdf_vision import rows_from_pdf_text, rows_from_vision_payload
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


def test_loads_json_repairs_missing_commas_between_rows() -> None:
    parsed = _loads_json_response(
        """{"rows":[
{"place_text":"반가안동국시","amount":336000}
{"place_text":"삼우정","amount":120000}
]}"""
    )

    assert [row["place_text"] for row in parsed["rows"]] == ["반가안동국시", "삼우정"]


def test_rows_from_pdf_text_parses_printed_pdf_table_rows() -> None:
    rows = rows_from_pdf_text(
        """
 1              2026.04.01.     12:40        네이버                      의원실 내방객 접대용 간식 구매          22,000         신용카드
 2      의정팀장    2026.04.06     20:17:13     김상현참치                 원활한 의회운영을 위하여 관계자 간담회 실시       202,000   6    신용카드
        """,
        fallback_department="금천구의회 사무국",
    )

    assert len(rows) == 2
    assert rows[0].place_text == "네이버"
    assert rows[0].amount == 22000
    assert rows[1].used_at.isoformat() == "2026-04-06T20:17:13"
    assert rows[1].user_text == "의정팀장 6명"
