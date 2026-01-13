import re
from src.parser import ParseMarkdown
from pathlib import Path
from datetime import date, datetime

def summarize(text: str, limit: int = 30) -> str:
    words = text.split()
    if len(words) <= limit:
        return " ".join(words) + "."
    else:
        return " ".join(words[:limit]) + "..."

class Page:
    def __init__(self, md_file : Path):
        self.parse_fields(md_file)

    def parse_fields(self, md_file : Path):
        parse : ParseMarkdown = ParseMarkdown(md_file)

        content     = parse.content_html                                                # html content, cannot be set by the user
        title       = parse.meta.get("title", [md_file.parent.stem])[0]                 # defaults to parent folder name
        author      = parse.meta.get("author", [""])[0]                                 # defaults to config field
        _date       = parse.meta.get("date", [date.today().strftime("%d/%m/%Y")])[0]    # defaults to date of creation
        template    = parse.meta.get("template", [""])[0]                               # template file name (not full path), defaults to nothing
        section     = parse.meta.get("section", [md_file.parent.parent.stem])[0]        # defaults to parent's parent folder
        summary     = summarize(parse.content_html)                                     # defaults to 30 words
        tags        = parse.meta.get("tags", [])                                        # unique list field

        formats = ["%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y"]  # common slash formats
        for fmt in formats:
            try:
                date_obj = datetime.strptime(_date, fmt)
                _dateB = date_obj.strftime("%B %d, %Y")
                break
            except ValueError:
                continue
        else:
            # fallback if no format matches
            date_obj = date.today()
            _dateB = date_obj.strftime("%B %d, %Y")

        fields = {
            "content"   : content,
            "title"     : title,
            "author"    : author,
            "date"      : _date,
            "dateB"     : _dateB,
            "template"  : template,
            "section"   : section,
            "summary"   : summary,
            "tags"      : tags,
            # "url"       : parse.meta.get("url", ""),
        }

        self.__fields = fields
    
    def get_field(self, key : str) -> list | None:
        if not key in self.__fields:
            return None
        return self.__fields[key]
    
    def has_field(self, key : str) -> bool:
        return key in self.__fields
    

    def render(self, template_content : str = "") -> str:
        pre_content : str = self.get_field("content")

        # apply template
        content :str = pre_content
        if template_content:
            matches_with_braces = re.findall(r"(\{\{.*?\}\})", template_content)
            matches = re.findall(r"\{\{(.*?)\}\}", template_content)
            for i in range(len(matches)):
                m : str = matches[i]
                token : str = m.strip()
                if token.startswith("page."):
                    token = token[len("page."):]
                    if token == "content":
                        content = template_content.replace(matches_with_braces[i], pre_content)

        # replace placeholders with front matter fields
        matches_with_braces = re.findall(r"(\{\{.*?\}\})", content)
        matches = re.findall(r"\{\{(.*?)\}\}", content)
        for i in range(len(matches)):
            m : str = matches[i]
            token : str = m.strip()
            if token.startswith("page."):
                token = token[len("page."):]
                if self.has_field(token):
                    content = content.replace(matches_with_braces[i], str(self.get_field(token)))
            # # TODO
            # if token.startswith("tag."):
        
        return content
