import shutil

from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from parser import parse_markdown
from structure import Site

site : Site = Site(build_path="build", content_path="content", deploy_path="deploy", templates_path="templates")
site.build()

class WatchDogHandler(FileSystemEventHandler):
    def on_modified(self, event: FileSystemEvent) -> None:
        mod_file_path : Path = Path(event.src_path)
        if mod_file_path.suffix == ".md":
            output : str = parse_markdown(mod_file_path)
            rel_path : Path = mod_file_path.relative_to(site.content_path)
            output_path : Path = Path("build") / rel_path.parent / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output, encoding="utf-8")

def main():
    event_handler : WatchDogHandler = WatchDogHandler()
    observer = Observer()
    observer.schedule(event_handler, site.content_path, recursive=True)
    observer.start()

    http_handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(site.build_path), **kw
    )

    HTTPServer(("127.0.0.1", 8000), http_handler).serve_forever()


main()