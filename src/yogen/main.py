import argparse
from .watcher import WatchDogHandler
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer
from pathlib import Path
from ._site import Site
from .defaults import build_default_files

def build(site : Site):
    build_default_files()
    site.build()

def serve(site : Site, port : int):
    event_handler : WatchDogHandler = WatchDogHandler(site)
    observer = Observer()
    observer.schedule(event_handler, site.content_path, recursive=True)
    observer.start()

    http_handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(site.build_path), **kw
    )

    HTTPServer(("127.0.0.1", port), http_handler).serve_forever()

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build")

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("port", type=int, nargs="?", default=8000)

    args = parser.parse_args()

    site : Site = Site(content_path="content", build_path="build", deploy_path="deploy", scripts_path="scripts", styles_path="styles", templates_path="templates")

    if args.cmd == "build":
        build(site)
    elif args.cmd == "serve":
        serve(site, args.port)

if  __name__ == "__main__":
    main()