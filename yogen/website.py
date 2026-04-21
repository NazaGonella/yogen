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
        self.sections : dict[str, set[Page]] = {}
        self.tags : dict[str, set[Page]] = {}
        self.page_sections : dict[Page, str] = {}
        self.page_tags : dict[Page, set[str]] = {}

        # helper paths
        self.build_path : Path = Path(self.config.paths.build)
        self.content_path : Path = Path(self.config.paths.content)
        self.static_path : Path = Path(self.config.paths.static)


    def index_page(self, page : Page):
        old_section : str = self.page_sections.pop(page, None)
        if old_section is not None:
            self.sections[old_section].discard(page)

        old_tags : set[str] = self.page_tags.pop(page, set())
        for tag in old_tags:
            self.tags[tag].discard(page)

        new_tags : set[str] = set()
        if page.has_meta("tags"):
            for tag in page.get_meta("tags"):
                self.tags.setdefault(tag, set()).add(page)
                new_tags.add(tag)
        self.page_tags[page] = new_tags

        if page.has_meta("section"):
            section : str = page.get_meta("section")
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
                page : Page = Page(item, self.config_file, self.content_path, self.sections, self.tags)
                self.pages[item] = page
        
        # TODO: handle sections and tags
        # TODO: test
        for page in self.pages.values():
            self.index_page(page)


    def convert_feed(self):
        feed_cfg = self.config.feed
        if feed_cfg:
            target_sections = set(feed_cfg.sections)
            target_tags = set(feed_cfg.tags)

            if not feed_cfg or (not target_sections and not target_tags):
                return

            pages_for_feed = [
                page for page in self.pages.values()
                if (target_sections and self.page_sections.get(page) in target_sections)
                or (target_tags and self.page_tags.get(page, set()) & target_tags)
            ]

            # print("pages:", [str(page.file) for page in pages_for_feed])

            output_path : Path = self.build_path / feed_cfg.output
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # print("output path:", output_path)

            fg = FeedGenerator()

            site_cfg = self.config.site

            base_url = site_cfg.base_url
            feed_link = f"{site_cfg.base_url}/{feed_cfg.output.lstrip('/')}"
            fg.id(feed_cfg.output)
            fg.title(feed_cfg.title)
            fg.subtitle(feed_cfg.subtitle)
            fg.link(href=base_url, rel="alternate")
            fg.link(href=feed_link, rel="self")
            fg.language(site_cfg.languages[0] if site_cfg.languages else "en")    # take first language, defaults to english

            for author in site_cfg.authors:
                fg.author({"name": author.name, "email": author.email})

            if feed_cfg.icon:
                fg.logo(feed_cfg.icon)

            # print("\nPAGES\n")
            for page in pages_for_feed:
                url : str = f"{base_url.rstrip('/')}{page.get_meta('url')}"
                entry = fg.add_entry()
                entry.id(url)
                entry.link(href=url)
                entry.title(str(page.get_meta("title") or "Untitled"))
                entry.content(page.render_raw() or "", type="html")
                page_date = page.get_meta("date")
                if isinstance(page_date, date) and not isinstance(page_date, datetime):
                    page_date = datetime(page_date.year, page_date.month, page_date.day, tzinfo=timezone.utc)
                entry.pubDate(page_date)

            fg.rss_file(str(output_path))

    def _output_relative_path(self, file: Path) -> Path:
        rel_file: Path = file.relative_to(self.content_path)
        if file.stem == "index":
            return rel_file.parent / "index.html"
        return rel_file.parent / f"{file.stem}.html"

    def _collect_markdown_outputs(self) -> dict[Path, Path]:
        outputs: dict[Path, Path] = {}
        for item in self.content_path.rglob("*.md"):
            output_rel: Path = self._output_relative_path(item)
            outputs[output_rel] = item
        return outputs

    def convert_page(self, file : Path, page : Page):
        output_rel: Path = self._output_relative_path(file)
        output_path: Path = self.build_path / output_rel
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(
            page.render(self.build_path),
            encoding="utf-8",
        )
    

    def convert_pages(self):    # should it be convert_loaded_pages()?
        for file, page in self.pages.items():
            self.convert_page(file, page)

    def _remove_page_from_indexes(self, page: Page):
        old_section: str = self.page_sections.pop(page, None)
        if old_section is not None:
            self.sections[old_section].discard(page)

        old_tags: set[str] = self.page_tags.pop(page, set())
        for tag in old_tags:
            self.tags[tag].discard(page)


    def copy_static_files(self):
        shutil.copytree(self.static_path, self.build_path)

    def copy_raw_content_files(self, markdown_outputs: dict[Path, Path]):
        for item in self.content_path.rglob("*"):
            if item.is_file() and item.suffix != ".md":
                target_rel = item.relative_to(self.content_path)
                target = self.build_path / target_rel
                target.parent.mkdir(parents=True, exist_ok=True)

                # Case 1: raw content file path collides with a markdown-generated output path.
                md_source = markdown_outputs.get(target_rel)
                if md_source is not None:
                    raise RuntimeError(
                        f"Output path collision: raw file {item} conflicts with markdown output "
                        f"from {md_source} at {target}"
                    )

                # Case 2: destination already exists (typically from static/ copy).
                if target.exists():
                    raise RuntimeError(
                        f"Output path collision: destination already exists at {target} "
                        f"(likely from static/) while copying raw file {item}"
                    )

                shutil.copy2(item, target)
    

    def rebuild_md(self, md_files: set[Path]):
        for file in md_files:
            if file.exists():
                page : Page = Page(file, self.config_file, self.content_path, self.sections, self.tags)
                self.pages[file] = page

                self.index_page(page)
                self.convert_page(file, page)
                continue

            old_page : Page | None = self.pages.pop(file, None)
            if old_page is not None:
                # case 1: remove deleted/moved page from in-memory section/tag indexes.
                self._remove_page_from_indexes(old_page)

            # case 2: remove stale generated output left by deleted/moved source markdown.
            output_path : Path = self.build_path / self._output_relative_path(file)
            if output_path.exists():
                output_path.unlink()


    def build(self):
        if self.build_path.exists() and self.build_path.is_dir():
            shutil.rmtree(self.build_path)

        self.copy_static_files()

        markdown_outputs = self._collect_markdown_outputs()
        self.copy_raw_content_files(markdown_outputs)
        self.load_pages()
        self.convert_pages()
        self.convert_feed()


    def deploy(self):
        build_path : Path = self.build_path

        if not build_path.exists() or not build_path.is_dir():
            print("build folder not found. Run `yogen build`.")
            return

        subprocess.run(
            ["git", "subtree", "push", "--prefix", str(build_path), self.config.deploy.remote, self.config.deploy.page_repo],
            check=True,
        )
