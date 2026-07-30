import fitz
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def md_to_pdf(md_filename: str = "sample_physics_lesson.md", pdf_filename: str = "sample_physics_lesson.pdf"):
    md_path = BASE_DIR / md_filename
    pdf_path = BASE_DIR / pdf_filename

    md_text = md_path.read_text(encoding="utf-8")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ font-family: sans-serif; font-size: 11pt; line-height: 1.5; color: #1e293b; margin: 40px; }}
        h1 {{ color: #1e40af; font-size: 20pt; border-bottom: 2px solid #3b82f6; padding-bottom: 8px; margin-bottom: 20px; }}
        h2 {{ color: #1d4ed8; font-size: 15pt; margin-top: 24px; margin-bottom: 12px; border-bottom: 1px solid #e2e8f0; }}
        h3 {{ color: #2563eb; font-size: 12pt; margin-top: 16px; margin-bottom: 8px; }}
        p {{ margin-bottom: 10px; }}
        ul {{ margin-top: 4px; margin-bottom: 12px; padding-left: 20px; }}
        li {{ margin-bottom: 4px; }}
        hr {{ border: none; border-top: 1px solid #cbd5e1; margin: 20px 0; }}
        code {{ background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 10pt; }}
        strong {{ color: #0f172a; }}
    </style>
    </head>
    <body>
    """
    
    lines = md_text.splitlines()
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_content += "</ul>\n"
                in_list = False
            continue
            
        if stripped.startswith("# "):
            if in_list: html_content += "</ul>\n"; in_list = False
            html_content += f"<h1>{stripped[2:]}</h1>\n"
        elif stripped.startswith("## "):
            if in_list: html_content += "</ul>\n"; in_list = False
            html_content += f"<h2>{stripped[3:]}</h2>\n"
        elif stripped.startswith("### "):
            if in_list: html_content += "</ul>\n"; in_list = False
            html_content += f"<h3>{stripped[4:]}</h3>\n"
        elif stripped.startswith("---"):
            if in_list: html_content += "</ul>\n"; in_list = False
            html_content += "<hr/>\n"
        elif stripped.startswith("- ") or stripped.startswith("* "):
            if not in_list:
                html_content += "<ul>\n"
                in_list = True
            content = stripped[2:]
            while "**" in content:
                content = content.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            html_content += f"  <li>{content}</li>\n"
        elif stripped[0].isdigit() and len(stripped) > 2 and stripped[1:3] in (". ", ") "):
            if in_list: html_content += "</ul>\n"; in_list = False
            content = stripped[3:]
            while "**" in content:
                content = content.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            html_content += f"<p><strong>{stripped[:2]}</strong> {content}</p>\n"
        else:
            if in_list: html_content += "</ul>\n"; in_list = False
            content = stripped
            while "**" in content:
                content = content.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            html_content += f"<p>{content}</p>\n"
            
    if in_list:
        html_content += "</ul>\n"
        
    html_content += "</body></html>"
    
    story = fitz.Story(html=html_content)
    writer = fitz.DocumentWriter(str(pdf_path))
    
    rect = fitz.Rect(0, 0, 595, 842) # A4 page format
    where = fitz.Rect(36, 36, 559, 806)
    
    more = True
    while more:
        device = writer.begin_page(rect)
        more, _ = story.place(where)
        story.draw(device)
        writer.end_page()
        
    writer.close()
    print(f"Successfully created PDF at: {pdf_path}")

if __name__ == "__main__":
    md_to_pdf()
