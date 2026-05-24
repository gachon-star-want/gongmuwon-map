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


def test_rows_from_pdf_text_parses_purpose_first_pdf_table_rows() -> None:
    rows = rows_from_pdf_text(
        """
1    2026-04-01 09:03 의정활동 의견 수렴을 위한 관계자 간담회 비용 지출      195,000   카드     ㈜토다코리아        15
13   2026-04-10 12:51 의정활동 의견 수렴을 위한 관계자 간담회 비용 지출       48,200   계좌이체   파리크라상 서래점     6
        """,
        fallback_department="서초구의회 의장",
    )

    assert len(rows) == 2
    assert rows[0].place_text == "㈜토다코리아"
    assert rows[0].purpose == "의정활동 의견 수렴을 위한 관계자 간담회 비용 지출"
    assert rows[0].amount == 195000
    assert rows[0].user_text == "서초구의회 의장 15명"
    assert rows[1].payment_method == "계좌이체"


def test_rows_from_pdf_text_parses_user_address_pdf_table_rows() -> None:
    rows = rows_from_pdf_text(
        """
1    행정기획위원장   2026-04-01   08:10:04   좋은소리카페（길음실   서울 성북구 삼양로2길 55       지역 현안 업무 협의                    5     29,500    카드    의회운영
3    부의장       2026-04-01   12:25:47   우리풍천장어       서울 성북구 장월로 148-1      지역 현안 논의를 위한 유관기관 관계자 간담회      6     78,000    카드    의회운영
        """,
        fallback_department="성북구의회",
    )

    assert len(rows) == 2
    assert rows[0].place_text == "좋은소리카페（길음실(서울 성북구 삼양로2길 55)"
    assert rows[0].purpose == "지역 현안 업무 협의"
    assert rows[0].amount == 29500
    assert rows[0].user_text == "구의원 5명"
    assert rows[0].expense_category == "의회운영"
    assert rows[1].place_text == "우리풍천장어(서울 성북구 장월로 148-1)"
    assert rows[1].payment_method == "카드"


def test_rows_from_pdf_text_parses_user_no_address_pdf_table_rows() -> None:
    rows = rows_from_pdf_text(
        """
 1    부의장      2026. 4. 1. 18:26      본가한우생고기           의정활동 및 직무수행과 관련된 소요경비                5명   124,300  카드    의회운영
 3   의회운영위원장   2026. 4. 2. 12:30    혜리여수돌산갓김치 의회운영위원장 의정활동 및 직무수행과 관련된 소요 경비                 3명    55,000  카드    의회운영
 의정팀장    2026. 1. 1. 09:20     굴다리전주콩나물국밥            의정현안업무 협의 관련 업무추진               12명   177,000    카드    시책
 1   의회사무국직원 등    2026. 2. 2. 12:17 가마솥밥상 의회사무국 직원 격려 소요경비     7명    92,000  카드    기관
        """,
        fallback_department="광진구의회",
    )

    assert len(rows) == 4
    assert rows[0].used_at.isoformat() == "2026-04-01T18:26:00"
    assert rows[0].place_text == "본가한우생고기"
    assert rows[0].amount == 124300
    assert rows[0].user_text == "구의원 5명"
    assert rows[1].place_text == "혜리여수돌산갓김치"
    assert rows[1].purpose == "의회운영위원장 의정활동 및 직무수행과 관련된 소요 경비"
    assert rows[2].place_text == "굴다리전주콩나물국밥"
    assert rows[3].place_text == "가마솥밥상"
    assert rows[3].purpose == "의회사무국 직원 격려 소요경비"


def test_rows_from_pdf_text_parses_user_amount_purpose_pdf_table_rows() -> None:
    rows = rows_from_pdf_text(
        """
1    의정팀     2026.01.05    12:09:50                        막내네       144,000      의정업무 추진 관련 간담회비 지출          9     신용카드     시책
14   의정팀     2026.01.13    09:54:36                가까운온누리약국           30,000         부서운영 음료구입비 지출                  신용카드    부서운영
        """,
        fallback_department="양천구의회 사무국",
    )

    assert len(rows) == 2
    assert rows[0].place_text == "막내네"
    assert rows[0].amount == 144000
    assert rows[0].user_text == "의정팀 9명"
    assert rows[0].payment_method == "신용카드"
    assert rows[1].place_text == "가까운온누리약국"
    assert rows[1].user_text == "의정팀"
    assert rows[1].expense_category == "부서운영"
