## Work in progress

## Welcome to yogen!

yogen is a straightforward static site generator written in Python. It lets you build websites from Markdown or HTML files, designed for quick setup and fast iteration.

## Features

- Live editing
- Partial rebuilding
- Simple templating system
- Generation of RSS feeds

## Quick setup

You can install yogen via [PyPy](), or by downloading the [executable]().

## All the commands

- `yogen create name`: Creates your site's directory.
- `yogen build`: Compiles your site, generating the output in the `build` folder.
- `yogen serve [--no-live] [port]`: Serves the site locally on the given port (default: 8000). Add the --no-live option if you don't want live rebuilding of your site.
- `yogen deploy`: Push the results of the `build` into a remote repository. 

## Content to URL mapping

- `index.md` maps to the parent route (`/blog/index.md` -> `/blog/`).
- Any other markdown file maps to an html file with the same name (`/blog/post.md` -> `/blog/post.html`).

## Yogen Markdown

## Yogen Collections

### Sections

### Tags

## Build flow

- .md file modification --> partial rebuild
- .md file front matter modification --> full rebuild
- other file modification --> full rebuild