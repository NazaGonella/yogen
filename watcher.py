from pathlib import Path
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from structure import Site
from structure import Page

class WatchDogHandler(FileSystemEventHandler):
    def __init__(self, site : Site):
        super().__init__()
        self.site : Site = site

    def on_modified(self, event: FileSystemEvent) -> None:
        mod_file_path : Path = Path(event.src_path)
        if (mod_file_path.suffix != ".md"):
            return
        if (mod_file_path in self.site.pages):
            page : Page = self.site.pages[mod_file_path]
            page.parse_fields(mod_file_path)

            self.site.update_indices_for_page(page)

            rel_path : Path = mod_file_path.relative_to(self.site.content_path)
            output_path : Path = Path("build") / rel_path.parent / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(page.get_field("content"), encoding="utf-8")