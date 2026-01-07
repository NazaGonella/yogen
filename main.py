import shutil

from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from parser import parse_markdown

content_path = Path("content")
build_path = Path("build")

class WatchDogHandler(FileSystemEventHandler):
    def on_modified(self, event: FileSystemEvent) -> None:
        mod_file_path : Path = Path(event.src_path)
        if mod_file_path.suffix == ".md":
            output : str = parse_markdown(mod_file_path)

            output_path : Path = mod_file_path.parent / "index.html"
            output_path.write_text(output, encoding="utf-8")

def build(src:Path):
    # delete pre-existing build folder
    if build_path.exists() and build_path.is_dir():
        shutil.rmtree(build_path)

    for item in src.rglob("*"):
        target = build_path / item.relative_to(src)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif item.suffix == ".md":
            target.parent.mkdir(parents=True, exist_ok=True)
            output : str = parse_markdown(item)
            output_path : Path = target.parent / "index.html"
            output_path.write_text(output, encoding="utf-8")


def main():
    event_handler = WatchDogHandler()

    observer = Observer()
    observer.schedule(event_handler, content_path, recursive=True)
    observer.start()

    build(content_path)

    handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(build_path), **kw
    )

    HTTPServer(("127.0.0.1", 8000), handler).serve_forever()

main()