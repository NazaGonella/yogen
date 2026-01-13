from src.watcher import WatchDogHandler
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer

from src.structure.site import Site

site : Site = Site(build_path="build", content_path="content", deploy_path="deploy", templates_path="templates")
site.build()

def main():
    event_handler : WatchDogHandler = WatchDogHandler(site)
    observer = Observer()
    observer.schedule(event_handler, site.content_path, recursive=True)
    observer.start()

    http_handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(site.build_path), **kw
    )

    HTTPServer(("127.0.0.1", 8000), http_handler).serve_forever()

main()