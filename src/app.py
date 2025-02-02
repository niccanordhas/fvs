"""
app.py
"""

import os
import subprocess
import requests
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QListWidget, QHBoxLayout, QFileDialog
from PyQt5.QtCore import Qt, QSettings

from src.thread.download import DownloadThread
from src.utils.datetime import DateTime
from src.thread.unzip import UnzipThread


class FlutterVersionSwitcher(QWidget):
    """main window class"""

    def __init__(self):
        super().__init__()
        self.settings = QSettings("FVS", "FlutterVersionSwitcher")
        self.download_path = self.settings.value("download_dir", None)
        if not self.download_path:
            self.download_path = os.path.expanduser("~/Downloads/flutter_sdk/")
            self.settings.setValue("download_dir", self.download_path)

        self.flutter_sdk_url = "https://storage.googleapis.com/flutter_infra_release/releases/releases_macos.json"

        self._init_ui()
        self._fetch_flutter_sdks()

    def _init_ui(self) -> None:
        """initialize the ui"""
        self.setWindowTitle("Flutter Version Switcher")
        self.setGeometry(100, 100, 800, 400)

        self.layout = QVBoxLayout()

        self.label = QLabel("SDK Channels:")
        self.layout.addWidget(self.label)

        self.channel_list = QListWidget()
        self.channel_list.setFixedHeight(80)
        self.channel_list.itemSelectionChanged.connect(
            self._filter_versions_by_channel)
        self.layout.addWidget(self.channel_list)

        self.version_label = QLabel("SDK Versions:")
        self.layout.addWidget(self.version_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setMinimumHeight(150)
        self.table.horizontalHeader().setFixedHeight(30)
        self.table.setHorizontalHeaderLabels(
            ["Version", "Dart Sdk Version", "Dart Sdk Arch", "Release Date", "Status"])
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.layout.addWidget(self.table)

        btns_group = QHBoxLayout()

        self.download_path_btn = QPushButton("Change Download Path")
        self.download_path_btn.clicked.connect(self._on_change_download_path)
        btns_group.addWidget(self.download_path_btn)

        self.set_default_btn = QPushButton("Set Default")
        self.set_default_btn.clicked.connect(self._on_set_default)
        btns_group.addWidget(self.set_default_btn)

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self._download_selected)
        btns_group.addWidget(self.download_btn)

        self.layout.addLayout(btns_group)

        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        self.setLayout(self.layout)

    def _fetch_flutter_sdks(self) -> None:
        """fetch the sdk data from googleapis"""
        response = requests.get(self.flutter_sdk_url, timeout=10)
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

    def _filter_versions_by_channel(self) -> None:
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
                    s = "Downloaded" if self._is_downloaded(
                        v, dsa) else "Not Downloaded"

                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)

                    self.table.setItem(row_position, 0, QTableWidgetItem(v))
                    self.table.setItem(row_position, 1, QTableWidgetItem(dsv))
                    self.table.setItem(row_position, 2, QTableWidgetItem(dsa))
                    self.table.setItem(row_position, 3, QTableWidgetItem(rd))
                    self.table.setItem(row_position, 4, QTableWidgetItem(s))

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

    def _is_downloaded(self, v: str, arch: str) -> bool:
        """verify the version is downloaded or not"""
        file_path = os.path.join(self.download_path, f"flutter_{v}_{arch}")
        return os.path.exists(file_path)

    def _on_download_completed(self, msg: str, fp: str, v: str, arch: str) -> None:
        """on download complete"""
        self.status_label.setText(msg)
        if msg == 'Download Completed':
            self.unzip_thread = UnzipThread(fp, v, arch)
            self.unzip_thread.progress.connect(self.status_label.setText)
            self.unzip_thread.completed.connect(self._on_download_completed)
            self.unzip_thread.start()
        if msg == 'Unzipping Completed':
            self._filter_versions_by_channel()

    def _on_change_download_path(self) -> None:
        """on change the download location of sdks"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", "")
        if directory:
            self.settings.setValue("download_dir", f"{directory}/")
            self.download_path = directory

    def _on_set_default(self) -> None:
        """on set the selected version to default"""
        selected_row = self.table.currentRow()
        if selected_row != 0:
            self.status_label.setText(
                "Select a version before set to default.")
        else:
            self.status_label.setText("")

            if selected_row >= 0:
                v = self.table.item(selected_row, 0).text()
                arch = self.table.item(selected_row, 2).text()
                flutter_path = os.path.join(
                        self.download_path, f"flutter_{v}_{arch}/flutter")
                
                if self._is_downloaded(v, arch):
                    home_dir = os.path.expanduser("~")

                    shell = os.environ.get("SHELL", "").lower()
                    if "zsh" in shell:
                        profile_file = ".zshrc"
                    else:
                        profile_file = ".bash_profile"

                    flutter_path = flutter_path.rstrip("/bin")
                    flutter_path_line = f'\n# Add Flutter to PATH\nexport PATH="$PATH{flutter_path}/bin:$PATH"\n'
                    profile_file_path = os.path.join(home_dir, profile_file)

                    try:
                        with open(profile_file_path, "r", encoding="utf-8") as file:
                            existing_content = file.read()

                        if flutter_path_line.strip() not in existing_content.strip():
                            with open(profile_file_path, "a", encoding="utf-8") as file:
                                file.write(flutter_path_line)
                            print(f"Flutter path added to {profile_file_path}. Please run the following command to apply changes:")
                            print(f"source {profile_file_path}")
                            print("Alternatively, you can restart your terminal session to apply the changes.")
                        else:
                            print("Flutter path is already added in the profile file.")

                    except subprocess.CalledProcessError as e:
                        print(f"Error updating {profile_file}: {e}")
                else:
                    self.status_label.setText("Flutter sdk not found.")

    def _download_selected(self) -> None:
        """download the selected version"""
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            v = self.table.item(selected_row, 0).text()
            arch = self.table.item(selected_row, 2).text()
            if self._is_downloaded(v, arch):
                self.status_label.setText("Version already downloaded.")
                return

            for release in self.releases:
                if release["version"] == v:
                    url = release["archive"]
                    full_url = f"https://storage.googleapis.com/flutter_infra_release/releases/{
                        url}"
                    file_path = os.path.join(
                        self.download_path, f"flutter_{v}_{arch}.zip")

                    self.download_thread = DownloadThread(
                        full_url, file_path, v, arch)
                    self.download_thread.progress.connect(
                        self.status_label.setText)
                    self.download_thread.completed.connect(
                        self._on_download_completed)
                    self.download_thread.start()
                    break
