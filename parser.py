import markdown
import re
from pathlib import Path


def parse_content(meta : dict, content_html : str, template : str) -> str:
    pre_content : str = content_html
    content = content_html
    if template:
        matches_with_braces = re.findall(r"(\{\{.*?\}\})", template)
        matches = re.findall(r"\{\{(.*?)\}\}", template)
        for i in range(len(matches)):
            m : str = matches[i]
            token : str = m.strip()
            if token.startswith("page."):
                token = token[len("page."):]
                if token == "content":
                    content = template.replace(matches_with_braces[i], pre_content)

    matches_with_braces = re.findall(r"(\{\{.*?\}\})", content)
    matches = re.findall(r"\{\{(.*?)\}\}", content)
    for i in range(len(matches)):
        m : str = matches[i]
        token : str = m.strip()
        if token.startswith("page."):
            token = token[len("page."):]
            if token in meta:
                content = content.replace(matches_with_braces[i], meta[token][0])
    
    
    return content


class ParseMarkdown:
    def __init__(self, templates_path : str, md_file : Path):
        md : markdown.Markdown = markdown.Markdown(extensions=["meta"])
        content_md : str = md_file.read_text(encoding="utf-8")
        content_html : str = md.convert(content_md)

        # print(md.Meta)
        # parse_content(md.Meta, content_html, md.Meta["template"])
        self.meta : dict = md.Meta
        self.content_md : str = content_md
        # self.content_html : str = parse_content(md.Meta, content_html, md.Meta["template"])

        template_name = md.Meta.get("template", [""])[0]

        if template_name != "":
            template_path = Path(templates_path) / f"{template_name}.html"
            print(template_path)
            if template_path.exists():
                template_content = template_path.read_text(encoding="utf-8")
            else:
                template_content = ""
        else:
            template_content = ""


        self.content_html: str = parse_content(self.meta, content_html, template_content)
