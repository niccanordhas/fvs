"""
app.py
"""

import os
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QListWidget
from PyQt5.QtCore import Qt

from src.thread.download import DownloadThread
from src.utils.datetime import DateTime


class FlutterVersionSwitcher(QWidget):
    """main window class"""

    def __init__(self):
        super().__init__()
        self.flutter_sdk_url = "https://storage.googleapis.com/flutter_infra_release/releases/releases_macos.json"
        self.download_path = os.path.expanduser("~/Downloads/flutter_sdk/")

        self.init_ui()
        self.loadFlutterSDKs()

    def init_ui(self):
        """initialize the ui"""
        self.setWindowTitle("Flutter Version Switcher")
        self.setGeometry(100, 100, 800, 400)

        self.layout = QVBoxLayout()

        self.label = QLabel("SDK Channels:")
        self.layout.addWidget(self.label)

        self.channel_list = QListWidget()
        self.channel_list.itemSelectionChanged.connect(
            self.filterVersionsByChannel)
        self.layout.addWidget(self.channel_list)

        self.version_label = QLabel("Available Flutter SDK Versions:")
        self.layout.addWidget(self.version_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.horizontalHeader().setFixedHeight(30)
        self.table.setHorizontalHeaderLabels(
            ["Version", "Dart Sdk Version", "Dart Sdk Arch", "Release Date", "Status"])
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.layout.addWidget(self.table)

        self.download_btn = QPushButton("Download Selected")
        self.download_btn.clicked.connect(self.downloadSelected)
        self.layout.addWidget(self.download_btn)

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def loadFlutterSDKs(self):
        """fetch the sdk data from googleapis"""
        response = requests.get(self.flutter_sdk_url)
        if response.status_code == 200:
            data = response.json()
            self.releases = data.get("releases", [])
            self.channels = set()

            for release in self.releases:
                self.channels.add(release["channel"])

            for channel in sorted(self.channels):
                self.channel_list.addItem(channel.capitalize())
        else:
            self.status_label.setText("Failed to fetch SDK versions")

    def filterVersionsByChannel(self):
        """filter the version by channel"""
        self.table.setRowCount(0)
        selected_channel = self.channel_list.currentItem()

        if selected_channel:
            selected_channel = selected_channel.text().lower()

            for release in self.releases:
                if release["channel"] == selected_channel:
                    v = release["version"]
                    dsv = release.get("dart_sdk_version", "")
                    dsa = release.get("dart_sdk_arch", "")
                    rd = DateTime().to_local(release.get("release_date", ""))
                    download_status = "Downloaded" if self.isDownloaded(
                        v) else "Not Downloaded"

                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)

                    # Insert items into the table
                    self.table.setItem(row_position, 0, QTableWidgetItem(v))
                    self.table.setItem(row_position, 1, QTableWidgetItem(dsv))
                    self.table.setItem(row_position, 2, QTableWidgetItem(dsa))
                    self.table.setItem(row_position, 3, QTableWidgetItem(rd))

        self.table.resizeColumnsToContents()

        row_header = self.table.verticalHeader()
        column_header = self.table.horizontalHeader()
        if column_header:
            column_header.setSectionsClickable(False)
            column_header.setSelectionMode(
                QTableWidget.SelectionMode.NoSelection)
        if row_header:
            row_header.setVisible(False)
            row_header.setDefaultAlignment(Qt.AlignmentFlag.AlignHCenter)
            row_header.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

    def isDownloaded(self, version):
        """verify the version is downloaded or not"""
        file_path = os.path.join(self.download_path, f"flutter_{version}.zip")
        return os.path.exists(file_path)

    def downloadSelected(self):
        """download the selected version"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            version = self.table.item(selected_row, 0).text()
            if self.isDownloaded(version):
                self.status_label.setText("Version already downloaded.")
                return

            for release in self.releases:
                if release["version"] == version:
                    url = release["archive"]
                    full_url = f"https://storage.googleapis.com/flutter_infra_release/releases/{
                        url}"
                    file_path = os.path.join(
                        self.download_path, f"flutter_{version}.zip")

                    self.downloadThread = DownloadThread(
                        full_url, file_path, version)
                    self.downloadThread.progress.connect(
                        self.status_label.setText)
                    self.downloadThread.completed.connect(
                        self.downloadCompleted)
                    self.downloadThread.start()
                    break

    def downloadCompleted(self, message):
        """on download complete"""
        self.status_label.setText(message)
        self.filterVersionsByChannel()  # Refresh the table to show updated status
