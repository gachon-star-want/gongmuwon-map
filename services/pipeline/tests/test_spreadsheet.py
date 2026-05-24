from io import BytesIO

from openpyxl import Workbook

from public_officer_pipeline.extractor import extract_spreadsheet_rows


def test_extracts_gangnam_xlsx_rows() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "공개"
    worksheet.append(["2026년 4월 업무추진비 집행내역"])
    worksheet.append(["□ 부서명 : 지방소득세과"])
    worksheet.append([])
    worksheet.append(["연번", "집행일자", "집행시간", "사용자", "장소", "집행 목적", "대상 인원수", "금액", "결제방법", "비목"])
    worksheet.append(
        [
            1,
            "2026-04-30",
            "19:47:37",
            "지방소득세과장",
            "남도사계고운님",
            "세무서 업무 협의",
            6,
            121000,
            "카드결제",
            "시책",
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="강남구청")

    assert len(rows) == 1
    assert rows[0].department_name == "지방소득세과"
    assert rows[0].place_text == "남도사계고운님"
    assert rows[0].amount == 121000
    assert rows[0].user_text == "지방소득세과장 6명"
