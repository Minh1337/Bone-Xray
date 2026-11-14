from docx import Document

from tools.export_report_docx import convert


def test_convert_handles_headings_tables_lists_alerts_and_code():
    markdown = "\n".join([
        "# Title",
        "> [!IMPORTANT]",
        "> Keep `answer_ready=false`.",
        "## Section",
        "| A | B |",
        "| --- | ---: |",
        "| **x** | [link](file.md) |",
        "- item one",
        "1. step",
        "```powershell",
        "python -m pytest",
        "```",
        "Plain \\$1 text.",
        "<!-- pagebreak -->",
        "## References",
        "1. reference one",
    ])
    doc = convert(markdown)
    text = "\n".join(p.text for p in doc.paragraphs)
    assert "Title" in text and "Section" in text
    assert "Quan trọng: Keep answer_ready=false." in text
    assert "python -m pytest" in text
    assert "Plain $1 text." in text
    assert "1. step" in text and "1. reference one" in text
    assert 'w:type="page"' in doc._element.xml
    assert len(doc.tables) == 1
    assert doc.tables[0].cell(1, 0).text == "x"
    assert doc.tables[0].cell(1, 1).text == "link"


def test_export_writes_readable_docx(tmp_path):
    from tools.export_report_docx import main

    source = tmp_path / "r.md"
    source.write_text("# Báo cáo\n\nNội dung.", encoding="utf-8")
    target = tmp_path / "r.docx"
    assert main([str(source), str(target)]) == 0
    assert "Báo cáo" in Document(target).paragraphs[0].text
    assert Document(target).core_properties.title == "Báo cáo"
