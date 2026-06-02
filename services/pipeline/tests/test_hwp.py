import pytest

from public_officer_pipeline.extractor import extract_hwp_rows
from public_officer_pipeline.extractor import hwp as hwp_module
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
