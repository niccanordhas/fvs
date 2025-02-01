import sys
import os
import requests
import time
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal

FLUTTER_SDK_URL = "https://storage.googleapis.com/flutter_infra_release/releases/releases_macos.json"
DOWNLOAD_PATH = os.path.expanduser("~/Downloads/flutter_sdk/")

class DownloadThread(QThread):
    progress = pyqtSignal(str)
    completed = pyqtSignal(str)
    
    def __init__(self, url, file_path, version):
        super().__init__()
        self.url = url
        self.file_path = file_path
        self.version = version
    
    def run(self):
        response = requests.get(self.url, stream=True)
        start_time = time.time()
        
        if response.status_code == 200:
            with open(self.file_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            elapsed_time = time.time() - start_time
            self.completed.emit(f"Download complete: {self.file_path} (Time: {elapsed_time:.2f} seconds)")
        else:
            self.completed.emit("Download failed")

class FlutterSDKDownloader(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.loadFlutterSDKs()

    def initUI(self):
        self.setWindowTitle("Flutter SDK Downloader")
        self.setGeometry(100, 100, 500, 400)

        self.layout = QVBoxLayout()

        self.label = QLabel("Available Flutter SDK Channels:")
        self.layout.addWidget(self.label)

        self.channelListWidget = QListWidget()
        self.channelListWidget.itemSelectionChanged.connect(self.filterVersionsByChannel)
        self.layout.addWidget(self.channelListWidget)

        self.versionLabel = QLabel("Available Flutter SDK Versions:")
        self.layout.addWidget(self.versionLabel)

        self.listWidget = QListWidget()
        self.layout.addWidget(self.listWidget)

        self.downloadButton = QPushButton("Download Selected")
        self.downloadButton.clicked.connect(self.downloadSelected)
        self.layout.addWidget(self.downloadButton)

        self.statusLabel = QLabel("")
        self.layout.addWidget(self.statusLabel)

        self.setLayout(self.layout)

    def loadFlutterSDKs(self):
        response = requests.get(FLUTTER_SDK_URL)
        if response.status_code == 200:
            data = response.json()
            self.releases = data.get("releases", [])
            self.channels = set()
            
            for release in self.releases:
                self.channels.add(release["channel"])
            
            for channel in sorted(self.channels):
                self.channelListWidget.addItem(channel.capitalize())
        else:
            self.statusLabel.setText("Failed to fetch SDK versions")

    def filterVersionsByChannel(self):
        self.listWidget.clear()
        selected_channel = self.channelListWidget.currentItem()
        if selected_channel:
            selected_channel = selected_channel.text().lower()
            for release in self.releases:
                if release["channel"] == selected_channel:
                    version = release["version"]
                    if self.isDownloaded(version):
                        version += " (Downloaded)"
                    self.listWidget.addItem(version)

    def isDownloaded(self, version):
        file_path = os.path.join(DOWNLOAD_PATH, f"flutter_{version}.zip")
        return os.path.exists(file_path)

    def downloadSelected(self):
        selected_item = self.listWidget.currentItem()
        if selected_item:
            version = selected_item.text().replace(" (Downloaded)", "")
            if self.isDownloaded(version):
                self.statusLabel.setText("Version already downloaded.")
                return
            
            for release in self.releases:
                if release["version"] == version:
                    url = release["archive"]
                    full_url = f"https://storage.googleapis.com/flutter_infra_release/releases/{url}"
                    file_path = os.path.join(DOWNLOAD_PATH, f"flutter_{version}.zip")
                    
                    self.downloadThread = DownloadThread(full_url, file_path, version)
                    self.downloadThread.progress.connect(self.statusLabel.setText)
                    self.downloadThread.completed.connect(self.downloadCompleted)
                    self.downloadThread.start()
                    break

    def downloadCompleted(self, message):
        self.statusLabel.setText(message)
        self.filterVersionsByChannel()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FlutterSDKDownloader()
    window.show()
    sys.exit(app.exec_())
