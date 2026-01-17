import argparse
from .watcher import WatchDogHandler
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer
from pathlib import Path
from ._site import Site
from .defaults import build_default_files

def build(site : Site):
    site.build()

def serve(site : Site, port : int):
    site.build()

    event_handler : WatchDogHandler = WatchDogHandler(site)
    observer = Observer()
    observer.schedule(event_handler, site.content_path, recursive=True)
    observer.start()

    http_handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(site.build_path), **kw
    )

    HTTPServer(("127.0.0.1", port), http_handler).serve_forever()

def make_site(root: Path) -> Site:
    return Site(
        content_path=root / "content",
        build_path=root / "build",
        deploy_path=root / "deploy",
        scripts_path=root / "scripts",
        assets_path=root / "assets",
        styles_path=root / "styles",
        templates_path=root / "templates",
        rss_config_path=root / "rss-config.json"
    )

def yogen_folder_check():
    if not Path(".yogen").is_file():
        raise SystemExit(
            "not a yogen site. Run `yogen create <name>`."
        )

def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)


    create_p = sub.add_parser("create")
    create_p.add_argument("name")

    sub.add_parser("build")

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("port", type=int, nargs="?", default=8000)

    args = parser.parse_args()

    if args.cmd == "create":
        root = Path(args.name)
        root.mkdir(parents=True, exist_ok=True)
        (root / ".yogen").touch(exist_ok=True)
        site = make_site(root)
        build_default_files(root)
        build(site)
    else:
        yogen_folder_check()
        site = make_site(Path("."))
        if args.cmd == "build":
            build(site)
        elif args.cmd == "serve":
            serve(site, args.port)

if  __name__ == "__main__":
    main()