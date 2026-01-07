from pathlib import Path
from parser import ParseMarkdown
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from structure import Site

class WatchDogHandler(FileSystemEventHandler):
    def __init__(self, site : Site):
        super().__init__()
        self.site : Site = site

    def on_modified(self, event: FileSystemEvent) -> None:
        mod_file_path : Path = Path(event.src_path)
        if mod_file_path.suffix == ".md":
            # output : str = parse_markdown(mod_file_path)
            output : str = ParseMarkdown(mod_file_path).content_html
            rel_path : Path = mod_file_path.relative_to(self.site.content_path)
            output_path : Path = Path("build") / rel_path.parent / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")