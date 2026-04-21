import threading
from pathlib import Path
from watchdog.events import FileSystemEvent, FileSystemEventHandler

class WatchDogHandler(FileSystemEventHandler):
    def __init__(self, content_root : Path, delay : float = 0.3):
        super().__init__()
        self.content_root = content_root.resolve()
        self.site_root = self.content_root.parent
        self.delay = delay
        self._timer : threading.Timer | None = None

        self.rebuild_all : bool = False
        self.rebuild_md : set[Path] = set()

        # signals
        self.on_rebuild_all : callable[[], None] | None = None
        self.on_rebuild_md : callable[[set[Path]], None] | None = None
        
        
    def _arm_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self.delay, self.on_timeout)
        self._timer.daemon = True
        self._timer.start()
    
    def _classify(self, p : Path):
        p_resolved = p.resolve()
        # Partial rebuild is only for markdown files inside content/.
        # Any other change (non-.md files or directory events) triggers full rebuild.
        if p_resolved.is_relative_to(self.content_root) and p_resolved.suffix == ".md":
            # Keep markdown paths site-relative (e.g. content/home.md) so Site.rebuild_md
            # uses the same key style as normal page loading.
            self.rebuild_md.add(p_resolved.relative_to(self.site_root))
        else:
            self.rebuild_all = True

    def on_modified(self, event : FileSystemEvent) -> None:
        if event.is_directory:
            return

        file_path : Path = Path(event.src_path)
        print("Modified file:", file_path)
        try:
            self._classify(file_path)
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_created(self, event : FileSystemEvent) -> None:
        if event.is_directory:
            dir_path = Path(event.src_path)
            print("Created directory:", dir_path)
            self.rebuild_all = True
            self._arm_timer()
            return

        file_path : Path = Path(event.src_path)
        print("Created file:", file_path)
        try:
            self._classify(file_path)
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_deleted(self, event : FileSystemEvent) -> None:
        if event.is_directory:
            dir_path = Path(event.src_path)
            print("Deleted directory:", dir_path)
            self.rebuild_all = True
            self._arm_timer()
            return

        file_path : Path = Path(event.src_path)
        print("Deleted file:", file_path)
        try:
            # paths of deleted files are still added to the rebuild_md set.
            # website.py then checks if the file exists, if not (like in this case), it handles removal.
            self._classify(file_path)
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_moved(self, event : FileSystemEvent) -> None:
        if event.is_directory:
            src_path : Path = Path(event.src_path)
            dst_path : Path = Path(event.dest_path)
            print("Moved directory:", src_path, "->", dst_path)
            self.rebuild_all = True
            self._arm_timer()
            return

        src_path : Path = Path(event.src_path)
        dst_path : Path = Path(event.dest_path)
        print("Moved file:", src_path, "->", dst_path)
        try:
            self._classify(src_path)
            self._classify(dst_path)
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_timeout(self):
        if self.rebuild_all and self.on_rebuild_all:
            print("REBUILDING ALL...")
            self.on_rebuild_all()
        elif self.rebuild_md and self.on_rebuild_md:
            print("REBUILDING MD...")
            self.on_rebuild_md(self.rebuild_md)

        self.rebuild_all = False
        self.rebuild_md.clear()
        self._timer = None
