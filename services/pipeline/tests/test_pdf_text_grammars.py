from __future__ import annotations

from public_officer_pipeline.extractor import pdf_vision
from public_officer_pipeline.extractor.pdf_text import build_default_grammars, parse_pdf_text_with_diagnostics


def test_pdf_text_parser_selects_expected_line_grammar_for_each_representative_case() -> None:
    line_grammars, whole_text_grammars = build_default_grammars()

    samples = {
        "user_address": "1    행정기획위원장   2026-04-01   08:10:04   좋은소리카페（길음실   서울 성북구 삼양로2길 55       지역 현안 업무 협의                    5     29,500    카드    의회운영",
        "date_user_amount_place": "1   2026.04.01   11:57:10   의장    218,000       김삼보        의정활동 및 직무활동을 위한 경비     17      카드     의회운영업무추진비",
        "purpose_place_amount": "1    2026-01-02 11:39   의정활동 홍보를 위한 언론 관계자 간담회   단정                     3         42,000    카드",
        "date_purpose_party_amount_place": "2026.04.01. 12:00 도시농업 활성화 방안 논의를 위한 간담회 4 77,400 황제삼계탕, 참새커피 카드",
        "region_amount_place_purpose": "서울시 성동구    2026-01-02   12:19:13   220,000              부성식당              의정활동 및 업무추진을 위한 각종 회의·간담회·행사   10    카드       의장",
        "optional_user_place_purpose_amount": "1            2026.04.01    12:09:03    원양참치        2026년 상반기 청소년 의회교실 개최 관련 간담회        7     203,000   신용카드   시책",
        "user_amount_place_address_purpose": "1     의장     2026.01.05   13:00:30     334,000       화사랑화로구이          선유로9가길 16          지역 현안사항 논의를 위한 간담회 개최         의원 등   12명   카드",
        "user_place_purpose_amount": "의장    2026-04-01   08:42:47 파리바게뜨       종로구청   의회 현한업무 관련 간담회            100,000        6    카드",
        "user_amount_purpose": "1    의정팀     2026.01.13    09:54:36                가까운온누리약국           30,000         부서운영 음료구입비 지출                  신용카드    부서운영",
        "user_no_address": " 1    부의장      2026. 4. 1. 18:26      본가한우생고기           의정활동 및 직무수행과 관련된 소요경비                5명   124,300  카드    의회운영",
        "purpose_first": "1    2026-04-01 09:03 의정활동 의견 수렴을 위한 관계자 간담회 비용 지출      195,000   카드     ㈜토다코리아        15",
        "generic_text_row": " 1              2026.04.01.     12:40        네이버                      의원실 내방객 접대용 간식 구매          22,000         신용카드",
    }

    for expected_grammar, text in samples.items():
        result = parse_pdf_text_with_diagnostics(
            text,
            fallback_department="테스트",
            line_grammars=line_grammars,
            whole_text_grammars=whole_text_grammars,
        )

        assert [diag.row_count for diag in result.diagnostics if diag.row_count] == [1]
        winners = {diag.grammar_name for diag in result.diagnostics if diag.row_count > 0}
        assert winners == {expected_grammar}
        assert next(diag.failed_reason for diag in result.diagnostics if diag.grammar_name == expected_grammar) is None


def test_pdf_text_parser_uses_earlier_grammar_when_multiple_patterns_match() -> None:
    line_grammars, whole_text_grammars = build_default_grammars()
    overlapping_line = "1    2026.04.01   11:57:10   의장    218,000       김삼보        의정활동 및 직무활동을 위한 경비     17      카드     의회운영업무추진비"

    result = parse_pdf_text_with_diagnostics(
        overlapping_line,
        fallback_department="테스트",
        line_grammars=line_grammars,
        whole_text_grammars=whole_text_grammars,
    )

    winners = [diag.grammar_name for diag in result.diagnostics if diag.row_count > 0]
    assert winners == ["date_user_amount_place"]
    assert len(result.rows) == 1
    assert result.rows[0].place_text == "김삼보"


def test_pdf_text_parser_selects_central_state_grammars() -> None:
    line_grammars, whole_text_grammars = build_default_grammars()
    samples = [
        (
            "central_state_purpose_place_amount",
            "경찰청 범죄예방대응국장",
            "2026-04-06 성매매광고차단시스템 개선 사전검토     커피빈코리아 순화점      46,000       6명     카드",
            "커피빈코리아 순화점",
            46000,
        ),
        (
            "central_state_amount_place_purpose",
            "통일부",
            "2026-04-02   12:44    178,000        해초가           간담회 개최     4",
            "해초가",
            178000,
        ),
        (
            "central_state_place_purpose_amount",
            "보건복지부",
            "2026-03-03           도마              업무홍보 관련 협의      400,000     14",
            "도마",
            400000,
        ),
        (
            "central_state_user_place_purpose_amount",
            "보건복지부",
            "대변인 2026-01-06 11:35 한화커넥트 (주)     출입기자단 간담회     71,000 4 카드",
            "한화커넥트 (주)",
            71000,
        ),
    ]

    for expected_grammar, department, text, place_text, amount in samples:
        result = parse_pdf_text_with_diagnostics(
            text,
            fallback_department=department,
            line_grammars=line_grammars,
            whole_text_grammars=whole_text_grammars,
        )

        winners = {diag.grammar_name for diag in result.diagnostics if diag.row_count > 0}
        assert winners == {expected_grammar}
        assert len(result.rows) == 1
        assert result.rows[0].place_text == place_text
        assert result.rows[0].amount == amount


def test_pdf_text_parser_uses_whole_text_fallback_only_when_line_parsing_fails() -> None:
    line_grammars, whole_text_grammars = build_default_grammars()
    layout_text = """
               집행일시        집행장소        집행목적         집행금액 대상인원
연번    사용자                                                            결제방법
              (결제시간)       (가맹점명)       (내역)         (원)       (명)

              2026-04-01 ㈜장수마늘  강북구 스마트팜센터
1    교육협력팀장                    체험 프로그램 지원 사업          63,000   5     법인카드
                 12:12     보쌈
                                운영 관계자 간담회
"""

    result = parse_pdf_text_with_diagnostics(
        layout_text,
        fallback_department="테스트",
        line_grammars=line_grammars,
        whole_text_grammars=whole_text_grammars,
    )

    assert len(result.rows) == 1
    fallback_winner = {diag.grammar_name: diag for diag in result.diagnostics}
    assert fallback_winner["user_address"].row_count == 0
    assert fallback_winner["user_place_purpose_layout"].row_count == 1
    assert fallback_winner["layout_office"].row_count == 0
    assert fallback_winner["segmented_office"].row_count == 0
    assert fallback_winner["user_place_purpose_layout"].failed_reason is None
    assert result.rows[0].place_text == "㈜장수마늘 보쌈"


def test_pdf_text_parser_reports_failures_when_no_text_matches() -> None:
    line_grammars, whole_text_grammars = build_default_grammars()
    result = parse_pdf_text_with_diagnostics(
        "\n\n안전 안내 문구\n무관한 텍스트",
        fallback_department="테스트",
        line_grammars=line_grammars,
        whole_text_grammars=whole_text_grammars,
    )

    assert len(result.rows) == 0
    assert all(diag.row_count == 0 for diag in result.diagnostics)
    assert all(diag.failed_reason is not None for diag in result.diagnostics)


def test_pdf_text_module_rows_interface_matches_pdf_vision_wrapper() -> None:
    from public_officer_pipeline.extractor.pdf_text import rows_from_pdf_text

    fallback_department = "성동구의회 사무국"
    sample_text = """
1    2026-01-02 11:39   의정활동 홍보를 위한 언론 관계자 간담회   단정                     3         42,000    카드
    """

    module_rows = rows_from_pdf_text(sample_text, fallback_department=fallback_department)
    wrapper_rows = pdf_vision.rows_from_pdf_text(sample_text, fallback_department=fallback_department)

    assert len(module_rows) == 1
    assert module_rows[0].department_name == fallback_department
    assert module_rows[0].amount == 42000
    assert module_rows[0].payment_method == "카드"
    assert [row.model_dump(mode="json") for row in module_rows] == [
        row.model_dump(mode="json") for row in wrapper_rows
    ]
