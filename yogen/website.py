import shutil
import subprocess
from yogen.config import load_config
from yogen.page import Page
from feedgen.feed import FeedGenerator
from datetime import datetime, date, timezone
from pathlib import Path

class Site():
    def __init__(self, config_path : Path):
        self.config_file : Path = config_path
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
                page : Page = Page(item, self.config_file, self.content_path)
                self.pages[item] = page
        
        # TODO: handle sections and tags
        # TODO: test
        for page in self.pages.values():
            self.index_page(page)
    

    def convert_feed(self):
        feed_cfg = self.config.get("feed", {})
        target_sections = set(feed_cfg.get("sections", []))
        target_tags = set(feed_cfg.get("tags", []))

        if not feed_cfg or (not target_sections and not target_tags):
            return

        pages_for_feed = [
            page for page in self.pages.values()
            if (target_sections and self.page_sections.get(page) in target_sections)
            or (target_tags and self.page_tags.get(page, set()) & target_tags)
        ]

        # print("pages:", [str(page.file) for page in pages_for_feed])

        output_path : Path = self.build_path / feed_cfg["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # print("output path:", output_path)

        fg = FeedGenerator()

        site_cfg = self.config["site"]

        base_url = site_cfg["base_url"]
        feed_link = f"{site_cfg["base_url"]}/{feed_cfg['output'].lstrip('/')}"
        fg.id(feed_cfg["output"])
        fg.title(feed_cfg["title"])
        fg.subtitle(feed_cfg["subtitle"])
        fg.link(href=base_url, rel="alternate")
        fg.link(href=feed_link, rel="self")
        # print("link:", base_url)
        # print("feed_link:", feed_link)
        fg.language(site_cfg["languages"][0] if site_cfg["languages"] else "en")    # take first language, defaults to english

        for author in site_cfg["authors"]:
            # print("author:", author["name"])
            # print("email:", author["email"])
            fg.author({"name": author["name"], "email": author["email"]})

        if feed_cfg.get("icon"):
            fg.logo(feed_cfg["icon"])

        # print("\nPAGES\n")
        for page in pages_for_feed:
            page_path : Path = page.file.relative_to(self.content_path)
            url : str = f"{base_url.rstrip("/")}/{str(page_path.parent)}/"
            entry = fg.add_entry()
            entry.id(url)
            entry.link(href=url)
            entry.title(str(page.get_field("title") or "Untitled"))
            entry.content(page.render_raw() or "", type="html")
            page_date = page.get_field("date")
            if isinstance(page_date, date) and not isinstance(page_date, datetime):
                page_date = datetime(page_date.year, page_date.month, page_date.day, tzinfo=timezone.utc)
            entry.pubDate(page_date)

        fg.rss_file(str(output_path))

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
            page : Page = Page(file, self.config_file, self.content_path)
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
        self.convert_feed()


    def deploy(self):
        build_path : Path = self.build_path

        if not build_path.exists() or not build_path.is_dir():
            print("build folder not found. Run `yogen build`.")
            return

        subprocess.run(
            ["git", "subtree", "push", "--prefix", str(build_path), "origin", "gh-pages"],
            check=True,
        )