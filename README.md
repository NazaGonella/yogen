# yogen

> ⚠️ Work in progress. The API and configuration format may still change.

**yogen** is a straightforward static site generator written in Python. It turns
a folder of Markdown (and plain HTML) files into a complete website, and is built
for quick setup and fast iteration: start a project, run a local server, and see
your changes live as you save.

## Features

- **Markdown-based content** with front matter for per-page metadata
- **Jinja2 templating**: pages can be rendered through reusable HTML templates
- **Live reload**: a local server rebuilds the site as you edit
- **Incremental rebuilds**: only recompiles what changed, so edits show up fast
- **Collections**: organize pages into *sections* and *tags*
- **RSS feed generation** from selected sections and tags
- **Predictable builds**: a clear content-to-output mapping that's robust to authoring mistakes

## Installation

yogen requires **Python 3.10+**.

From source:

```sh
git clone https://github.com/NazaGonella/yogen.git
cd yogen
pip install .
```

Or install the prebuilt wheel from `dist/`:

```sh
pip install dist/yogen-0.5.0-py3-none-any.whl
```

This installs the `yogen` command.

## Quick start

```sh
yogen create mysite   # scaffold a new site
cd mysite
yogen serve           # build + serve at http://127.0.0.1:8000 with live reload
```

Edit the files under `content/` and the browser will reflect your changes on save.
When you're ready to publish, run `yogen build` to generate the final site into
`build/`.

## Commands

| Command | Description |
| --- | --- |
| `yogen create <name>` | Create a new site in a directory called `<name>`. |
| `yogen build` | Compile the site into the `build/` folder. |
| `yogen serve [port] [--no-live]` | Serve the site locally (default port `8000`). Live reload is on by default; pass `--no-live` to disable it. |
| `yogen deploy` | Push the `build/` folder to the remote branch configured in `yogen.toml`. |

## Project structure

A freshly created site looks like this:

```
mysite/
├── yogen.toml        # site configuration (also marks the project root)
├── content/          # your Markdown / HTML pages
└── static/           # assets copied verbatim into the build (CSS, fonts, images…)
    └── templates/    # Jinja2 templates referenced by pages
```

`yogen build` (or `yogen serve`) generates the site into a `build/` folder.

### How files map to the build

- `yogen.toml` designates the root of the site.
- Markdown files in `content/` are compiled to HTML (see [Content-to-URL mapping](#content-to-url-mapping)).
- Non-Markdown files inside `content/` are copied verbatim.
- Files in `static/` are copied as-is into `build/`.

## Configuration

All configuration lives in `yogen.toml`:

```toml
[paths]
static = "static/"
content = "content/"
templates = "templates/"
build = "build/"

[site]
title = "Your Site Title"               # default title for pages
description = "Your site description"   # default description for pages
base_url = "https://example.com"
languages = ["en"]                      # the RSS feed uses the first language

[[site.authors]]
name = "Author Name"
email = "author@example.com"

[deploy]
remote = "origin"
page_repo = "gh-pages"

[feed]                                  # optional, omit to disable the RSS feed
title = "Your Feed Title"
subtitle = "Your Feed Subtitle"
icon = "icon.svg"
output = "feed.xml"
sections = ["posts"]                    # include pages from these sections…
tags = []                               # …and/or these tags
```

Missing or malformed fields fail the build with a clear error.

## Writing content

Each page is a Markdown file with an optional **front matter** block delimited by
`+++` and written in TOML:

```markdown
+++
title = "Tech Post"
authors = ["Your Name"]
date = "2024-01-15"
tags = ["python", "web"]
section = "posts"
template = "/templates/template-post.html"
+++

Lorem ipsum `dolor` sit amet…
```

### Front matter fields

| Field | Type | Default |
| --- | --- | --- |
| `title` | string | derived from the file/folder name, or the site title |
| `authors` | list of strings (a bare string is accepted too) | `[]` |
| `date` | `YYYY-MM-DD` | today |
| `template` | path to a template | none (raw rendered content) |
| `section` | string | `"global"` |
| `tags` | list of strings (a bare string is accepted too) | `[]` |

Any additional fields you add are passed through and made available to templates.
Front matter is optional. A file with no `+++` block compiles fine.

### Content-to-URL mapping

- `index.md` maps to its parent route: `content/blog/index.md` → `/blog/`
- any other Markdown file maps to a same-named HTML file: `content/blog/post.md` → `/blog/post.html`

### Markdown features

yogen enables these Markdown extensions: footnotes, tables, definition lists,
table of contents, [captions](https://pypi.org/project/markdown-captions/), and
fenced code blocks. Indentation-based code blocks are disabled; use fenced blocks
(```` ``` ````) instead.

## Templating

A page is rendered in two stages: the Markdown body is first rendered as a Jinja2
template, then (if `template` is set) wrapped in the named template. Templates
receive the following context:

- `page`: the page's front matter (`page.title`, `page.date`, `page.section`,
  `page.tags`, plus any custom fields)
- `content`: the rendered HTML body of the page
- `url`: the page's route
- `raw`: the page body before templating
- `sections`: a mapping of section name → set of pages
- `tags`: a mapping of tag name → set of pages

The computed values are also mirrored onto `page`, so `page.content`, `page.url`,
and `page.raw` give the same results as `content`, `url`, and `raw`. Use whichever
reads better.

```html
<article>
  <h2>{{ page.title }}</h2>
  <p><em>{{ page.date.strftime("%B %d, %Y") }}</em></p>
  {{ content }}
</article>
```

### Collections

A page belongs to a single **section** but can carry any number of **tags**. Use a
section for a page's primary grouping (the kind of content it is: `posts`, `notes`,
`projects`), and use tags for cross-cutting topics that span sections (`python`,
`tutorial`, `release`). A page defaults to the `"global"` section and no tags.

Because `sections` and `tags` are available in every template, you can build index
pages that list other pages. For example, an `index.md` that lists every post in the
`posts` section, newest first:

```jinja
{% for p in sections.posts | sort(attribute="date", reverse=True) %}
<p>
    {{ p.date.strftime("%d/%m/%Y") }}
    <a href="{{ p.url }}">{{ p.title }}</a>
</p>
{% endfor %}
```

Here each `p` is another page. `p.<field>` resolves to that page's front matter
field if present, otherwise to its computed value, so `p.title` is the title and
`p.url` is the route, the same way `page.<field>` works on the current page.

> **Overriding computed values:** defining a front matter field named `content`,
> `url`, or `raw` overrides the mirrored value, so `page.content` (and `p.content`)
> then return your value instead of the computed one. The build prints a warning
> when this happens, and the computed value is always still available as the
> top-level `content` / `url` / `raw`.

## RSS feed

If a `[feed]` table is present in `yogen.toml`, yogen generates an RSS feed at the
configured `output` path. A page is included when its section is listed in
`feed.sections` or any of its tags is listed in `feed.tags`.

## Build flow

- `.md` body change → **partial rebuild** (only the affected page is recompiled)
- `.md` front matter change → **full rebuild** (metadata can affect collections and the feed)
- any other change (assets, templates, config, file/dir create/delete/move) → **full rebuild**

## Deploy

`yogen deploy` is a convenience command that publishes the `build/`
folder using `git subtree push`, targeting the `remote` and `page_repo` (branch)
configured under `[deploy]`, a common setup for GitHub Pages. You can always
deploy `build/` by your own means instead.

## License

[MIT](LICENSE)
