from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from public_officer_pipeline import document_guards as guards
from public_officer_pipeline.extractor.spreadsheet import extract_spreadsheet_rows
from public_officer_pipeline.models import ParsedExpenseRow, PipelineConfigError


HWP5_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def extract_hwp_rows(content: bytes, *, fallback_department: str) -> list[ParsedExpenseRow]:
    guards.ensure_size_at_most(
        size=len(content),
        max_bytes=guards.MAX_DOCUMENT_DOWNLOAD_BYTES,
        subject="HWP document",
    )
    if not content.startswith(HWP5_OLE_MAGIC):
        raise PipelineConfigError("HWP extractor requires a binary HWP 5.x OLE document")

    html = _convert_hwp_to_html(content)
    return extract_spreadsheet_rows(html, fallback_department=fallback_department)


def _convert_hwp_to_html(content: bytes) -> bytes:
    soffice = shutil.which("soffice")
    if not soffice:
        raise PipelineConfigError(
            "HWP extraction requires LibreOffice CLI (`soffice`) or a future hwp5txt adapter"
        )

    with tempfile.TemporaryDirectory(prefix="public-officer-hwp-") as tmp:
        tmp_path = Path(tmp)
        input_path = tmp_path / "input.hwp"
        input_path.write_bytes(content)
        command = [
            soffice,
            "--headless",
            "--convert-to",
            "html",
            "--outdir",
            str(tmp_path),
            str(input_path),
        ]
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                timeout=guards.PDF_SUBPROCESS_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise PipelineConfigError("LibreOffice HWP conversion timed out") from exc

        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            stdout = result.stdout.decode("utf-8", errors="replace").strip()
            message = stderr or stdout or f"exit code {result.returncode}"
            raise PipelineConfigError(f"LibreOffice HWP conversion failed: {message}")

        output_candidates = sorted(
            path
            for path in tmp_path.iterdir()
            if path.suffix.lower() in {".html", ".htm"} and path.name != input_path.name
        )
        if not output_candidates:
            raise PipelineConfigError("LibreOffice HWP conversion produced no HTML output")

        output_path = output_candidates[0]
        guards.ensure_size_at_most(
            size=output_path.stat().st_size,
            max_bytes=guards.MAX_SPREADSHEET_BYTES,
            subject="converted HWP HTML",
        )
        return output_path.read_bytes()


__all__ = ["extract_hwp_rows"]
