import pytest

from public_officer_pipeline.extractor import extract_hwp_rows
from public_officer_pipeline.extractor import hwp as hwp_module
from public_officer_pipeline.extractor.hwp import _expense_rows_from_text_items
from public_officer_pipeline.models import PipelineConfigError


HWP5_HEADER = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def test_extracts_hwp_table_rows_from_converted_html(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html>
      <body>
        <table>
          <tr><td>부서명: 정부법무공단</td></tr>
        </table>
        <table>
          <tr>
            <td>사용일자</td>
            <td>사용장소</td>
            <td>집행목적</td>
            <td>대상인원</td>
            <td>금액</td>
            <td>결제방법</td>
          </tr>
          <tr>
            <td>2026-05-13</td>
            <td>법무식당</td>
            <td>소송업무 협의</td>
            <td>4</td>
            <td>48,000</td>
            <td>카드</td>
          </tr>
        </table>
      </body>
    </html>
    """.encode()
    monkeypatch.setattr(hwp_module, "_convert_hwp_to_html", lambda _content: html)

    rows = extract_hwp_rows(HWP5_HEADER + b"hwp-body", fallback_department="대한법률구조공단")

    assert len(rows) == 1
    assert rows[0].department_name == "대한법률구조공단"
    assert rows[0].place_text == "법무식당"
    assert rows[0].purpose == "소송업무 협의"
    assert rows[0].amount == 48000
    assert rows[0].user_text == "대한법률구조공단 4명"
    assert rows[0].payment_method == "카드"


def test_hwp_extractor_rejects_non_hwp5_input() -> None:
    with pytest.raises(PipelineConfigError, match="HWP 5.x"):
        extract_hwp_rows(b"not a hwp document", fallback_department="정부법무공단")


def test_reconstructs_fragmented_hwp_expense_rows() -> None:
    rows = _expense_rows_from_text_items(
        [
            "도지사 업무추진비 사용내역 ('26. 2월)",
            "연번",
            "사용자",
            "사용일자",
            "사용장소 (가맹점명)",
            "사 용 목 적(내역) *사용대상 포함",
            "사용금액(원)",
            "대상인원(명)",
            "사용방법",
            "구분",
            "비고 (사용시간)",
            "1",
            "도지사",
            "2",
            "2",
            "유한회사",
            "다농푸드",
            "내방객 제공용 다과 등 구입",
            "39,100",
            "카드",
            "기관",
            "13:02",
            "2",
            "도지사",
            "2",
            "4",
            "카페유알피",
            "행정통합 관련 도의회 현안업무",
            "추진관계자 등 간담",
            "52,800",
            "도지사, 기획조정실장 등 19",
            "카드",
            "시책",
            "10:56",
        ],
        fallback_department="전라남도청 도지사",
        fallback_year=2026,
    )

    assert len(rows) == 2
    assert rows[0].department_name == "전라남도청 도지사"
    assert rows[0].used_at.isoformat() == "2026-02-02T13:02:00"
    assert rows[0].place_text == "유한회사 다농푸드"
    assert rows[0].purpose == "내방객 제공용 다과 등 구입"
    assert rows[0].amount == 39100
    assert rows[0].user_text == "도지사"
    assert rows[0].payment_method == "카드"
    assert rows[0].expense_category == "기관"
    assert rows[1].used_at.isoformat() == "2026-02-04T10:56:00"
    assert rows[1].place_text == "카페유알피"
    assert rows[1].purpose == "행정통합 관련 도의회 현안업무 추진관계자 등 간담"
    assert rows[1].user_text == "도지사 19명"
