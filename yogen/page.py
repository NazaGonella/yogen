import tomllib
import markdown
import ast
import re
from yogen.config import load_config
from pathlib import Path
from datetime import date, datetime

class Page():
    def __init__(self, md_file : Path, config_file : Path, content_path : Path):
        self.config = load_config(config_file)
        self.file : Path = md_file
        self.__fields = {
            "title" : self._define_title(md_file, content_path),
            "author" : "",
            "date" : date.today(),
            "template" : "",
            "section" : "global",
            "tags" : []
        }
        meta, self.raw_html = self._parse_page()
        protected = {"content", "raw"}      # fields users cannot set
        for k, v in meta.items():
            if k == "date":
                self.__fields[k] = self._parse_date(v)
            elif k not in protected:
                self.__fields[k] = v
            else:
                raise ValueError(f"metadata field '{k}' is protected and cannot be set")
    
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

        # start with template applied
        content : str = template_content or pre_content
        if template_content:
            pattern = re.compile(r"\{\{\s*page\.content\s*\}\}")
            # content = pattern.sub(pre_content, content)
            content = pattern.sub(lambda _: pre_content, content)

        content = self._replace_placeholders(content)

        return content
    
    def render_raw(self) -> str:
        content : str = self.get_field("content")
        content = self._replace_placeholders(content)
        return content

    def _define_title(self, md_file : Path, content_path : Path) -> str:
        if md_file.stem != "index":
            title = md_file.stem
        elif md_file.parent == content_path:
            title = self.config["site"]["title"]
        else:
            title = md_file.parent.stem
        return title

    
    def _parse_date(self, value : str) -> date:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {value}. Expected ISO YYYY-MM-DD.")
    
    def page_date(self, fmt: str = "%Y-%m-%d") -> str:
        """Return the formatted date for templates"""
        d = self.get_field("date")
        if not isinstance(d, (date, datetime)):
            return ""  # fallback
        return d.strftime(fmt)

    def _parse_page(self) -> tuple[dict, str]:
        FRONT_MATTER_DELIM = "+++"

        meta = {}
        raw = ""

        md : markdown.Markdown = markdown.Markdown(extensions=["footnotes", "tables", "def_list", "toc", 'markdown_captions'])
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

    
    def _replace_placeholders(self, _content : str) -> str:
        content = _content
        # find all placeholders
        matches_with_braces = re.findall(r"(\{\{.*?\}\})", content)
        matches = re.findall(r"\{\{(.*?)\}\}", content)

        for i, m in enumerate(matches_with_braces):
            token = matches[i].strip()
            if not token.startswith("page."):
                continue

            expr = token[len("page."):]

            try:
                node = ast.parse(expr, mode="eval").body

                # method call: page.method(args)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    method_name = node.func.id
                    args = [ast.literal_eval(a) for a in node.args]
                    method = getattr(self, f"page_{method_name}", None)
                    if callable(method):
                        replacement = str(method(*args))
                        content = content.replace(m, replacement)

                # property access: page.field
                elif isinstance(node, ast.Name):
                    field_name = node.id
                    if self.has_field(field_name):
                        replacement = str(self.get_field(field_name))
                        content = content.replace(m, replacement)

            except Exception:
                pass

        return content