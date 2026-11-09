"""
scripts/generate_html_report.py - Converts the academic Markdown project report into a print-ready HTML report.
"""

import os
import re

def markdown_to_html(md_text: str) -> str:
    """Basic parser to convert GitHub-flavored markdown to clean, styled HTML."""
    html = md_text

    # Escape HTML special chars inside code blocks first
    code_blocks = []
    def save_code_block(match):
        code_blocks.append(match.group(1))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"

    html = re.sub(r'```[a-zA-Z0-9_-]*\n(.*?)```', save_code_block, html, flags=re.DOTALL)

    # Headers
    html = re.sub(r'^# (.*?)$', r'<h1 class="report-title">\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.*?)$', r'<h2 class="section-title">\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.*?)$', r'<h3 class="subsection-title">\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^#### (.*?)$', r'<h4 class="subsubsection-title">\1</h4>', html, flags=re.MULTILINE)

    # Bold and Italic
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html)

    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

    # Horizontal rules
    html = re.sub(r'^---$', r'<hr class="divider" />', html, flags=re.MULTILINE)

    # Unordered Lists
    lines = html.split('\n')
    in_list = False
    processed_lines = []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                processed_lines.append('<ul class="report-list">')
                in_list = True
            content = line.strip()[2:]
            processed_lines.append(f'<li>{content}</li>')
        else:
            if in_list:
                processed_lines.append('</ul>')
                in_list = False
            processed_lines.append(line)
    if in_list:
        processed_lines.append('</ul>')
    html = '\n'.join(processed_lines)

    # Tables
    def parse_table(match):
        table_raw = match.group(0).strip()
        rows = [r.strip() for r in table_raw.split('\n') if r.strip()]
        if len(rows) < 2:
            return table_raw
        
        header_cells = [c.strip() for c in rows[0].split('|') if c.strip()]
        tbody_rows = rows[2:] # skip separator

        table_html = ['<div class="table-container"><table class="report-table">', '<thead><tr>']
        for h in header_cells:
            table_html.append(f'<th>{h}</th>')
        table_html.append('</tr></thead><tbody>')

        for r in tbody_rows:
            cells = [c.strip() for c in r.split('|') if c.strip()]
            if cells:
                table_html.append('<tr>')
                for c in cells:
                    table_html.append(f'<td>{c}</td>')
                table_html.append('</tr>')
        table_html.append('</tbody></table></div>')
        return '\n'.join(table_html)

    html = re.sub(r'(\|.+?\|\n\|[-:| ]+\|\n(?:\|.+?\|\n?)+)', parse_table, html)

    # Paragraphs
    paragraphs = html.split('\n\n')
    formatted_p = []
    for p in paragraphs:
        p_str = p.strip()
        if p_str and not p_str.startswith('<h') and not p_str.startswith('<ul') and not p_str.startswith('<div') and not p_str.startswith('<hr'):
            formatted_p.append(f'<p class="report-para">{p_str}</p>')
        else:
            formatted_p.append(p_str)
    html = '\n\n'.join(formatted_p)

    # Restore code blocks
    for i, code in enumerate(code_blocks):
        escaped_code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html = html.replace(f"__CODE_BLOCK_{i}__", f'<pre class="code-block"><code>{escaped_code}</code></pre>')

    return html

def build_html_report():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, "docs", "project_report.md")
    out_path = os.path.join(base_dir, "docs", "project_report.html")

    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        return

    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    body_html = markdown_to_html(md_content)

    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Academic Project Report - Software Defect Management and Prediction System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Open+Sans:wght@400;600;700&display=swap');
        
        body {{
            font-family: 'Open Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.75;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 40px 20px;
        }}
        .report-wrapper {{
            max-width: 900px;
            margin: 0 auto;
            background: #ffffff;
            padding: 60px 80px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        }}
        .report-title {{
            font-family: 'Merriweather', serif;
            font-size: 2.2rem;
            color: #0f172a;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 12px;
            margin-top: 20px;
            text-align: center;
        }}
        .section-title {{
            font-family: 'Merriweather', serif;
            font-size: 1.45rem;
            color: #1e3a8a;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 8px;
            margin-top: 45px;
        }}
        .subsection-title {{
            font-size: 1.15rem;
            color: #1e293b;
            margin-top: 25px;
        }}
        .report-para {{
            font-size: 1rem;
            color: #334155;
            margin-bottom: 18px;
            text-align: justify;
        }}
        .divider {{
            border: 0;
            height: 1px;
            background: #cbd5e1;
            margin: 40px 0;
        }}
        .report-list {{
            margin-bottom: 20px;
            padding-left: 28px;
            color: #334155;
        }}
        .report-list li {{
            margin-bottom: 8px;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 25px 0;
        }}
        .report-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.92rem;
        }}
        .report-table th, .report-table td {{
            padding: 10px 14px;
            border: 1px solid #cbd5e1;
            text-align: left;
        }}
        .report-table th {{
            background-color: #f1f5f9;
            font-weight: 600;
            color: #0f172a;
        }}
        .report-table tr:nth-child(even) {{
            background-color: #f8fafc;
        }}
        .code-block {{
            background: #0f172a;
            color: #f8fafc;
            padding: 16px 20px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.88rem;
            font-family: Consolas, Monaco, "Courier New", monospace;
        }}
        code {{
            background: #f1f5f9;
            color: #be185d;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.9em;
            font-family: Consolas, Monaco, "Courier New", monospace;
        }}
        pre code {{
            background: transparent;
            color: inherit;
            padding: 0;
        }}
        @media print {{
            body {{
                background: #ffffff;
                padding: 0;
            }}
            .report-wrapper {{
                box-shadow: none;
                padding: 0;
                max-width: 100%;
            }}
            .section-title {{
                page-break-before: auto;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-wrapper">
        {body_html}
    </div>
</body>
</html>
"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"HTML Academic Project Report generated successfully: {out_path}")

if __name__ == "__main__":
    build_html_report()

