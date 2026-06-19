import sys
import tomllib
import markdown
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from yogen.config import load_config
from pathlib import Path
from datetime import date, datetime
from yogen.front_matter import FrontMatter

# Computed/derived values that are always exposed at the top level of the render
# context (content, url, raw) and mirrored onto `page` so page.content == content
# unless the user defines a front matter field of the same name.
COMPUTED_FIELDS = ("content", "url", "raw")


class _PageMeta(dict):
    def bind(self, computed: dict) -> "_PageMeta":
        self._computed = computed
        return self

    def __missing__(self, key):
        computed = getattr(self, "_computed", None)
        if computed is not None and key in COMPUTED_FIELDS:
            return computed[key]
        raise KeyError(key)


class Page():
    def __init__(self, md_file : Path, config_file : Path, content_path : Path, meta_sections : dict[str, set[Page]], meta_tags : dict[str, set[Page]]):
        self.config : Path = load_config(config_file)
        self.content_path : Path = content_path
        self.file : Path = md_file

        self.__metadata = {
            "page": {},
            "content": Markup(""),
            "raw": "",
            "url": "",
            "sections": meta_sections,
            "tags": meta_tags,
        }

        meta, self.raw_html = self._md_to_html()

        fm = FrontMatter.model_validate(meta)

        rel_file = md_file.relative_to(content_path)
        rel_parent = rel_file.parent.as_posix()

        # Routing model:
        # - index.md -> parent URL (e.g. /guides/index.md -> /guides/)
        # - name.md  -> name.html (e.g. /guides/quickstart.md -> /guides/quickstart.html)
        if md_file.stem == "index":
            url = "/" if rel_parent == "." else f"/{rel_parent}/"
        else:
            if rel_parent == ".":
                url = f"/{md_file.stem}.html"
            else:
                url = f"/{rel_parent}/{md_file.stem}.html"

        # `page` holds the document's front matter (recognized fields + user
        # extras). Missing computed names fall back to the computed values, so
        # page.content == content unless the user overrides it (see _PageMeta).
        page = _PageMeta({
            "title" : fm.title or self._define_title(md_file, content_path),
            "authors" : fm.authors,
            "date" : fm.date,
            "template" : fm.template,
            "section" : fm.section,
            "tags" : fm.tags,
        })
        page.update(fm.model_extra)
        page.bind(self.__metadata)

        # warn when a user field overrides a built-in computed value
        for name in COMPUTED_FIELDS:
            if name in fm.model_extra:
                print(
                    f"WARNING: {md_file}: front matter field '{name}' overrides the "
                    f"built-in page.{name}; the computed value is still available as "
                    f"the top-level '{name}' in templates.",
                    file=sys.stderr,
                )

        self.__metadata["page"] = page
        self.__metadata["url"] = url
        self.__metadata["raw"] = self.raw_html

    
    def __hash__(self):
        return hash(self.file)
    
    def __eq__(self, other):
        if not isinstance(other, Page):
            return NotImplemented
        return self.file == other.file
    
    def __getattr__(self, name):
        # __getattr__ runs only when normal attribute lookup fails; use the raw
        # lookup to avoid recursing back here before __metadata is set.
        try:
            metadata = object.__getattribute__(self, "_Page__metadata")
        except AttributeError:
            raise AttributeError(name)

        page = metadata["page"]
        if name in page:
            return page[name]
        if name in COMPUTED_FIELDS:
            return metadata[name]
        raise AttributeError(name)
    
    def get_meta(self, key : str) -> object | None:
        if not key in self.__metadata["page"]:
            return None
        return self.__metadata["page"][key]

    def has_meta(self, key : str) -> bool:
        return key in self.__metadata["page"]

    def meta_snapshot(self) -> dict:
        # only front matter is tracked here; computed values (content, url, raw)
        # live outside the page dict and are derived deterministically.
        return dict(self.__metadata["page"])

    def render(self, build_path: Path) -> str:
        content_template : Template = Template(self.raw_html)
        rendered_content = content_template.render(**self.__metadata)

        self.__metadata["content"] = Markup(rendered_content)

        template_path : str = self.get_meta("template")
        if not template_path:
            return rendered_content

        env = Environment(
            loader=FileSystemLoader(str(build_path)),
            autoescape=select_autoescape()
        )

        template = env.get_template(str(Path(template_path).relative_to("/")))
        return template.render(**self.__metadata)
    
    def render_raw(self) -> str:
        return self.__metadata["content"]

    def _define_title(self, md_file : Path, content_path : Path) -> str:
        if md_file.stem != "index":
            title = md_file.stem
        elif md_file.parent == content_path:
            title = self.config.site.title
        else:
            title = md_file.parent.stem
        return title

    def _parse_date(self, value : str) -> date:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"Invalid date format: {value}. Expected ISO YYYY-MM-DD.")
    
    def _md_to_html(self) -> tuple[dict, str]:
        FRONT_MATTER_DELIM = "+++"

        meta = {}
        raw = ""

        md : markdown.Markdown = markdown.Markdown(extensions=["footnotes", "tables", "def_list", "toc", 'markdown_captions', 'fenced_code'])
        md.parser.blockprocessors.deregister("code")    # this disables code blocks by indentation
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

        # provisional rendered body; render() overwrites it with the Jinja-rendered version
        self.__metadata["content"] = Markup(raw_html)

        return meta, raw_html
