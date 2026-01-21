import threading
from pathlib import Path
from watchdog.events import FileSystemEvent, FileSystemEventHandler

class WatchDogHandler(FileSystemEventHandler):
    def __init__(self, delay : float = 0.3):
        super().__init__()
        self.delay = delay
        self._timer : threading.Timer | None = None

        self.rebuild_all : bool = False
        self.rebuild_md : set[str] = set()

        # signals
        self.on_rebuild_all : callable[[], None] | None = None
        self.on_rebuild_md : callable[[set[Path]], None] | None = None
        
        
    def _arm_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(self.delay, self.on_timeout)
        self._timer.daemon = True
        self._timer.start()

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return

        file_path : Path = Path(event.src_path)
        print("Modified file:", file_path)
        try:
            if file_path.suffix != ".md":
                self.rebuild_all = True
            else:
                self.rebuild_md.add(file_path)
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_created(self, event: FileSystemEvent) -> None:
        file_path : Path = Path(event.src_path)
        print("Created file:", file_path)
        try:
            self.rebuild_all = True
            self._arm_timer()
        except FileNotFoundError:
            return
    
    # TODO: not rebuild when creating or deleting markdown file
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        file_path : Path = Path(event.src_path)
        print("Deleted file:", file_path)
        try:
            self.rebuild_all = True
            self._arm_timer()
        except FileNotFoundError:
            return
    
    def on_moved(self, event: FileSystemEvent) -> None:
        file_path : Path = Path(event.src_path)
        print("Moved file:", file_path)
        try:
            self.rebuild_all = True
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