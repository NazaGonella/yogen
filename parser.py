import markdown
import re
from pathlib import Path

class ParseMarkdown:
    def __init__(self, md_file : Path):
        md : markdown.Markdown = markdown.Markdown(extensions=["meta"])
        content_md : str = md_file.read_text(encoding="utf-8")
        content_html : str = md.convert(content_md)
        print(md.Meta)

        self.content_md : str = content_md
        self.content_html : str = content_html

def apply_template(template : str):
    pass

def get_symbols(content_html : Path):
    pass