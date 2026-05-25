from public_officer_pipeline.llm.schema import _loads_json_response, _repair_common_json_response


def test_loads_fenced_json_with_nested_rows() -> None:
    parsed = _loads_json_response(
        """```json
{"rows":[{"place_text":"반가안동국시","amount":336000}]}
```"""
    )

    assert parsed["rows"][0]["place_text"] == "반가안동국시"


def test_repair_common_json_response_handles_missing_commas() -> None:
    repaired = _repair_common_json_response(
        """{"rows":[
{"place_text":"반가안동국시","amount":336000}
{"place_text":"삼우정","amount":120000}
]}"""
    )
    assert repaired == """{"rows":[
{"place_text":"반가안동국시","amount":336000},
{"place_text":"삼우정","amount":120000}
]}"""


def test_loads_json_repairs_missing_commas_between_rows() -> None:
    parsed = _loads_json_response(
        """{"rows":[
{"place_text":"반가안동국시","amount":336000}
{"place_text":"삼우정","amount":120000}
]}"""
    )

    assert [row["place_text"] for row in parsed["rows"]] == ["반가안동국시", "삼우정"]
