"""
create_docx_report.py — Generates a formal academic Word (.docx) report
using pure Python standard library (zipfile + XML). Zero external dependencies.
"""
import io
import re
import zipfile
from pathlib import Path


def create_academic_docx(output_path: str | Path, markdown_path: str | Path):
    md_text = Path(markdown_path).read_text(encoding="utf-8")
    lines = md_text.splitlines()

    # Minimal DOCX XML structure
    document_xml = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">',
        '  <w:body>',
    ]

    in_table = False
    table_rows = []

    def flush_table():
        nonlocal in_table, table_rows
        if not table_rows:
            in_table = False
            return
        document_xml.append('    <w:tbl>')
        document_xml.append('      <w:tblPr>')
        document_xml.append('        <w:tblW w:w="5000" w:type="pct"/>')
        document_xml.append('        <w:tblBorders>')
        for border in ["top", "left", "bottom", "right", "insideH", "insideV"]:
            document_xml.append(f'          <w:{border} w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>')
        document_xml.append('        </w:tblBorders>')
        document_xml.append('      </w:tblPr>')

        for row_idx, row in enumerate(table_rows):
            is_header = (row_idx == 0)
            document_xml.append('      <w:tr>')
            for cell in row:
                document_xml.append('        <w:tc>')
                document_xml.append('          <w:tcPr>')
                if is_header:
                    document_xml.append('            <w:shd w:val="clear" w:color="auto" w:fill="F1F5F9"/>')
                document_xml.append('          </w:tcPr>')
                document_xml.append('          <w:p>')
                document_xml.append('            <w:r>')
                if is_header:
                    document_xml.append('              <w:rPr><w:b/><w:sz w:val="20"/></w:rPr>')
                else:
                    document_xml.append('              <w:rPr><w:sz w:val="20"/></w:rPr>')
                cell_escaped = cell.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                document_xml.append(f'              <w:t>{cell_escaped}</w:t>')
                document_xml.append('            </w:r>')
                document_xml.append('          </w:p>')
                document_xml.append('        </w:tc>')
            document_xml.append('      </w:tr>')

        document_xml.append('    </w:tbl>')
        document_xml.append('    <w:p/>')
        in_table = False
        table_rows = []

    for line in lines:
        stripped = line.strip()

        # Handle tables
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            # Skip delimiter line like |:---|---|
            if all(re.match(r'^:?-+:?$', c) for c in cells if c):
                continue
            in_table = True
            table_rows.append(cells)
            continue
        elif in_table:
            flush_table()

        if not stripped:
            continue

        # Headings
        if stripped.startswith("# "):
            h_text = stripped[2:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            document_xml.append('    <w:p>')
            document_xml.append('      <w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="120"/></w:pPr>')
            document_xml.append('      <w:r><w:rPr><w:b/><w:color w:val="1E3A8A"/><w:sz w:val="36"/></w:rPr>')
            document_xml.append(f'        <w:t>{h_text}</w:t>')
            document_xml.append('      </w:r>')
            document_xml.append('    </w:p>')
        elif stripped.startswith("## "):
            h_text = stripped[3:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            document_xml.append('    <w:p>')
            document_xml.append('      <w:pPr><w:jc w:val="center"/><w:spacing w:before="180" w:after="80"/></w:pPr>')
            document_xml.append('      <w:r><w:rPr><w:b/><w:color w:val="1E293B"/><w:sz w:val="28"/></w:rPr>')
            document_xml.append(f'        <w:t>{h_text}</w:t>')
            document_xml.append('      </w:r>')
            document_xml.append('    </w:p>')
        elif stripped.startswith("### "):
            h_text = stripped[4:].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            document_xml.append('    <w:p>')
            document_xml.append('      <w:pPr><w:spacing w:before="140" w:after="60"/></w:pPr>')
            document_xml.append('      <w:r><w:rPr><w:b/><w:color w:val="2563EB"/><w:sz w:val="24"/></w:rPr>')
            document_xml.append(f'        <w:t>{h_text}</w:t>')
            document_xml.append('      </w:r>')
            document_xml.append('    </w:p>')
        elif stripped.startswith("---"):
            document_xml.append('    <w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr></w:pPr></w:p>')
        else:
            # Paragraph
            # Clean basic bold markdown **...**
            p_text = stripped
            p_text = p_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            document_xml.append('    <w:p>')
            document_xml.append('      <w:pPr><w:spacing w:after="100"/></w:pPr>')
            
            # Simple bold handler
            parts = re.split(r'(\*\*.*?\*\*)', p_text)
            for part in parts:
                if part.startswith('**') and part.endswith('**'):
                    clean_bold = part[2:-2]
                    document_xml.append('      <w:r><w:rPr><w:b/><w:sz w:val="22"/></w:rPr>')
                    document_xml.append(f'        <w:t>{clean_bold}</w:t>')
                    document_xml.append('      </w:r>')
                else:
                    document_xml.append('      <w:r><w:rPr><w:sz w:val="22"/></w:rPr>')
                    document_xml.append(f'        <w:t xml:space="preserve">{part}</w:t>')
                    document_xml.append('      </w:r>')
            document_xml.append('    </w:p>')

    if in_table:
        flush_table()

    document_xml.append('    <w:sectPr>')
    document_xml.append('      <w:pgSz w:w="12240" w:h="15840"/>')  # Letter size in twips
    document_xml.append('      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>')  # 1-inch margins
    document_xml.append('    </w:sectPr>')
    document_xml.append('  </w:body>')
    document_xml.append('</w:document>')

    # Standard OpenXML boilerplate
    content_types_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''

    rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

    doc_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'''

    with zipfile.ZipFile(str(output_path), 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', content_types_xml)
        zf.writestr('_rels/.rels', rels_xml)
        zf.writestr('word/_rels/document.xml.rels', doc_rels_xml)
        zf.writestr('word/document.xml', '\n'.join(document_xml))

    print(f"Successfully generated Word document: {output_path}")


if __name__ == "__main__":
    create_academic_docx("PROJECT_REPORT_STUDYVERSE.docx", "PROJECT_REPORT.md")

