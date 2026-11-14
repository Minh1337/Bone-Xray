"""Export a simple Markdown report to DOCX (headings, paragraphs, lists, tables, code, alerts).

Usage:
    .\\.venv\\Scripts\\python.exe -m tools.export_report_docx INPUT.md OUTPUT.docx
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Inches, Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)")
ALERT = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$")
ALERT_LABEL = {
    "NOTE": "Ghi chú", "TIP": "Gợi ý", "IMPORTANT": "Quan trọng",
    "WARNING": "Cảnh báo", "CAUTION": "Thận trọng",
}

NAVY = "263445"
TEAL = "126B76"
INK = "1F2933"
MUTED = "59636D"
PALE = "EEF5F7"
ROW_ALT = "F4F7FA"


def set_run_font(run, name="Arial", size=None, color=None, bold=None, italic=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_hyperlink(paragraph, label: str, url: str) -> None:
    relationship = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship)
    run = OxmlElement("w:r")
    properties = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), TEAL)
    properties.append(color)
    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    properties.append(underline)
    run.append(properties)
    text = OxmlElement("w:t")
    text.text = label
    run.append(text)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def shade_cell(cell, fill: str) -> None:
    properties = cell._tc.get_or_add_tcPr()
    shading = properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        properties.append(shading)
    shading.set(qn("w:fill"), fill)


def border_cell(cell) -> None:
    properties = cell._tc.get_or_add_tcPr()
    borders = properties.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        properties.append(borders)
    for side in ("top", "left", "bottom", "right"):
        edge = borders.find(qn(f"w:{side}"))
        if edge is None:
            edge = OxmlElement(f"w:{side}")
            borders.append(edge)
        for key, value in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
            edge.set(qn(f"w:{key}"), value)


def style_callout(paragraph, fill: str) -> None:
    properties = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)
    borders = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "24")
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), TEAL)
    borders.append(left)
    properties.append(borders)
    paragraph.paragraph_format.left_indent = Pt(8)
    paragraph.paragraph_format.right_indent = Pt(8)
    paragraph.paragraph_format.space_before = Pt(5)
    paragraph.paragraph_format.space_after = Pt(7)


def set_cell_margins(cell, top=90, start=105, bottom=90, end=105) -> None:
    properties = cell._tc.get_or_add_tcPr()
    margins = properties.first_child_found_in("w:tcMar")
    if margins is None:
        margins = OxmlElement("w:tcMar")
        properties.append(margins)
    for edge, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = margins.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            margins.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def repeat_header(row) -> None:
    properties = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    properties.append(header)


def prevent_row_split(row) -> None:
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def add_page_number(paragraph) -> None:
    for kind, value in (("begin", None), ("instrText", "PAGE"), ("end", None)):
        run = OxmlElement("w:r")
        if kind == "instrText":
            node = OxmlElement("w:instrText")
            node.set(qn("xml:space"), "preserve")
            node.text = value
        else:
            node = OxmlElement("w:fldChar")
            node.set(qn("w:fldCharType"), kind)
        run.append(node)
        paragraph._p.append(run)


def style_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.72)
    section.left_margin = Inches(0.78)
    section.right_margin = Inches(0.78)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12

    title = doc.styles["Title"]
    title.font.name = "Arial"
    title._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    title._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    title.font.size = Pt(26)
    title.font.bold = True
    title.font.color.rgb = RGBColor(0, 0, 0)
    title.paragraph_format.space_before = Pt(12)
    title.paragraph_format.space_after = Pt(9)
    title.paragraph_format.keep_with_next = True
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title_properties = title._element.get_or_add_pPr()
    title_borders = OxmlElement("w:pBdr")
    title_bottom = OxmlElement("w:bottom")
    title_bottom.set(qn("w:val"), "nil")
    title_borders.append(title_bottom)
    title_properties.append(title_borders)

    for style_name, size, before, after in (
        ("Heading 1", 16, 16, 7),
        ("Heading 2", 12.5, 11, 5),
        ("Heading 3", 11, 8, 3),
    ):
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(header.add_run("BONESCOPE  |  BÁO CÁO HỌC TẬP"), size=8, color="000000", bold=True)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(footer.add_run("BoneScope  ·  Trang "), size=8, color="000000")
    add_page_number(footer)

    doc.core_properties.title = "Báo cáo BoneScope"
    doc.core_properties.subject = "Tài liệu đồ án BoneScope"
    doc.core_properties.author = "BoneScope"


def add_inline(paragraph, text: str) -> None:
    text = text.replace("\\$", "$")
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, name="Consolas", size=9, color=NAVY)
        elif part.startswith("[") and "](" in part:
            end = part.index("](")
            label, target = part[1:end], part[end + 2:-1]
            if target.startswith(("https://", "http://", "mailto:")):
                add_hyperlink(paragraph, label, target)
            else:
                paragraph.add_run(label)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def convert(markdown: str) -> Document:
    doc = Document()
    style_document(doc)
    lines = markdown.splitlines()
    first_title = next((line[2:].strip() for line in lines if line.startswith("# ")), None)
    if first_title:
        doc.core_properties.title = first_title
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.strip() == "<!-- pagebreak -->":
            doc.add_page_break()
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i].rstrip())
                i += 1
            i += 1
            para = doc.add_paragraph()
            run = para.add_run("\n".join(code))
            set_run_font(run, name="Consolas", size=8.5, color=NAVY)
            properties = para._p.get_or_add_pPr()
            shading = OxmlElement("w:shd")
            shading.set(qn("w:fill"), "F2F5F8")
            properties.append(shading)
            para.paragraph_format.left_indent = Pt(8)
            para.paragraph_format.right_indent = Pt(8)
            para.paragraph_format.space_before = Pt(4)
            para.paragraph_format.space_after = Pt(7)
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            if level == 1 and not any(p.style.name == "Title" for p in doc.paragraphs):
                para = doc.add_paragraph(style="Title")
            else:
                para = doc.add_heading(level=min(level - 1, 3))
            add_inline(para, heading.group(2))
            i += 1
            continue
        if line.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i].lstrip(">").strip())
                i += 1
            label = None
            if block and ALERT.match(block[0]):
                label = ALERT_LABEL[ALERT.match(block[0]).group(1)]
                block = block[1:]
            para = doc.add_paragraph()
            style_callout(para, "FFF5E8" if label in {"Cảnh báo", "Thận trọng"} else PALE)
            if label:
                run = para.add_run(f"{label}: ")
                set_run_font(run, size=10, color="9A4C12", bold=True)
            add_inline(para, " ".join(b for b in block if b))
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = split_row(line)
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(split_row(lines[i]))
                i += 1
            table = doc.add_table(rows=1 + len(rows), cols=len(header))
            table.style = "Table Grid"
            table.autofit = True
            for r, cells in enumerate([header] + rows):
                prevent_row_split(table.rows[r])
                for c in range(len(header)):
                    cell = table.cell(r, c)
                    cell.text = ""
                    set_cell_margins(cell)
                    border_cell(cell)
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    if r == 0:
                        shade_cell(cell, NAVY)
                    elif r % 2 == 0:
                        shade_cell(cell, ROW_ALT)
                    add_inline(cell.paragraphs[0], cells[c] if c < len(cells) else "")
                    for run in cell.paragraphs[0].runs:
                        if r == 0:
                            set_run_font(run, size=8.8, color="FFFFFF", bold=True)
                        else:
                            set_run_font(run, size=8.8, color=INK)
                    cell.paragraphs[0].paragraph_format.space_after = Pt(1)
            repeat_header(table.rows[0])
            doc.add_paragraph()
            continue
        bullet = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        number = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if bullet or number:
            if bullet:
                para = doc.add_paragraph(style="List Bullet")
                add_inline(para, bullet.group(2))
            else:
                para = doc.add_paragraph()
                para.paragraph_format.left_indent = Pt(22)
                para.paragraph_format.first_line_indent = Pt(-18)
                para.add_run(f"{number.group(2)}. ")
                add_inline(para, number.group(3))
            para.paragraph_format.space_after = Pt(3)
            i += 1
            continue
        para_lines = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and lines[i].strip() != "<!-- pagebreak -->" and not re.match(r"^(#|>|\||```|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        add_inline(doc.add_paragraph(), " ".join(para_lines))
    return doc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    convert(args.input.read_text(encoding="utf-8")).save(args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
