import shutil
import re
from parser import ParseMarkdown
from pathlib import Path
from datetime import date

class Page:
    def __init__(self, site : "Site", md_file : Path):
        self.site : "Site" = site
        self.parse_fields(md_file)

    def parse_fields(self, md_file : Path):
        parse : ParseMarkdown = ParseMarkdown(md_file)

        content     = parse.content_html                                            # html content, cannot be set by the user
        title       = parse.meta.get("title", [md_file.parent.stem])[0]             # defaults to parent folder name
        _date        = parse.meta.get("date", [date.today()])[0]                    # defaults to date of creation
        template    = parse.meta.get("template", [""])[0]                           # template file name (not full path), defaults to nothing
        section     = parse.meta.get("section", [md_file.parent.parent.stem])[0]    # defaults to parent's parent folder
        tags        = parse.meta.get("tags", [])                                    # unique list field

        fields = {
            "content"   : content,
            "title"     : title,
            "date"      : _date,
            "template"  : template,
            "section"   : section,
            "tags"      : tags,
            # "summary"   : parse.,
            # "url"       : parse.meta.get("url", ""),
        }

        self.__fields = fields

    
    def update_fields(self, new_fields : dict):
        self.__fields = new_fields
    
    def get_field(self, key : str) -> list | None:
        if not key in self.__fields:
            return None
        return self.__fields[key]
    
    def has_field(self, key : str) -> bool:
        return key in self.__fields
    
    def render(self, template_content : str) -> str:
        pre_content : str = self.get_field("content")
        content = pre_content
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

        matches_with_braces = re.findall(r"(\{\{.*?\}\})", content)
        matches = re.findall(r"\{\{(.*?)\}\}", content)
        for i in range(len(matches)):
            m : str = matches[i]
            token : str = m.strip()
            if token.startswith("page."):
                token = token[len("page."):]
                if self.has_field(token):
                    content = content.replace(matches_with_braces[i], self.get_field(token)[0])
        
        return content

class Site:
    def __init__(self, content_path : str, build_path : str, deploy_path : str, templates_path : str):
        self.content_path : Path = Path(content_path)
        self.build_path : Path = Path(build_path)
        self.deploy_path : Path = Path(deploy_path)
        self.templates_path : Path = Path(templates_path)
        self.pages : dict[Path, Page] = {}
        self.sections = {}
        self.tags = {}
    
    def build(self):
        # delete pre-existing build folder
        if self.build_path.exists() and self.build_path.is_dir():
            shutil.rmtree(self.build_path)
        
        self.pages.clear()
        self.sections.clear()
        self.tags.clear()

        for item in self.content_path.rglob("*"):
            target = self.build_path / item.relative_to(self.content_path)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif item.suffix == ".md":
                target.parent.mkdir(parents=True, exist_ok=True)

                page : Page = Page(self, item)
                self.pages[item] = page

                template_path = self.templates_path / f"{page.get_field("template")[0]}.html"
                template_content = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

                output_path : Path = target.parent / "index.html"
                output_path.write_text(page.render(template_content), encoding="utf-8")
        
        self.update_page_indices()
    
    def update_page_indices(self):
        self.sections.clear()
        self.tags.clear()

        for page in self.pages.values():
            if page.has_field("tags"):
                for tag in page.get_field("tags"):
                    self.tags.setdefault(tag, []).append(page)
            if page.has_field("section"):
                section_meta = page.get_field("section")
                assert len(section_meta) == 1, f"section should only have one value. section_meta={section_meta}."
                self.sections.setdefault(section_meta[0], []).append(page)
        # print("\nUPDATE ALL PAGES")
        # print("sections:", self.sections)
        # print("tags:", self.tags)
    
    def update_indices_for_page(self, page : Page):
        for pages in self.tags.values():
            if page in pages:
                pages.remove(page)
        for pages in self.sections.values():
            if page in pages:
                pages.remove(page)

        if page.has_field("tags"):
            for tag in page.get_field("tags"):
                self.tags.setdefault(tag, []).append(page)

        if page.has_field("section"):
            section_meta = page.get_field("section")
            assert len(section_meta) == 1
            self.sections.setdefault(section_meta[0], []).append(page)

        # print("\nUPDATE FOR PAGE")
        # print("sections:", self.sections)
        # print("tags:", self.tags)


    def deploy_path(self):
        pass

