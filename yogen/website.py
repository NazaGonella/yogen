import shutil
from yogen.config import load_config
from yogen.page import Page
from pathlib import Path

class Site():
    def __init__(self, config_path : Path):
        self.config = load_config(config_path)
        self.pages : dict[Path, Page] = {}
        self.templates : dict[str, str] = {}    # template name -> template content
        self.sections : dict[str, set[Page]] = {}
        self.tags : dict[str, set[Page]] = {}
        self.page_sections : dict[Page, str] = {}
        self.page_tags : dict[Page, set[str]] = {}

        # helper paths
        self.build_path : Path = Path(self.config['paths']['build'])
        self.content_path : Path = Path(self.config['paths']['content'])
        self.templates_path : Path = Path(self.config['paths']['templates'])
        self.static_path : Path = Path(self.config['paths']['static'])


    def index_page(self, page : Page):
        old_section : str = self.page_sections.pop(page, None)
        if old_section is not None:
            self.sections[old_section].discard(page)

        old_tags : set[str] = self.page_tags.pop(page, set())
        for tag in old_tags:
            self.tags[tag].discard(page)

        new_tags : set[str] = set()
        if page.has_field("tags"):
            for tag in page.get_field("tags"):
                self.tags.setdefault(tag, set()).add(page)
                new_tags.add(tag)
        self.page_tags[page] = new_tags

        if page.has_field("section"):
            section : str = page.get_field("section")
            self.sections.setdefault(section, set()).add(page)
            self.page_sections[page] = section

    
    def load_pages(self):
        self.pages.clear()
        self.sections.clear()
        self.tags.clear()

        self.page_sections.clear()
        self.page_tags.clear()

        for item in self.content_path.rglob("*"):
            if item.suffix == ".md":
                page : Page = Page(item)
                self.pages[item] = page
        
        # TODO: handle sections and tags
        # TODO: test
        for page in self.pages.values():
            self.index_page(page)
    

    def convert_page(self, file : Path, page : Page):
        target: Path = self.build_path / file.relative_to(self.content_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        output_path: Path = target.parent / "index.html"
        output_path.write_text(
            page.render(self.templates),
            encoding="utf-8",
        )
    

    def convert_pages(self):    # should it be convert_loaded_pages()?
        self.load_templates()

        for file, page in self.pages.items():
            self.convert_page(file, page)


    def copy_other_files(self):
        for item in self.content_path.rglob("*"):
            if item.is_file() and item.suffix != ".md":
                target = self.build_path / item.relative_to(self.content_path)
                target.parent.mkdir(parents=True, exist_ok=True)

                if target.exists():
                    raise RuntimeError(
                        f"Output path collision: {target} "
                        f"(raw file conflicts with markdown-generated page)"
                    )

                shutil.copy2(item, target)
    

    def load_templates(self):
        for file in self.templates_path.glob("*.html"):
            name = file.stem
            self.templates[name] = file.read_text(encoding="utf-8")
    

    def rebuild_md(self, md_files: set[Path]):
        self.load_templates()

        for file in md_files:
            page = Page(file)
            self.pages[file] = page

            self.index_page(page)
            self.convert_page(file, page)


    def build(self):
        if self.build_path.exists() and self.build_path.is_dir():
            shutil.rmtree(self.build_path)

        shutil.copytree(self.static_path, self.build_path)

        self.load_pages()
        self.convert_pages()
        self.copy_other_files()