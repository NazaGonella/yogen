import shutil
from pathlib import Path
from src.structure.page import Page

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

                page : Page = Page(item)
                self.pages[item] = page

                template_path = self.templates_path / f"{page.get_field("template")}.html"
                template_content = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

                output_path : Path = target.parent / "index.html"
                output_path.write_text(page.render(template_content), encoding="utf-8")
            elif item.suffix == ".css":
                # target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
            elif item.suffix == ".js":
                # target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        
        self.update_page_indices()
    
    def update_page_indices(self):
        self.sections.clear()
        self.tags.clear()

        for page in self.pages.values():
            if page.has_field("tags"):
                for tag in page.get_field("tags"):
                    self.tags.setdefault(tag, []).append(page)
            if page.has_field("section"):
                self.sections.setdefault(page.get_field("section"), []).append(page)
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
            self.sections.setdefault(page.get_field("section"), []).append(page)

        # print("\nUPDATE FOR PAGE")
        # print("sections:", self.sections)
        # print("tags:", self.tags)


    def deploy_path(self):
        pass

