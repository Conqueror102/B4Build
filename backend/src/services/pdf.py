"""PDF rendering for FullPlan artefacts.

Exposes a single public function ``render_plan_pdf`` that turns a
``FullPlan`` (and optional ``RedTeamCritique``) into a multi-page PDF
document returned as raw bytes. The output starts with the ``%PDF``
magic so it can be streamed straight back through FastAPI as
``application/pdf``.

The renderer is intentionally defensive - phase outputs can come in
either dict-of-models or list-of-models shape, fields may be missing,
and the prompt registry import may fail in unit-test contexts where the
LangGraph stack isn't installed. Each access is guarded so a single
malformed phase never poisons the whole document.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..schemas.plan import FullPlan, RedTeamCritique

try:
    from ..prompts import PHASE_REGISTRY
except Exception:  # pragma: no cover - keeps tests independent of graph stack
    PHASE_REGISTRY = {}


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _build_styles() -> dict[str, ParagraphStyle]:
    """Return a small bag of paragraph styles used across the document."""
    base = getSampleStyleSheet()
    return {
        "h1": ParagraphStyle(
            "H1Custom",
            parent=base["Title"],
            fontSize=24,
            leading=28,
            spaceAfter=18,
            textColor=colors.HexColor("#0a0a0a"),
        ),
        "h2": ParagraphStyle(
            "H2Custom",
            parent=base["Heading2"],
            fontSize=16,
            leading=20,
            spaceBefore=8,
            spaceAfter=10,
            textColor=colors.HexColor("#1f2937"),
        ),
        "h3": ParagraphStyle(
            "H3Custom",
            parent=base["Heading3"],
            fontSize=12,
            leading=16,
            spaceBefore=6,
            spaceAfter=4,
            textColor=colors.HexColor("#374151"),
        ),
        "body": ParagraphStyle(
            "BodyCustom",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            spaceAfter=4,
            textColor=colors.HexColor("#111827"),
        ),
        "muted": ParagraphStyle(
            "MutedCustom",
            parent=base["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#6b7280"),
        ),
    }


def _table_style() -> TableStyle:
    """Shared table look used for nested key/value rendering."""
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


# ---------------------------------------------------------------------------
# Value rendering
# ---------------------------------------------------------------------------


def _escape(text: Any) -> str:
    """Escape characters reportlab's mini-HTML parser treats as markup."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render_value(val: Any, styles: dict[str, ParagraphStyle] | None = None) -> Any:
    """Render an arbitrary value as a flowable.

    Recursive contract:
      - ``dict``  -> two-column ``Table`` of key/value rows.
      - ``list``  -> bulleted ``Paragraph`` (one item per line).
      - scalar    -> ``Paragraph`` with the stringified value.
    """
    styles = styles or _build_styles()
    body = styles["body"]

    if val is None:
        return Paragraph("<i>—</i>", body)

    if isinstance(val, dict):
        if not val:
            return Paragraph("<i>(empty)</i>", body)
        rows: list[list[Any]] = []
        for key, sub in val.items():
            rows.append([Paragraph(_escape(key), body), _render_value(sub, styles)])
        table = Table(rows, colWidths=[1.5 * inch, 5.0 * inch])
        table.setStyle(_table_style())
        return table

    if isinstance(val, (list, tuple, set)):
        items = list(val)
        if not items:
            return Paragraph("<i>(none)</i>", body)
        if all(not isinstance(item, (dict, list, tuple, set)) for item in items):
            bullets = "<br/>".join(f"&bull; {_escape(item)}" for item in items)
            return Paragraph(bullets, body)
        rows = [
            [Paragraph(f"{idx + 1}.", body), _render_value(item, styles)]
            for idx, item in enumerate(items)
        ]
        table = Table(rows, colWidths=[0.4 * inch, 6.1 * inch])
        table.setStyle(_table_style())
        return table

    return Paragraph(_escape(val), body)


# ---------------------------------------------------------------------------
# Phase rendering
# ---------------------------------------------------------------------------


def _phase_title(phase_id: str) -> str:
    """Pretty title for a phase, falling back to a humanised id."""
    spec = PHASE_REGISTRY.get(phase_id) if isinstance(PHASE_REGISTRY, dict) else None
    title = getattr(spec, "title", None)
    if title:
        return str(title)
    return phase_id.replace("_", " ").title()


def _to_dict(output: Any) -> dict[str, Any]:
    """Best-effort conversion of a phase output to a plain dict."""
    if output is None:
        return {}
    if isinstance(output, dict):
        return output
    dump = getattr(output, "model_dump", None)
    if callable(dump):
        try:
            return dump()
        except Exception:
            pass
    dict_method = getattr(output, "dict", None)
    if callable(dict_method):
        try:
            return dict_method()
        except Exception:
            pass
    return {"value": output}


def _phase_elements(phase_id: str, output: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Build the heading + body flowables for a single phase."""
    elements: list[Any] = [
        Paragraph(_escape(_phase_title(phase_id)), styles["h2"]),
        Paragraph(f"<i>{_escape(phase_id)}</i>", styles["muted"]),
        Spacer(1, 0.15 * inch),
    ]

    data = _to_dict(output)
    if not data:
        elements.append(Paragraph("<i>No output recorded for this phase.</i>", styles["body"]))
        return elements

    for key, value in data.items():
        elements.append(Paragraph(_escape(str(key).replace("_", " ").title()), styles["h3"]))
        if isinstance(value, (dict, list, tuple, set)):
            elements.append(_render_value(value, styles))
        else:
            elements.append(
                Paragraph(
                    f"<b>{_escape(key)}:</b> {_escape(value)}"
                    if value not in ("", None)
                    else f"<b>{_escape(key)}:</b> <i>—</i>",
                    styles["body"],
                )
            )
        elements.append(Spacer(1, 0.08 * inch))

    return elements


def _iter_phase_outputs(full_plan: FullPlan) -> list[tuple[str, Any]]:
    """Yield ``(phase_id, output)`` pairs from a FullPlan.

    Tries the (hypothetical) ``phase_outputs`` container first - it can be
    either a mapping or an iterable of models with a ``phase_id`` attribute -
    and falls back to walking the explicit named fields on ``FullPlan``.
    """
    container = getattr(full_plan, "phase_outputs", None)
    if isinstance(container, dict) and container:
        return [(str(k), v) for k, v in container.items()]
    if isinstance(container, (list, tuple)) and container:
        pairs: list[tuple[str, Any]] = []
        for idx, item in enumerate(container):
            phase_id = getattr(item, "phase_id", None) or f"phase_{idx}"
            pairs.append((str(phase_id), item))
        return pairs

    field_to_phase = [
        ("pressure_test", "phase_0"),
        ("problem_model_fit", "phase_1"),
        ("architecture", "phase_2"),
        ("build_buy_train", "phase_3"),
        ("infrastructure", "phase_4"),
        ("cost_model", "phase_5"),
        ("security", "phase_6_25"),
        ("observability", "phase_6_5"),
        ("scaling", "phase_7"),
    ]
    pairs = []
    for attr, phase_id in field_to_phase:
        value = getattr(full_plan, attr, None)
        if value is not None:
            pairs.append((phase_id, value))
    return pairs


# ---------------------------------------------------------------------------
# Cover + red team
# ---------------------------------------------------------------------------


def _cover_elements(full_plan: FullPlan, styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Title page: big title, plan title, generation timestamp, summary."""
    elements: list[Any] = [
        Spacer(1, 1.0 * inch),
        Paragraph("AI Build Plan", styles["h1"]),
    ]

    subtitle = (
        getattr(full_plan, "title", None)
        or getattr(full_plan, "idea", None)
        or getattr(full_plan, "plan_id", None)
        or "Untitled plan"
    )
    elements.append(Paragraph(_escape(subtitle), styles["h2"]))

    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    elements.append(Paragraph(f"Generated {generated}", styles["muted"]))
    elements.append(Spacer(1, 0.4 * inch))

    try:
        summary = getattr(full_plan, "idea_summary", None) or getattr(
            full_plan, "executive_summary", None
        )
    except Exception:
        summary = None
    if summary:
        elements.append(Paragraph("Summary", styles["h3"]))
        elements.append(Paragraph(_escape(summary), styles["body"]))

    next_steps = getattr(full_plan, "next_steps", None)
    if next_steps:
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("Next steps", styles["h3"]))
        elements.append(_render_value(list(next_steps), styles))

    elements.append(PageBreak())
    return elements


def _red_team_elements(critique: Any, styles: dict[str, ParagraphStyle]) -> list[Any]:
    """Render the red-team critique as its own page."""
    elements: list[Any] = [Paragraph("Red Team Critique", styles["h2"])]

    summary = getattr(critique, "summary", None)
    if summary:
        elements.append(Paragraph(_escape(summary), styles["body"]))
        elements.append(Spacer(1, 0.15 * inch))

    confidence = getattr(critique, "overall_confidence", None)
    if confidence:
        elements.append(
            Paragraph(f"<b>Overall confidence:</b> {_escape(confidence)}", styles["body"])
        )
        elements.append(Spacer(1, 0.15 * inch))

    findings = getattr(critique, "findings", None)
    if findings:
        elements.append(Paragraph("Findings", styles["h3"]))
        rendered: list[dict[str, Any]] = []
        for finding in findings:
            if hasattr(finding, "model_dump"):
                try:
                    rendered.append(finding.model_dump())
                    continue
                except Exception:
                    pass
            if isinstance(finding, dict):
                rendered.append(finding)
            else:
                rendered.append({"finding": str(finding)})
        elements.append(_render_value(rendered, styles))

    for label, attr in (
        ("Risks", "risks"),
        ("Blind spots", "blind_spots"),
        ("Missing prerequisites", "prerequisites_missing"),
    ):
        items = getattr(critique, attr, None)
        if items:
            elements.append(Spacer(1, 0.15 * inch))
            elements.append(Paragraph(label, styles["h3"]))
            elements.append(_render_value(list(items), styles))

    elements.append(PageBreak())
    return elements


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def render_plan_pdf(full_plan: FullPlan, red_team: RedTeamCritique | None = None) -> bytes:
    """Render ``full_plan`` (with optional explicit red-team) to PDF bytes.

    The returned ``bytes`` payload always starts with the ``%PDF`` magic
    header, suitable for serving directly as ``application/pdf``.
    """
    styles = _build_styles()
    elements: list[Any] = []

    elements.extend(_cover_elements(full_plan, styles))

    for phase_id, output in _iter_phase_outputs(full_plan):
        try:
            elements.extend(_phase_elements(phase_id, output, styles))
        except Exception as exc:  # pragma: no cover - defensive guard
            elements.append(Paragraph(_escape(_phase_title(phase_id)), styles["h2"]))
            elements.append(
                Paragraph(f"<i>Failed to render this phase: {_escape(exc)}</i>", styles["muted"])
            )
        elements.append(PageBreak())

    critique = red_team if red_team is not None else getattr(full_plan, "red_team", None)
    if critique is not None:
        try:
            elements.extend(_red_team_elements(critique, styles))
        except Exception as exc:  # pragma: no cover - defensive guard
            elements.append(Paragraph("Red Team Critique", styles["h2"]))
            elements.append(
                Paragraph(f"<i>Failed to render critique: {_escape(exc)}</i>", styles["muted"])
            )
            elements.append(PageBreak())

    if not elements:
        elements.append(Paragraph("AI Build Plan", styles["h1"]))
        elements.append(Paragraph("<i>No plan content was provided.</i>", styles["body"]))

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="AI Build Plan",
    )
    doc.build(elements)
    return buffer.getvalue()
