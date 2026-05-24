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


def test_extracts_council_cost_xlsx_header_variants() -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "부의장"
    worksheet.append(["부의장 활동비 집행내역(4월)"])
    worksheet.append([])
    worksheet.append(["사용자", "일 자", "시간", "집행처 명", "집행내역", "집행처 주소", "집행방법", "금액", "인원", "비고"])
    worksheet.append(
        [
            "이충현",
            "2026-04-01",
            "12:29",
            "당진아구동태찜탕",
            "의정활동설명 및 민원청취",
            "양천구 등촌로 182",
            "법인카드",
            55000,
            4,
            None,
        ]
    )
    content = BytesIO()
    workbook.save(content)

    rows = extract_spreadsheet_rows(content.getvalue(), fallback_department="강서구의회")

    assert len(rows) == 1
    assert rows[0].place_text == "당진아구동태찜탕 (양천구 등촌로 182)"
    assert rows[0].purpose == "의정활동설명 및 민원청취"
    assert rows[0].payment_method == "법인카드"
    assert rows[0].user_text == "이충현 4명"
