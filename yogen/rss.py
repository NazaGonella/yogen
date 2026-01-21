import json
from feedgen.feed import FeedGenerator
from pathlib import Path
from yogen.config import load_config
from yogen.page import Page
from datetime import datetime, date, timezone

class MarkdownRSS:
    def __init__(self, pages : list[Page], output_file: str, config_file: str):
        self.pages = pages
        self.output_file = Path(output_file)
        self.config = load_config(Path(config_file))

    def build(self):
        fg = FeedGenerator()

        feed_cfg = self.config["feed"]
        site_cfg = self.config["site"]

        fg.id(feed_cfg["output"])
        fg.title(feed_cfg["title"])
        fg.subtitle(feed_cfg["subtitle"])
        fg.link(href=site_cfg["base_url"], rel="alternate")
        fg.link(href=site_cfg["base_url"] + feed_cfg["output"], rel="self")
        fg.language(site_cfg["languages"][0] if site_cfg["languages"] else "en")

        for author in site_cfg["authors"]:
            fg.author({"name": author["name"], "email": author["email"]})

        if feed_cfg.get("icon"):
            fg.logo(feed_cfg["icon"])

        for page in self.pages:
            entry = fg.add_entry()
            entry.id(f"{site_cfg['base_url']}/{page.file.stem}")
            entry.title(str(page.get_field("title") or "Untitled"))
            entry.link(href=f"{site_cfg['base_url']}/{page.file.stem}")
            entry.content(page.get_field("content") or "", type="html")
            page_date = page.get_field("date")
            if isinstance(page_date, date) and not isinstance(page_date, datetime):
                page_date = datetime(page_date.year, page_date.month, page_date.day, tzinfo=timezone.utc)

            entry.pubDate(page_date)

        fg.rss_file(str(self.output_file))