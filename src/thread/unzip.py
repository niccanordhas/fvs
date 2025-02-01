"""
unzip.py
"""


import os
import zipfile
from PyQt5.QtCore import QThread, pyqtSignal


class UnzipThread(QThread):
    """this class used create new thread on unzip"""

    progress = pyqtSignal(str)
    completed = pyqtSignal(str, str, str, str)

    def __init__(self, zip_path: str, v, arch):
        super().__init__()
        self.zip_path = zip_path
        self.extract_to = zip_path.replace('.zip', '')
        self.version = v
        self.arch = arch

    def run(self):
        """unzip the file in the background"""
        try:
            with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
                total_files = len(zip_ref.namelist())
                for index, file in enumerate(zip_ref.namelist(), start=1):
                    zip_ref.extract(file, self.extract_to)
                    progress = (index / total_files) * 100
                    self.progress.emit(f"Extracting... {progress:.2f}%")
            os.remove(self.zip_path)
            self.completed.emit("Unzipping Completed",
                                self.extract_to, self.version, self.arch)
        except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError) as e:
            self.completed.emit(
                f"Unzipping Error: {str(e)}", self.extract_to, self.version, self.arch)
