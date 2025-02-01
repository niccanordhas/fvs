"""
download.py
"""

import requests
import time
from PyQt5.QtCore import QThread, pyqtSignal


class DownloadThread(QThread):
    """this class used create new thread on download"""

    progress = pyqtSignal(str)
    completed = pyqtSignal(str)

    def __init__(self, url, file_path, version):
        super().__init__()
        self.url = url
        self.file_path = file_path
        self.version = version

    def run(self):
        """run"""
        response = requests.get(self.url, stream=True)
        start_time = time.time()

        if response.status_code == 200:
            with open(self.file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            elapsed_time = time.time() - start_time
            self.completed.emit(f"Download complete: {
                                self.file_path} (Time: {elapsed_time:.2f} seconds)")
        else:
            self.completed.emit("Download failed")
