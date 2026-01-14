---
title: Setting Up a Simple Blog - Handmade Static Site Generator
author: Nazareno Gonella
date: 04/11/25
template: template
---

---

You can check the repository [here](https://github.com/NazaGonella/yors-generator).

The idea to start writing a blog has been in my mind for some time now, until today that I decided to get on with it. And what better way to begin than writing about this same process?

---

### What Am I Looking For?

From the start I knew I wanted something simple, easy to maintain and quick to iterate. One of the major reasons I'm doing this is to structure my thinking when working on any type of project, and for that I need not be distracted by implementation details.

---

### Barebones

Still, I would like to have some formatting, as there were times I would take notes in plain text files for then to never come back to them. So I'm using the next closest thing, Markdown.

Now what I need is to convert this Markdown file into a HTML file. After looking around through some posts on reddit, I found the [pandoc](https://pandoc.org/) document converter, exactly what I needed. For any Markdown file I just had to run `pandoc input.md -o index.html`. 

Pandoc uses an extended version of Markdown which comes in handy, as it includes support for tables, definition lists, footnotes, citations and even math.  It also supports *Metadata Blocks*, which allows including information such as `% title`, `% author` and `% date`. I will only be using `% title` since the tool issues a warning when not using it.

And there it was, just what I wanted, almost.

---

### Not Stylish, Just Yet

A plain HTML file with formatted text is a lot better than a plain text file, but unfortunately it doesn't look good on the portfolio. 

I need something simple, but still good looking. Luckily you can link a `.css` file to the output of pandoc using the `--css` argument. The problem is I don't have much experience using css, so it is time to look for references.

I really like [Fabien Sanglard's](https://fabiensanglard.net/) and [Steve Losh's](https://stevelosh.com/) websites. They are minimalistic, nice to look at, and easy to read. I appreciate how you can immediately see all the stuff the authors have been working on or pondering over the last couple of years as soon as you enter. With the help of inspect element, a couple of queries to ChatGPT, and a background from [Hero Patterns](https://heropatterns.com/), I ended up with a style I was happy with.

There was now a need for a nice header: css and Markdown alone wouldn't suffice. Fortunately, pandoc allows for HTML to be written into the Markdown file, which it then passes to the final output unchanged. I can now define a simple header to include on all the pages and ensure a concise style, but to achieve that I would have to copy and paste the same header everytime I create a new page. It would be nice to have some sort of page template.

---

### The Page Template

I went on and created `create-post.py`, a Python script that takes `<file-name>` and `<post-title>` as arguments. This script creates `<file-name>.md` and writes to it the metadata block `% <post-title>`, the page header and the post header with the date of when the post was created.[^1]

    header_date = datetime.now().strftime("%B {S}, %Y").replace('{S}', str(datetime.now().day))

    header = f"""%{post_title}

    <header>
        header content goes here
    </header>

    ## {post_title}

    {header_date}

    ---

    with open(f"{posts_path}/{file_name}/{file_name}.md", "w", encoding="utf-8") as f:
        f.write(header)

I also included some code to add the post entry along with the date to the home page

    home_path = "./home.md"
    date_entry = datetime.now().strftime("%d/%m/%Y")
    post_entry = f"{date_entry}: [**{post_title}**]({posts_path}/{file_name}/index.html)  \n"

    with open(home_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines.insert(7, post_entry) # hardcoded position, for now

    with open(home_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

Some of this code is hardcoded. I plan on adding config files in the future. To see the full code visit the [repository](https://github.com/NazaGonella/ngonella-static-site-generator).

With this, I now have an easy way of creating new entries.

---

### Generating the Site

Calling pandoc for every `.md` file is not ideal. That's why I implemented `build.py`, a minimal build system for transforming recently modified Markdown files into HTML files.

    import os
    import subprocess
    from pathlib import Path

    css_path = Path("style.css").resolve()      # absolute path to CSS

    ignored_mds = [Path("./README.md")]         # will not apply to ALL Markdown files

    markdown_files = [md for md in Path(".").rglob("*.md") if md not in ignored_mds]

    paired_files = [(md, md.parent / "index.html") for md in markdown_files if md not in ignored_mds]   # target: index.html file in the same directory

    print("### BUILD ###")

    for md, html in paired_files:
        mod_time_md = md.stat().st_mtime
        if html.exists():
            mod_time_html = html.stat().st_mtime
            if mod_time_html >  mod_time_md:
                continue

        relative_path_css  = os.path.relpath(css_path, start=html.parent)  # relative to html and md path

        subprocess.run([
            "pandoc",
            "-s", str(md),
            "-o", str(html),
            "--css", relative_path_css,
            "-V", "title="
        ])

        print(md, "->", html)

`-s` inserts the necessary headers and footers to create a full HTML file.

`-V title=` prevents pandoc of inserting the variable defined in `% title` as a header, while still keeping it as the document title.

---

### Workflow

I will be using [vim](https://www.vim.org/) as my text editor, primarily for three reasons.

1. Fast and comfortable to write in.
2. Very customizable.
3. Looks cool.

Probably one of the most important aspects of using vim in this case is having the option to execute a command when saving the file. Thanks to this, I can now avoid having to call pandoc with the same arguments everytime I want to see the results on the browser. I just save the file and the HTML file is automatically generated.

I added the following to the `.vimrc`

    let s:script_dir = expand('<sfile>:p:h')
    autocmd FileType markdown autocmd BufWritePost <buffer> execute '!python3 ' . shellescape(s:script_dir . '/build.py')

This will apply only when saving `.md` files.[^2]

How about deployment? As I'm using Github Pages for hosting, pushing my local files to the remote repository will deploy the page. The thing is, I don't want to deploy everytime I correct a minor mistake, it would make version control really uncomfortable.

To fix this I created a new `working` branch. Every change I make gets pushed to that branch. And once I feel it's time to deploy, I merge into the `master` branch.

For easy deployment I made a simple shell script `deploy.sh`.

    set -e

    working_branch="working"

    git checkout master
    git merge "$working_branch" --no-ff -m "Merge $working_branch branch into master"
    git push origin master

    echo "Master branch updated"

    git checkout "$working_branch"

`set -e` tells the shell to exit immediately if any command fails.

`--no-ff` ensures git creates a merge commit even if a fast-forward is possible.

---


And there it is, a simple framework for my use case. Every time I want to write about a new topic, I run `create-post.py` and start writing right away. Once I'm done, I simply save and check the browser. If I'm happy with the result, I commit, push to origin and then run `deploy.sh`. And just like that a new entry is added to the blog.

Initially, I wasn't familiar with the concept of static site generators. I've seen recommendations of tools like [Jekyll](https://jekyllrb.com/) or [Hugo](https://gohugo.io/) for easily creating personal websites, but I felt they were more than what I needed at the moment[^3]. I also liked the idea of creating a basic blog framework. What I ended up with was a custom static site generator. 

Now it's a matter of time to see how well this framework holds up for me.


[^1]: It would make more sense for the date to be the day it's published, added to the TODO list.
[^2]: This assumes the .vimrc or .exrc files are in the same directory as build.py.
[^3]: Reading Fabien Sanglard's post [All you may need is HTML](https://fabiensanglard.net/html/index.html) may have had an effect on this decision.
