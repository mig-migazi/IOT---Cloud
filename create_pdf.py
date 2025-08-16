#!/usr/bin/env python3
"""
Convert markdown to PDF using WeasyPrint
"""

import markdown2
import weasyprint
import os
from pathlib import Path

def markdown_to_pdf(markdown_file, output_pdf):
    """Convert markdown file to PDF with custom styling"""
    
    # Read markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown2.markdown(
        markdown_content,
        extras=['tables', 'fenced-code-blocks', 'code-friendly', 'cuddled-lists']
    )
    
    # Add custom CSS styling
    css_styles = """
    <style>
        @page {
            size: A4;
            margin: 1in;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
            margin: 0;
            padding: 0;
        }
        
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
            page-break-after: avoid;
        }
        
        h2 {
            color: #34495e;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
            margin-top: 25px;
            page-break-after: avoid;
        }
        
        h3 {
            color: #7f8c8d;
            margin-top: 20px;
            page-break-after: avoid;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            overflow-x: auto;
            page-break-inside: avoid;
        }
        
        pre code {
            background-color: transparent;
            padding: 0;
        }
        
        blockquote {
            border-left: 4px solid #3498db;
            margin: 0;
            padding-left: 15px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        .highlight {
            background-color: #fff3cd;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
        }
        
        .success {
            background-color: #d4edda;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #28a745;
        }
        
        .warning {
            background-color: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            border-left: 4px solid #dc3545;
        }
        
        .architecture-diagram {
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
            page-break-inside: avoid;
        }
        
        .architecture-diagram pre {
            background-color: transparent;
            border: none;
            font-family: 'Courier New', monospace;
            font-size: 0.8em;
            line-height: 1.2;
        }
        
        .toc {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        
        .toc li {
            margin: 5px 0;
        }
        
        .toc a {
            text-decoration: none;
            color: #3498db;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        /* Ensure proper page breaks */
        h1, h2, h3 {
            page-break-after: avoid;
        }
        
        pre, table, .architecture-diagram {
            page-break-inside: avoid;
        }
        
        /* Add some spacing for better readability */
        p {
            margin-bottom: 1em;
        }
        
        ul, ol {
            margin-bottom: 1em;
        }
        
        li {
            margin-bottom: 0.5em;
        }
    </style>
    """
    
    # Create full HTML document
    html_document = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>IoT Cloud Project - Architecture & Implementation Guide</title>
        {css_styles}
    </head>
    <body>
        {html_content}
        <div class="footer">
            <p>Generated from IoT Cloud Project documentation</p>
            <p>Document created on: August 15, 2025</p>
        </div>
    </body>
    </html>
    """
    
    # Write HTML to temporary file
    temp_html = 'temp_document.html'
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_document)
    
    try:
        # Convert HTML to PDF using WeasyPrint
        print("🔄 Converting HTML to PDF...")
        weasyprint.HTML(string=html_document).write_pdf(output_pdf)
        print(f"✅ Successfully created PDF: {output_pdf}")
        
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        print("The HTML file has been created and can be opened in a browser.")
        
    finally:
        # Clean up temporary HTML file
        if os.path.exists(temp_html):
            os.remove(temp_html)

if __name__ == "__main__":
    markdown_file = "IOT-Cloud-Architecture.md"
    output_pdf = "IOT-Cloud-Architecture.pdf"
    
    if not os.path.exists(markdown_file):
        print(f"❌ Markdown file not found: {markdown_file}")
        exit(1)
    
    print(f"📖 Converting {markdown_file} to PDF...")
    markdown_to_pdf(markdown_file, output_pdf)
    
    if os.path.exists(output_pdf):
        print(f"🎉 PDF created successfully: {output_pdf}")
        print(f"📁 File size: {os.path.getsize(output_pdf)} bytes")
        print(f"📂 Location: {os.path.abspath(output_pdf)}")
    else:
        print("⚠️  PDF creation failed")
        print("You can open the HTML file in a browser and print to PDF manually")

