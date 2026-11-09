"""Export a simple Markdown report to DOCX (headings, paragraphs, lists, tables, code, alerts).

Usage:
    .\\.venv\\Scripts\\python.exe -m tools.export_report_docx INPUT.md OUTPUT.docx
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

INLINE = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*]+\*)")
ALERT = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$")
ALERT_LABEL = {
    "NOTE": "Ghi chú", "TIP": "Gợi ý", "IMPORTANT": "Quan trọng",
    "WARNING": "Cảnh báo", "CAUTION": "Thận trọng",
}


def add_inline(paragraph, text: str) -> None:
    text = text.replace("\\$", "$")
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9.5)
        elif part.startswith("[") and "](" in part:
            paragraph.add_run(part[1:part.index("](")])
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            paragraph.add_run(part[1:-1]).italic = True
        else:
            paragraph.add_run(part)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def convert(markdown: str) -> Document:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    lines = markdown.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
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
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            continue
        heading = re.match(r"^(#{1,4})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            para = doc.add_heading(level=0 if level == 1 else level - 1)
            add_inline(para, heading.group(2))
            if level == 1:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
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
            if label:
                run = para.add_run(f"{label}: ")
                run.bold = True
                run.font.color.rgb = RGBColor(0xA0, 0x30, 0x00)
            add_inline(para, " ".join(b for b in block if b))
            para.paragraph_format.left_indent = Pt(18)
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
            for r, cells in enumerate([header] + rows):
                for c in range(len(header)):
                    cell = table.cell(r, c)
                    cell.text = ""
                    add_inline(cell.paragraphs[0], cells[c] if c < len(cells) else "")
                    for run in cell.paragraphs[0].runs:
                        run.font.size = Pt(10)
                        if r == 0:
                            run.bold = True
            doc.add_paragraph()
            continue
        bullet = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        number = re.match(r"^(\s*)\d+\.\s+(.*)$", line)
        if bullet or number:
            match = bullet or number
            para = doc.add_paragraph(style="List Bullet" if bullet else "List Number")
            add_inline(para, match.group(2))
            i += 1
            continue
        para_lines = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|\||```|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
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
