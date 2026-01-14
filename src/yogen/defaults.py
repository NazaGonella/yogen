from importlib import resources
from pathlib import Path
import shutil

def build_default_files():
    root = Path.cwd()
    defaults = resources.files("yogen").joinpath("defaults")

    for item in defaults.rglob("*"):
        target = root / item.relative_to(defaults)
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copyfile(item, target)
