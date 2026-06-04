from __future__ import annotations

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel

from public_officer_pipeline.models import Agency
from public_officer_pipeline.source_pattern import (
    AlioItemDisclosurePattern,
    AdapterRequiredPattern,
    AttachmentBoardPattern,
    CleanEyeOwnerWorkCostPattern,
    EstimateListPattern,
    InlineExpenseTablePattern,
    SeoulOpenGovPattern,
    SourcePatternError,
    parse_source_pattern,
)

VerificationStatus = Literal[
    "verified_in_code",
    "pending",
    "legal_hold",
    "source_not_found",
    "no_recent_data",
    "pdf_vision_hold",
    "adapter_hold",
    "invalid_source_pattern",
]

GOV_TIER_LABELS = {
    "regional": "광역자치단체",
    "basic": "기초자치단체",
    "national": "국가기관",
    "constitutional": "헌법기관",
    "public": "공공기관",
    "local_public": "지방공공기관",
}
BRANCH_LABELS = {
    "admin": "집행기관",
    "council": "의회",
    "constitutional": "헌법기관",
    "public": "공공기관",
}
JURISDICTION_TYPE_LABELS = {
    "special_city": "특별시",
    "metro_city": "광역시",
    "province": "도",
    "special_self_governing_city": "특별자치시",
    "special_self_governing_province": "특별자치도",
    "autonomous_gu": "자치구",
    "si": "시",
    "gun": "군",
    "central_administrative_agency": "중앙행정기관",
    "constitutional_institution": "헌법기관",
    "independent_state_agency": "독립국가기관",
    "public_institution": "지정 공공기관",
    "local_public_institution": "지방공공기관",
}
PRIORITY_GROUP_LABELS = {
    "p1": "P1 지방자치단체·의회",
    "p2": "P2 중앙행정기관·독립기관",
    "p3": "P3 지정 공공기관",
    "p4": "P4 지방공공기관",
}
VERIFICATION_STATUS_LABELS: dict[VerificationStatus, str] = {
    "verified_in_code": "코드 검증 완료",
    "pending": "공식 출처 검증 대기",
    "legal_hold": "법적 검토 보류",
    "source_not_found": "공식 출처 미발견",
    "no_recent_data": "최근 12개월 데이터 없음",
    "pdf_vision_hold": "PDF vision 보류",
    "adapter_hold": "어댑터/파서 보류",
    "invalid_source_pattern": "출처 패턴 오류",
}


class SourceRegistryEntry(BaseModel):
    agency_id: str
    name: str
    short_name: str
    parent_region: str
    sub_region: str | None
    gov_tier: str
    gov_tier_label: str
    branch: str
    branch_label: str
    jurisdiction_type: str
    jurisdiction_type_label: str
    priority_group: str
    priority_group_label: str
    adapter: str | None
    verification_status: VerificationStatus
    verification_status_label: str
    source_url: str | None
    source_file_kinds: list[str]
    baseline_source_url: str | None
    homepage: str | None
    verified_at: str | None
    verified_by: str | None
    evidence_note: str


class SourceRegistryPhaseSummary(BaseModel):
    total: int
    verified_in_code: int
    pending: int
    legal_hold: int = 0
    source_not_found: int = 0
    no_recent_data: int = 0
    pdf_vision_hold: int = 0
    adapter_hold: int = 0
    invalid_source_pattern: int


class SourceRegistrySummary(BaseModel):
    total: int
    verified_in_code: int
    pending: int
    legal_hold: int = 0
    source_not_found: int = 0
    no_recent_data: int = 0
    pdf_vision_hold: int = 0
    adapter_hold: int = 0
    invalid_source_pattern: int
    priority_group_counts: dict[str, SourceRegistryPhaseSummary]


def source_registry_entries(agencies: list[Agency]) -> list[SourceRegistryEntry]:
    return [_source_registry_entry(agency) for agency in agencies]


def source_registry_summary(entries: list[SourceRegistryEntry]) -> SourceRegistrySummary:
    priority_group_counts = {
        priority_group: SourceRegistryPhaseSummary(
            total=sum(1 for entry in entries if entry.priority_group == priority_group),
            verified_in_code=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group
                and entry.verification_status == "verified_in_code"
            ),
            pending=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group and entry.verification_status == "pending"
            ),
            legal_hold=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group and entry.verification_status == "legal_hold"
            ),
            source_not_found=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group
                and entry.verification_status == "source_not_found"
            ),
            no_recent_data=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group and entry.verification_status == "no_recent_data"
            ),
            pdf_vision_hold=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group
                and entry.verification_status == "pdf_vision_hold"
            ),
            adapter_hold=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group and entry.verification_status == "adapter_hold"
            ),
            invalid_source_pattern=sum(
                1
                for entry in entries
                if entry.priority_group == priority_group
                and entry.verification_status == "invalid_source_pattern"
            ),
        )
        for priority_group in PRIORITY_GROUP_LABELS
    }
    return SourceRegistrySummary(
        total=len(entries),
        verified_in_code=sum(1 for entry in entries if entry.verification_status == "verified_in_code"),
        pending=sum(1 for entry in entries if entry.verification_status == "pending"),
        legal_hold=sum(1 for entry in entries if entry.verification_status == "legal_hold"),
        source_not_found=sum(1 for entry in entries if entry.verification_status == "source_not_found"),
        no_recent_data=sum(1 for entry in entries if entry.verification_status == "no_recent_data"),
        pdf_vision_hold=sum(1 for entry in entries if entry.verification_status == "pdf_vision_hold"),
        adapter_hold=sum(1 for entry in entries if entry.verification_status == "adapter_hold"),
        invalid_source_pattern=sum(
            1 for entry in entries if entry.verification_status == "invalid_source_pattern"
        ),
        priority_group_counts=priority_group_counts,
    )


def _source_registry_entry(agency: Agency) -> SourceRegistryEntry:
    raw = agency.source_pattern
    adapter = raw.get("adapter") if isinstance(raw, dict) else None
    verified_at = _optional_str(raw.get("verifiedAt") if isinstance(raw, dict) else None)
    verified_by = _optional_str(raw.get("verifiedBy") if isinstance(raw, dict) else None)
    baseline_source_url = _optional_str(
        raw.get("baselineSourceUrl") if isinstance(raw, dict) else None
    )
    source_file_kinds = _source_file_kinds(raw)

    try:
        pattern = parse_source_pattern(agency)
    except SourcePatternError as exc:
        return _entry(
            agency,
            adapter=adapter,
            verification_status="invalid_source_pattern",
            source_url=None,
            source_file_kinds=source_file_kinds,
            baseline_source_url=baseline_source_url,
            verified_at=verified_at,
            verified_by=verified_by,
            evidence_note=str(exc),
        )

    if isinstance(pattern, AdapterRequiredPattern):
        return _entry(
            agency,
            adapter=pattern.adapter,
            verification_status=_adapter_required_status(raw),
            source_url=_adapter_required_source_url(agency, raw),
            source_file_kinds=source_file_kinds,
            baseline_source_url=baseline_source_url,
            verified_at=verified_at,
            verified_by=verified_by,
            evidence_note=_pending_evidence_note(raw),
        )

    source_url = _source_url(pattern)
    source_error = _source_verification_error(
        agency,
        raw=raw,
        source_url=source_url,
        verified_at=verified_at,
        verified_by=verified_by,
    )
    if source_error:
        return _entry(
            agency,
            adapter=pattern.adapter,
            verification_status="invalid_source_pattern",
            source_url=source_url,
            source_file_kinds=source_file_kinds,
            baseline_source_url=baseline_source_url,
            verified_at=verified_at,
            verified_by=verified_by,
            evidence_note=source_error,
        )
    return _entry(
        agency,
        adapter=pattern.adapter,
        verification_status="verified_in_code",
        source_url=source_url,
        source_file_kinds=source_file_kinds,
        baseline_source_url=baseline_source_url,
        verified_at=verified_at,
        verified_by=verified_by,
        evidence_note=_verified_evidence_note(raw),
    )


def _entry(
    agency: Agency,
    *,
    adapter: str | None,
    verification_status: VerificationStatus,
    source_url: str | None,
    source_file_kinds: list[str],
    baseline_source_url: str | None,
    verified_at: str | None,
    verified_by: str | None,
    evidence_note: str,
) -> SourceRegistryEntry:
    return SourceRegistryEntry(
        agency_id=str(agency.id),
        name=agency.name,
        short_name=agency.short_name,
        parent_region=agency.parent_region,
        sub_region=agency.sub_region,
        gov_tier=agency.gov_tier.value,
        gov_tier_label=GOV_TIER_LABELS.get(agency.gov_tier.value, agency.gov_tier.value),
        branch=agency.branch.value,
        branch_label=BRANCH_LABELS.get(agency.branch.value, agency.branch.value),
        jurisdiction_type=agency.jurisdiction_type.value,
        jurisdiction_type_label=JURISDICTION_TYPE_LABELS.get(
            agency.jurisdiction_type.value,
            agency.jurisdiction_type.value,
        ),
        priority_group=agency.expansion_phase.value,
        priority_group_label=PRIORITY_GROUP_LABELS.get(
            agency.expansion_phase.value,
            agency.expansion_phase.value,
        ),
        adapter=adapter,
        verification_status=verification_status,
        verification_status_label=VERIFICATION_STATUS_LABELS[verification_status],
        source_url=source_url,
        source_file_kinds=source_file_kinds,
        baseline_source_url=baseline_source_url,
        homepage=agency.homepage,
        verified_at=verified_at,
        verified_by=verified_by,
        evidence_note=evidence_note,
    )


def _source_url(
    pattern: SeoulOpenGovPattern
    | AttachmentBoardPattern
    | EstimateListPattern
    | InlineExpenseTablePattern
    | AlioItemDisclosurePattern
    | CleanEyeOwnerWorkCostPattern,
) -> str:
    if isinstance(pattern, SeoulOpenGovPattern):
        return "https://opengov.seoul.go.kr/expense/list"
    if isinstance(pattern, AlioItemDisclosurePattern | CleanEyeOwnerWorkCostPattern):
        return pattern.sourceUrl
    return pattern.listUrl


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _pending_evidence_note(raw: object) -> str:
    if isinstance(raw, dict):
        blocker = _optional_str(raw.get("blocker"))
        if blocker:
            return blocker
        baseline_evidence = _optional_str(raw.get("baselineEvidence"))
        if baseline_evidence:
            return baseline_evidence
    return "공식 업무추진비 출처 URL 검증 전입니다. adapter_required 상태로 유지합니다."


def _verified_evidence_note(raw: object) -> str:
    if isinstance(raw, dict):
        evidence_note = _optional_str(raw.get("evidenceNote"))
        if evidence_note:
            return evidence_note
    return "코드에 검증된 공식 출처 패턴이 있습니다. 대기 기관의 URL은 추정하지 않습니다."


def _adapter_required_status(raw: object) -> VerificationStatus:
    if isinstance(raw, dict):
        status = raw.get("holdStatus")
        if status in {
            "legal_hold",
            "source_not_found",
            "no_recent_data",
            "pdf_vision_hold",
            "adapter_hold",
        }:
            return status
    return "pending"


def _adapter_required_source_url(agency: Agency, raw: object) -> str | None:
    if not isinstance(raw, dict):
        return None
    return _optional_str(raw.get("sourceUrl"))


def _source_file_kinds(raw: object) -> list[str]:
    if not isinstance(raw, dict):
        return []
    value = raw.get("fileKinds")
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _source_verification_error(
    agency: Agency,
    *,
    raw: object,
    source_url: str,
    verified_at: str | None,
    verified_by: str | None,
) -> str | None:
    if agency.parent_region == "서울특별시":
        return None
    if not verified_at or not verified_by:
        return "신규 권역의 검증 완료 출처 패턴에는 verifiedAt/verifiedBy 근거 필드가 필요합니다."
    source_parts = urlsplit(source_url)
    if source_parts.scheme not in {"http", "https"} or not source_parts.netloc:
        return "출처 URL은 절대 경로의 공식 URL이어야 합니다."
    if isinstance(raw, dict) and raw.get("officialCommonPortal") is True:
        return None
    if not agency.homepage:
        return "신규 권역의 검증 완료 출처 패턴에는 공식 홈페이지가 필요합니다."
    homepage_parts = urlsplit(agency.homepage)
    if homepage_parts.scheme not in {"http", "https"} or not homepage_parts.netloc:
        return "홈페이지는 절대 경로의 공식 URL이어야 합니다."
    source_host = source_parts.netloc.lower()
    homepage_host = homepage_parts.netloc.lower()
    if source_host != homepage_host and not source_host.endswith(f".{homepage_host}"):
        return "출처 URL 호스트는 기관 공식 홈페이지 호스트와 일치해야 합니다."
    return None


__all__ = [
    "SourceRegistryEntry",
    "SourceRegistryPhaseSummary",
    "SourceRegistrySummary",
    "source_registry_entries",
    "source_registry_summary",
]
