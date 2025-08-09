"""
工作线程模块
包含所有异步操作的线程类
"""

import os
import subprocess
import json
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QMovie


class ExtractWorker(QThread):
    """文件提取工作线程"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        try:
            subprocess.run(self.command, capture_output=True, text=True)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class ImageLoadWorker(QThread):
    """图片异步加载工作线程"""
    imageLoaded = pyqtSignal(int, str, object)  # 索引、路径、QPixmap或QMovie
    progressChanged = pyqtSignal(int, int)  # 当前进度、总数
    finished = pyqtSignal()

    def __init__(self, image_paths, start_idx):
        super().__init__()
        self.image_paths = image_paths
        self.start_idx = start_idx

    def run(self):
        for i, imagePath in enumerate(self.image_paths):
            fileExt = os.path.splitext(imagePath)[1].lower()
            display_object = None

            if fileExt in ['.jpg', '.jpeg']:
                pixmap = QPixmap(imagePath)
                display_object = pixmap.scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            elif fileExt == '.gif':
                movie = QMovie(imagePath)
                if movie.isValid():
                    movie.jumpToFrame(0)
                    display_object = movie.currentPixmap().scaled(
                        180, 180, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation)

            self.imageLoaded.emit(i, imagePath, display_object)
            self.progressChanged.emit(i + 1, len(self.image_paths))

        self.finished.emit()


class SearchIndexWorker(QThread):
    """异步创建搜索索引的工作线程"""
    indexBuilt = pyqtSignal(list)

    def __init__(self, image_paths):
        super().__init__()
        self.image_paths = image_paths

    def run(self):
        index = []
        for image_path in self.image_paths:
            title = ""
            pj = os.path.join(os.path.dirname(image_path), "project.json")
            if os.path.exists(pj):
                try:
                    with open(pj, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        title = data.get("title", "")
                except Exception:
                    pass
            index.append({"title": title.lower(), "path": image_path})
        self.indexBuilt.emit(index)
