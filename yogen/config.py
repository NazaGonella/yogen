import tomllib
from pathlib import Path

def load_config(root: Path):
    if not root.exists():
        raise FileNotFoundError(f"Config file not found: {root}")
    if not root.is_file():
        raise ValueError(f"Expected a file, got: {root}")

    with root.open("rb") as f:
        config = tomllib.load(f)

    # paths section
    paths = config.get("paths")
    if not isinstance(paths, dict):
        raise KeyError("Missing or invalid [paths] section")
    for key in ("static", "content", "templates", "build"):
        if key not in paths or not isinstance(paths[key], str):
            raise KeyError(f"Missing or invalid paths.{key}")

    # site section
    site = config.get("site")
    if not isinstance(site, dict):
        raise KeyError("Missing or invalid [site] section")
    for key in ("title", "description", "base_url", "languages"):
        if key not in site:
            raise KeyError(f"Missing site.{key}")
    if not isinstance(site["title"], str):
        raise TypeError("site.title must be a string")
    if not isinstance(site["description"], str):
        raise TypeError("site.description must be a string")
    if not isinstance(site["base_url"], str):
        raise TypeError("site.base_url must be a string")
    if not isinstance(site["languages"], list) or not all(isinstance(l, str) for l in site["languages"]):
        raise TypeError("site.languages must be a list of strings")

    # site.authors
    authors = site.get("authors")
    if not isinstance(authors, list) or not all(isinstance(a, dict) for a in authors):
        raise TypeError("site.authors must be a list of dicts")
    for i, author in enumerate(authors, start=1):
        if "name" not in author or "email" not in author:
            raise KeyError(f"site.authors[{i}] missing name or email")
        if not isinstance(author["name"], str) or not isinstance(author["email"], str):
            raise TypeError(f"site.authors[{i}] name/email must be strings")

    # feed section
    feed = config.get("feed")
    if not isinstance(feed, dict):
        raise KeyError("Missing or invalid [feed] section")
    for key in ("enabled", "entries_path", "title", "subtitle", "icon", "output"):
        if key not in feed:
            raise KeyError(f"Missing feed.{key}")
    if not isinstance(feed["enabled"], bool):
        raise TypeError("feed.enabled must be a boolean")
    for key in ("entries_path", "title", "subtitle", "icon", "output"):
        if not isinstance(feed[key], str):
            raise TypeError(f"feed.{key} must be a string")

    return config
