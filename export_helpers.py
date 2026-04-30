# export_helpers.py

import csv
import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from db_layer import get_hearing_metadata, get_events_for_hearing


# ------------------------------------------------------------
# Build text version (used for TXT and combined exports)
# ------------------------------------------------------------
def build_hearing_text(hearing_id, duration_str=None):
    meta = get_hearing_metadata(hearing_id)
    events = get_events_for_hearing(hearing_id)

    if not meta:
        return "No data for this hearing."

    (
        h_id,
        created_at,
        date,
        case_number,
        case_type,
        judge,
        hearing_type,
        num_parties,
        num_pro_se,
        notes,
    ) = meta

    lines = []
    lines.append(f"Hearing ID: {h_id}")
    lines.append(f"Created At: {created_at}")
    lines.append(f"Date: {date}")
    lines.append(f"Case Number: {case_number or ''}")
    lines.append(f"Case Type: {case_type or ''}")
    lines.append(f"Judge: {judge or ''}")
    lines.append(f"Hearing Type: {hearing_type or ''}")
    lines.append(f"Number of Parties: {num_parties}")
    lines.append(f"Number of Pro Se: {num_pro_se}")
    if duration_str:
        lines.append(f"Duration: {duration_str}")
    lines.append("")
    lines.append("NOTES:")
    lines.append(notes or "")
    lines.append("")
    lines.append("EVENTS:")
    if not events:
        lines.append("(No events logged.)")
    else:
        for ts, cat, subcat, detail, tag in events:
            parts = [ts, cat]
            if subcat:
                parts.append(subcat)
            if detail:
                parts.append(detail)
            if tag:
                parts.append(f"[{tag}]")
            lines.append(" | ".join(parts))

    return "\n".join(lines)


# ------------------------------------------------------------
# Export TXT + PDF + CSV for a single hearing
# ------------------------------------------------------------
def export_hearing_txt_pdf_csv(hearing_id, base_path, duration_str=None):
    text_content = build_hearing_text(hearing_id, duration_str=duration_str)

    txt_path = base_path + ".txt"
    pdf_path = base_path + ".pdf"
    csv_path = base_path + ".csv"

    # TXT
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text_content)

    # PDF (Courier New, header, page numbers, wrapping)
    try:
        pdfmetrics.registerFont(TTFont("CourierNew", "cour.ttf"))
        font_name = "CourierNew"
    except:
        font_name = "Courier"

    styles = getSampleStyleSheet()

    base_style = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    label_style = ParagraphStyle(
        "Label",
        parent=base_style,
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
    )

    indented_style = ParagraphStyle(
        "Indented",
        parent=base_style,
        leftIndent=20,
    )

    detail_style = ParagraphStyle(
        "DetailIndented",
        parent=base_style,
        leftIndent=40,
    )

    meta = get_hearing_metadata(hearing_id)
    (
        h_id,
        created_at,
        date,
        case_number,
        case_type,
        judge,
        hearing_type,
        num_parties,
        num_pro_se,
        notes,
    ) = meta

    events = get_events_for_hearing(hearing_id)

    header_text = f"Case: {case_number or 'N/A'} | Judge: {judge or 'N/A'}"

    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 10)
        canvas.drawString(72, LETTER[1] - 50, header_text)
        page_num = canvas.getPageNumber()
        canvas.drawString(LETTER[0] - 100, 40, f"Page {page_num}")
        canvas.restoreState()

    story = []

    story.append(Paragraph("<b>Hearing Metadata</b>", label_style))
    story.append(Paragraph(f"<b>Date:</b> {date}", indented_style))
    story.append(Paragraph(f"<b>Case Number:</b> {case_number or ''}", indented_style))
    story.append(Paragraph(f"<b>Case Type:</b> {case_type or ''}", indented_style))
    story.append(Paragraph(f"<b>Judge:</b> {judge or ''}", indented_style))
    story.append(Paragraph(f"<b>Hearing Type:</b> {hearing_type or ''}", indented_style))
    story.append(Paragraph(f"<b>Number of Parties:</b> {num_parties}", indented_style))
    story.append(Paragraph(f"<b>Number of Pro Se:</b> {num_pro_se}", indented_style))
    if duration_str:
        story.append(Paragraph(f"<b>Duration:</b> {duration_str}", indented_style))

    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Notes</b>", label_style))
    for line in (notes or "").splitlines():
        story.append(Paragraph(line.replace(" ", "&nbsp;"), indented_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Events</b>", label_style))
    if not events:
        story.append(Paragraph("(No events logged.)", indented_style))
    else:
        for ts, cat, subcat, detail, tag in events:
            line = f"<b>{ts}</b> — {cat}"
            if subcat:
                line += f" / {subcat}"
            if tag:
                line += f" <i>[{tag}]</i>"
            story.append(Paragraph(line, indented_style))
            if detail:
                story.append(
                    Paragraph(
                        detail.replace(" ", "&nbsp;"),
                        detail_style,
                    )
                )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=LETTER,
        leftMargin=72,
        rightMargin=72,
        topMargin=90,
        bottomMargin=72,
    )

    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    # CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["HEARING_METADATA"])
        writer.writerow(["hearing_id", h_id])
        writer.writerow(["created_at", created_at])
        writer.writerow(["date", date])
        writer.writerow(["case_number", case_number])
        writer.writerow(["case_type", case_type])
        writer.writerow(["judge", judge])
        writer.writerow(["hearing_type", hearing_type])
        writer.writerow(["num_parties", num_parties])
        writer.writerow(["num_pro_se", num_pro_se])
        writer.writerow(["duration", duration_str or ""])
        writer.writerow(["notes", notes])
        writer.writerow([])

        writer.writerow(["EVENTS"])
        writer.writerow(["hearing_id", "timestamp", "category", "subcategory", "detail", "tag"])
        for ts, cat, subcat, detail, tag in events:
            writer.writerow([h_id, ts, cat, subcat, detail, tag])

    return txt_path, pdf_path, csv_path


# ------------------------------------------------------------
# Export combined TXT + PDF + CSV for a docket (multiple hearings)
# ------------------------------------------------------------
def export_docket_batch(base_path, hearing_ids):
    txt_path = base_path + ".txt"
    pdf_path = base_path + ".pdf"
    csv_path = base_path + ".csv"

    # TXT: concatenate hearings
    combined_lines = []
    for hid in hearing_ids:
        combined_lines.append(f"=== HEARING {hid} ===")
        combined_lines.append(build_hearing_text(hid))
        combined_lines.append("")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(combined_lines))

    # PDF: multiple hearings, page breaks between
    try:
        pdfmetrics.registerFont(TTFont("CourierNew", "cour.ttf"))
        font_name = "CourierNew"
    except:
        font_name = "Courier"

    styles = getSampleStyleSheet()

    base_style = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )

    label_style = ParagraphStyle(
        "Label",
        parent=base_style,
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
    )

    indented_style = ParagraphStyle(
        "Indented",
        parent=base_style,
        leftIndent=20,
    )

    detail_style = ParagraphStyle(
        "DetailIndented",
        parent=base_style,
        leftIndent=40,
    )

    def add_header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont(font_name, 10)
        canvas.drawString(72, LETTER[1] - 50, "Docket Summary")
        page_num = canvas.getPageNumber()
        canvas.drawString(LETTER[0] - 100, 40, f"Page {page_num}")
        canvas.restoreState()

    story = []

    first = True
    for hid in hearing_ids:
        meta = get_hearing_metadata(hid)
        if not meta:
            continue

        (
            h_id,
            created_at,
            date,
            case_number,
            case_type,
            judge,
            hearing_type,
            num_parties,
            num_pro_se,
            notes,
        ) = meta

        events = get_events_for_hearing(hid)

        if not first:
            story.append(PageBreak())
        first = False

        story.append(Paragraph(f"<b>Hearing {h_id}</b>", label_style))
        story.append(Paragraph(f"<b>Date:</b> {date}", indented_style))
        story.append(Paragraph(f"<b>Case Number:</b> {case_number or ''}", indented_style))
        story.append(Paragraph(f"<b>Case Type:</b> {case_type or ''}", indented_style))
        story.append(Paragraph(f"<b>Judge:</b> {judge or ''}", indented_style))
        story.append(Paragraph(f"<b>Hearing Type:</b> {hearing_type or ''}", indented_style))
        story.append(Paragraph(f"<b>Number of Parties:</b> {num_parties}", indented_style))
        story.append(Paragraph(f"<b>Number of Pro Se:</b> {num_pro_se}", indented_style))
        story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Notes</b>", label_style))
        for line in (notes or "").splitlines():
            story.append(Paragraph(line.replace(" ", "&nbsp;"), indented_style))
        story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Events</b>", label_style))
        if not events:
            story.append(Paragraph("(No events logged.)", indented_style))
        else:
            for ts, cat, subcat, detail, tag in events:
                line = f"<b>{ts}</b> — {cat}"
                if subcat:
                    line += f" / {subcat}"
                if tag:
                    line += f" <i>[{tag}]</i>"
                story.append(Paragraph(line, indented_style))
                if detail:
                    story.append(
                        Paragraph(
                            detail.replace(" ", "&nbsp;"),
                            detail_style,
                        )
                    )

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=LETTER,
        leftMargin=72,
        rightMargin=72,
        topMargin=90,
        bottomMargin=72,
    )
    doc.build(story, onFirstPage=add_header_footer, onLaterPages=add_header_footer)

    # CSV: all hearings + events
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow(["HEARING_METADATA_AND_EVENTS"])
        writer.writerow(
            [
                "hearing_id",
                "created_at",
                "date",
                "case_number",
                "case_type",
                "judge",
                "hearing_type",
                "num_parties",
                "num_pro_se",
                "notes",
                "event_timestamp",
                "event_category",
                "event_subcategory",
                "event_detail",
                "event_tag",
            ]
        )

        for hid in hearing_ids:
            meta = get_hearing_metadata(hid)
            if not meta:
                continue

            (
                h_id,
                created_at,
                date,
                case_number,
                case_type,
                judge,
                hearing_type,
                num_parties,
                num_pro_se,
                notes,
            ) = meta

            events = get_events_for_hearing(hid)
            if not events:
                writer.writerow(
                    [
                        h_id,
                        created_at,
                        date,
                        case_number,
                        case_type,
                        judge,
                        hearing_type,
                        num_parties,
                        num_pro_se,
                        notes,
                        "",
                        "",
                        "",
                        "",
                        "",
                    ]
                )
            else:
                for ts, cat, subcat, detail, tag in events:
                    writer.writerow(
                        [
                            h_id,
                            created_at,
                            date,
                            case_number,
                            case_type,
                            judge,
                            hearing_type,
                            num_parties,
                            num_pro_se,
                            notes,
                            ts,
                            cat,
                            subcat,
                            detail,
                            tag,
                        ]
                    )

    return txt_path, pdf_path, csv_path