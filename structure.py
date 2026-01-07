import shutil
from parser import ParseMarkdown
from pathlib import Path

class Site:
    def __init__(self, content_path : str, build_path : str, deploy_path : str, templates_path : str):
        self.content_path : Path = Path(content_path)
        self.build_path : Path = Path(build_path)
        self.deploy_path : Path = Path(deploy_path)
        self.templates_path : Path = Path(templates_path)
    
    def build(self):
        # delete pre-existing build folder
        if self.build_path.exists() and self.build_path.is_dir():
            shutil.rmtree(self.build_path)

        for item in self.content_path.rglob("*"):
            target = self.build_path / item.relative_to(self.content_path)
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif item.suffix == ".md":
                target.parent.mkdir(parents=True, exist_ok=True)
                # output : str = parse_markdown(item)
                output : str = ParseMarkdown(item).content_html
                output_path : Path = target.parent / "index.html"
                output_path.write_text(output, encoding="utf-8")

    def deploy_path(self):
        pass

class Page:
    pass

class Tag:
    pass

class Section:
    pass