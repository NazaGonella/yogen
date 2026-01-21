import argparse
import shutil
from yogen.website import Site
from yogen.page import Page
from yogen.watcher import WatchDogHandler
from importlib import resources
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from watchdog.observers import Observer

CONFIG_PATH = "yogen.toml"

def yogen_folder_check():
    if not Path(CONFIG_PATH).is_file():
        raise SystemExit(
            "not a yogen site. Run 'yogen create <name>'."
        )

def parse_arguments():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    create_p = sub.add_parser("create")
    create_p.add_argument("name")

    sub.add_parser("build")

    serve_p = sub.add_parser("serve")
    serve_p.add_argument("port", type=int, nargs="?", default=8000)

    return parser.parse_args()


def cmd_create(name : str):
    root = Path(name)
    defaults = resources.files("yogen").joinpath("defaults")
    if root.exists():
        raise FileExistsError(root)

    with resources.as_file(defaults) as src:
        shutil.copytree(src, root)


def cmd_build():
    site : Site = Site(Path(CONFIG_PATH))
    site.build()
    # print("SECTIONS")
    # for k, v in site.sections.items():
    #     print(k, "->", [str(p.file) for p in v])

    # print("PAGE_SECTIONS")
    # for p, s in site.page_sections.items():
    #     print(str(p.file), "->", s)

    # print("TAGS")
    # for k, v in site.tags.items():
    #     print(k, "->", [str(p.file) for p in v])

    # print("PAGE_TAGS")
    # for p, tags in site.page_tags.items():
    #     print(str(p.file), "->", list(tags))

def cmd_serve(port : int):
    site : Site = Site(Path(CONFIG_PATH))
    site.build()

    event_handler : WatchDogHandler = WatchDogHandler()
    event_handler.on_rebuild_all = site.build
    event_handler.on_rebuild_md = site.rebuild_md

    observer = Observer()
    # TODO watch templates folder: on any event, rebuild
    observer.schedule(event_handler, site.content_path, recursive=True)
    observer.start()

    http_handler = lambda *a, **kw: SimpleHTTPRequestHandler(
        *a, directory=str(site.build_path), **kw
    )

    HTTPServer(("127.0.0.1", port), http_handler).serve_forever()


def main():
    args = parse_arguments()

    match args.cmd:
        case "create":
            cmd_create(args.name)
        case "build":
            yogen_folder_check()
            cmd_build()
        case "serve":
            yogen_folder_check()
            cmd_serve(args.port)


if __name__ == "__main__":
    main()