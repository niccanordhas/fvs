"""
download.py
"""

import requests
from PyQt5.QtCore import QThread, pyqtSignal


class DownloadThread(QThread):
    """this class used create new thread on download"""

    progress = pyqtSignal(str)
    completed = pyqtSignal(str, str, str, str)

    def __init__(self, url, file_path, v, arch):
        super().__init__()
        self.url = url
        self.file_path = file_path
        self.version = v
        self.arch = arch

    def run(self):
        """downlod the file in the background"""
        response = requests.get(self.url, stream=True, timeout=50)
        total_length = response.headers.get('content-length')

        if response.status_code == 200:
            with open(self.file_path, "wb") as file:
                if total_length is None:
                    file.write(response.content)
                    self.progress.emit(f"{100}")
                else:
                    dl = 0
                    total_length = int(total_length)
                    for chunk in response.iter_content(8192):
                        dl += len(chunk)
                        file.write(chunk)
                        progress = int(50 * dl / total_length)
                        self.progress.emit(f"Downloading... {progress}%")

            self.completed.emit("Download Completed", self.file_path,
                                self.version, self.arch)
        else:
            self.completed.emit("Download Failed", self.file_path,
                                self.version, self.arch)
