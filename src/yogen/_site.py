import shutil
from pathlib import Path
from .page import Page
from .rss import MarkdownRSS

class Site:
    def __init__(self, content_path : str, build_path : str, deploy_path : str, scripts_path : str, assets_path : str, styles_path : str, templates_path : str, rss_config_path : str):
        self.content_path : Path = Path(content_path)
        self.build_path : Path = Path(build_path)
        self.deploy_path : Path = Path(deploy_path)
        self.assets_path : Path = Path(assets_path)
        self.scripts_path : Path = Path(scripts_path)
        self.styles_path : Path = Path(styles_path)
        self.templates_path : Path = Path(templates_path)
        self.rss_config_path : Path = Path(rss_config_path)
        self.pages : dict[Path, Page] = {}
        self.sections = {}
        self.tags = {}
    
    def build(self):
        # delete pre-existing build folder
        if self.build_path.exists() and self.build_path.is_dir():
            shutil.rmtree(self.build_path)
        
        self.build_path.mkdir(parents=True, exist_ok=True)

        # css files
        for css_file in self.styles_path.rglob("*.css"):
            target = self.build_path / css_file.name
            shutil.copy2(css_file, target)

        # js files
        for asset in self.scripts_path.rglob("*.js"):
            target = self.build_path / asset.name
            shutil.copy2(asset, target)
        
        # assets files
        for asset in self.assets_path.rglob("*"):
            target = self.build_path / asset.name
            shutil.copy2(asset, target)

        
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
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

        # generate RSS
        rss = MarkdownRSS(
            source_path=self.content_path,
            output_file=str(self.build_path / "feed.xml"),
            config_file=self.rss_config_path
        )
        rss.build()
        
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

