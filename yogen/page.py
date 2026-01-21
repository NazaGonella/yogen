import tomllib
import markdown
import re
from pathlib import Path
from datetime import date, datetime

class Page():
    def __init__(self, md_file: Path):
        self.file = md_file
        self.__fields = {
            "title" : md_file.parent.stem,
            "author" : "",
            "date" : {
                # "A" : date.today(),
                "A" : date.today().isoformat(),             # ISO
                "B" : date.today().strftime("%d/%m/%Y"),    # numeric
                "C" : date.today().strftime("%d/%m/%y"),    # numeric
                "D" : date.today().strftime("%m/%d/%Y"),    # numeric
                "E" : date.today().strftime("%m/%d/%y"),    # numeric
                "F" : date.today().strftime("%B %d, %Y"),   # display
            },
            "template" : "",
            "section" : md_file.parent.parent.stem,
            "tags" : []
        }
        meta, self.raw_html = self._parse_page()
        protected = {"content", "raw"}      # fields users cannot set
        for k, v in meta.items():
            if k == "date":
                self.__fields[k] = self._parse_date(v)
            elif k not in protected:
                self.__fields[k] = v
    
    def __hash__(self):
        return hash(self.file)
    
    def __eq__(self, other):
        if not isinstance(other, Page):
            return NotImplemented
        return self.file == other.file
    
    def get_field(self, key : str) -> object | None:
        if not key in self.__fields:
            return None
        return self.__fields[key]

    def has_field(self, key : str) -> bool:
        return key in self.__fields

    def render(self, templates : dict[str, str]) -> str:
        pre_content : str = self.get_field("content")
        template_content : str = templates.get(self.get_field("template"), "")

        # apply template
        content : str = pre_content
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

    
    def _parse_date(self, value) -> dict[str, date]:
        # allow multiple common formats
        date_obj : dict[str, date] = {}
        # formats = ["%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]
        formats = ["%Y-%m-%d"]  # enforce ISO format
        for fmt in formats:
            try:
                d = datetime.strptime(value, fmt).date()
                # date_obj["A"] = d
                date_obj["A"] = d.isoformat()
                date_obj["B"] = d.strftime("%d/%m/%Y")
                date_obj["C"] = d.strftime("%d/%m/%y")
                date_obj["D"] = d.strftime("%m/%d/%Y")
                date_obj["E"] = d.strftime("%m/%d/%y")
                date_obj["F"] = d.strftime("%B %d, %Y")
                break
            except ValueError:
                continue
        else:
            # fallback if no format matches
            today = date.today()
            # date_obj["A"] = today
            date_obj["A"] = today.isoformat()
            date_obj["B"] = today.strftime("%d/%m/%Y")
            date_obj["C"] = today.strftime("%d/%m/%y")
            date_obj["D"] = today.strftime("%m/%d/%Y")
            date_obj["E"] = today.strftime("%m/%d/%y")
            date_obj["F"] = today.strftime("%B %d, %Y")
        
        return date_obj

    def _parse_page(self) -> tuple[dict, str]:
        FRONT_MATTER_DELIM = "+++"

        meta = {}
        raw = ""

        md : markdown.Markdown = markdown.Markdown(extensions=["meta", "footnotes", "tables", "def_list", "toc", 'markdown_captions'])
        md_text : str = self.file.read_text(encoding="utf-8")

        lines = md_text.splitlines()
        if lines and lines[0].strip() == FRONT_MATTER_DELIM:
            # find the closing delimiter
            for i in range(1, len(lines)):
                if lines[i].strip() == FRONT_MATTER_DELIM:
                    fm_lines = lines[1:i]
                    if fm_lines:  # parse front matter if not empty
                        meta = tomllib.loads("\n".join(fm_lines))
                    # skip any blank lines immediately after front matter
                    content_lines = lines[i+1:]
                    while content_lines and content_lines[0].strip() == "":
                        content_lines.pop(0)
                    raw = "\n".join(content_lines)
                    break
            else:
                # no closing delimiter found
                raw = "\n".join(lines)
        else:
            # no front matter
            raw = "\n".join(lines)
        
        raw_html : str = md.convert(raw)

        self.__fields["content"] = raw_html
        
        return meta, raw_html
