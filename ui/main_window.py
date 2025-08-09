"""
主窗口模块
包含主GUI类和所有界面逻辑
"""

import sys
import os
import json
import glob
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QGridLayout, QFileDialog, QProgressBar, QMessageBox, QColorDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QMovie

from utils.config_manager import ConfigManager
from utils.file_operations import FileOperations
from utils.version_checker import VersionChecker
from utils.workers import ExtractWorker, ImageLoadWorker, SearchIndexWorker
from ui.tabs import TabCreator


class RePKGGUI(QWidget):
    """RePKG GUI 主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yet Another RePKG-GUI")
        self.currentImagePath = None
        self.previewImages = []
        self.originalPreviewImages = []
        self.thumbnail_widgets = []
        self.search_index = []
        
        # 初始化工具类
        self.config_manager = ConfigManager()
        self.file_ops = FileOperations()
        self.version_checker = VersionChecker()
        self.tab_creator = TabCreator(self)
        
        # 分页相关属性
        self.current_page = 0
        self.items_per_page = 30
        self.total_pages = 0
        
        # 检查RePKG.exe是否存在
        self.repkg_path = self.file_ops.find_repkg_exe()
        if not self.repkg_path:
            msg = QMessageBox()
            msg.setWindowTitle('缺少RePKG.exe')
            msg.setText('未找到RePKG.exe，请确保RePKG.exe位于程序目录下。\\n是否继续运行？（仅能提取未加密的图片和视频）')
            
            # 添加GitHub按钮
            github_btn = QPushButton("GitHub")
            github_btn.clicked.connect(self.version_checker.open_github)
            
            # 添加按钮到对话框
            msg.addButton(github_btn, QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Yes)
            msg.addButton(QMessageBox.StandardButton.No)
            
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.No:
                sys.exit()
        else:
            # 检查版本
            local_version = self.version_checker.check_repkg_version(self.repkg_path)
            latest_version = self.version_checker.get_latest_repkg_version()
            
            if local_version and latest_version:
                comparison = self.version_checker.compare_versions(local_version, latest_version)
                if comparison == -1:
                    # 版本较旧，提示更新
                    msg = QMessageBox()
                    msg.setWindowTitle('RePKG版本过旧')
                    msg.setText(f'当前RePKG版本为 {local_version}，最新版本为 {latest_version}\\n建议更新到最新版本以获得更好的体验。')
                    
                    # 添加GitHub按钮
                    github_btn = QPushButton("GitHub")
                    github_btn.clicked.connect(self.version_checker.open_github)
                    
                    # 添加按钮到对话框
                    msg.addButton(github_btn, QMessageBox.ButtonRole.ActionRole)
                    msg.addButton(QMessageBox.StandardButton.Yes)
                    msg.exec()
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        # 1. 加载配置
        config = self.config_manager.load_config()
        
        # 2. 获取Steam安装路径
        steam_path = self.config_manager.get_steam_install_path()
        if steam_path:
            workshop_dir = os.path.join(steam_path, "steamapps", "workshop", "content", "431960")
            # 更新配置中的创意工坊目录
            if "workshop_dir" not in config or config["workshop_dir"] != workshop_dir:
                config["workshop_dir"] = workshop_dir
        else:
            workshop_dir = config.get("workshop_dir", r"C:\\Program Files (x86)\\Steam\\steamapps\\workshop\\content\\431960")
        
        # 3. 计算屏幕居中位置
        screen = QApplication.primaryScreen().availableGeometry()
        windowWidth, windowHeight = 950, 800
        x = (screen.width() - windowWidth) // 2
        y = (screen.height() - windowHeight) // 2
        self.setGeometry(x, y, windowWidth, windowHeight)
        self.setWindowFlags(Qt.WindowType.MSWindowsFixedSizeDialogHint)
        
        # 4. 主布局 & Tab - 先创建布局
        self.mainLayout = QGridLayout(self)
        self.tabWidget = QTabWidget()
        self.mainLayout.addWidget(self.tabWidget, 0, 0, 1, 3)
        
        # 5. 创建并添加进度条
        self.progressBar = QProgressBar()
        self.progressBar.setVisible(False)
        self.progressBar.setTextVisible(True)
        self.progressBar.setFormat("加载中... %p% (%v/%m)")
        self.mainLayout.addWidget(self.progressBar, 1, 0, 1, 3)
        
        # 6. 添加左下角页码信息标签
        self.pageLabel = QLabel("第 1 页，共 1 页")
        self.pageLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.pageLabel.setStyleSheet("color: gray; font-size: 12px; padding: 5px;")
        self.mainLayout.addWidget(self.pageLabel, 2, 0, 1, 1)
        
        # 7. 设置创意工坊目录
        self.workshopDirectory = workshop_dir
        
        # 8. 添加选项卡
        self.pkgTab = self.tab_creator.create_pkg_tab()
        self.manualTab = self.tab_creator.create_manual_tab()
        self.settingsTab = self.tab_creator.create_settings_tab()
        self.aboutTab = self.tab_creator.create_about_tab()
        
        self.tabWidget.addTab(self.pkgTab, "已安装")
        self.tabWidget.addTab(self.manualTab, "手动提取")
        self.tabWidget.addTab(self.settingsTab, "设置")
        self.tabWidget.addTab(self.aboutTab, "关于")
        
        # 9. 应用配置中的自定义设置
        if "custom_title" in config:
            self.customTitleEdit.setText(config["custom_title"])
            self.setWindowTitle(config["custom_title"])  # 应用保存的标题
        if "custom_path" in config:
            # 这里应该有一个customPathEdit，但在原代码中似乎没有实际使用
            pass
        
        # 10. 设置保存路径
        defaultSavePath = config.get("save_path", os.path.dirname(os.path.abspath(__file__)))
        self.savePathEdit.setText(defaultSavePath)
        self.savePathEdit.setPlaceholderText(f"当前: {defaultSavePath}")
        
        # 11. 遍历目录加载预览
        self.traverse_directory()
    
    # ------------------------- 配置和设置 -------------------------
    
    def save_config(self):
        """保存配置"""
        config_data = {
            "save_path": self.savePathEdit.text(),
            "workshop_dir": self.workshopDirectory,
            "custom_title": self.customTitleEdit.text()
        }
        self.config_manager.save_config(config_data)
    
    def apply_custom_title(self):
        """应用自定义标题"""
        new_title = self.customTitleEdit.text().strip()
        if new_title:
            self.setWindowTitle(new_title)
            # 保存到配置
            self.save_config()
        else:
            QMessageBox.warning(self, '警告', '标题不能为空！')
    
    def choose_background_color(self):
        """选择背景颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.setStyleSheet(f"background-color: {color.name()};")
    
    def check_update(self):
        """检查更新并显示版本信息"""
        self.versionLabel.setText("检查中...")
        QApplication.processEvents()  # 确保界面更新
        
        try:
            # 获取远端版本信息
            latest_version = self.version_checker.get_latest_repkg_version()
            if latest_version:
                self.versionLabel.setText(f"远端版本: {latest_version}\\n(检查更新功能维护中)")
            else:
                self.versionLabel.setText("获取远端版本失败\\n(检查更新功能维护中)")
        except Exception as e:
            self.versionLabel.setText("检查更新失败\\n(检查更新功能维护中)")
            print(f"检查更新出错: {e}")
    
    # ------------------------- 目录和文件处理 -------------------------
    
    def traverse_directory(self):
        """遍历目录查找预览图片"""
        print("开始查找PKG文件")
        directory = self.workshopDirectory
        if not os.path.exists(directory):
            print(f"警告：创意工坊目录不存在 - {directory}")
            return
        else:
            print(f"创意工坊目录: {directory}")

        self.previewImages = []
        entries = [e for e in os.scandir(directory) if e.is_dir()]
        for root, _, files in os.walk(directory):
            for file in files:
                if file in ['preview.jpg', 'preview.gif']:
                    self.previewImages.append(os.path.join(root, file))

        if not self.previewImages:
            print("警告：未找到任何预览图片")

        # 备份原始列表并创建搜索索引
        self.originalPreviewImages = list(self.previewImages)
        QTimer.singleShot(0, self.start_search_index_worker)

        self.load_preview_images()
    
    def load_preview_images(self):
        """加载预览图片"""
        # 清理现有缩略图
        for w in self.thumbnail_widgets:
            w.deleteLater()
        self.thumbnail_widgets.clear()
        
        # 计算总页数
        total_images = len(self.previewImages)
        self.total_pages = (total_images + self.items_per_page - 1) // self.items_per_page
        
        if self.total_pages == 0:
            self.total_pages = 1
        
        # 确保当前页在有效范围内
        if self.current_page >= self.total_pages:
            self.current_page = self.total_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        # 获取当前页的图片范围
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, total_images)
        current_page_images = self.previewImages[start_idx:end_idx]

        # 如果没有图片，直接返回
        if not current_page_images:
            self.update_page_info()
            return

        # 设置进度条
        self.progressBar.setMaximum(len(current_page_images))
        self.progressBar.setValue(0)
        self.progressBar.setVisible(True)

        # 预创建缩略图控件
        for i in range(len(current_page_images)):
            thumbnail = QLabel()
            thumbnail.setFixedSize(180, 180)
            thumbnail.setStyleSheet("border: 1px solid gray;")
            thumbnail.setText("加载中...")
            thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.thumbnailLayout.addWidget(thumbnail, i // 3, i % 3)
            self.thumbnail_widgets.append(thumbnail)

        # 启动图片加载线程
        self.loadWorker = ImageLoadWorker(current_page_images, start_idx)
        self.loadWorker.imageLoaded.connect(self.on_image_loaded)
        self.loadWorker.progressChanged.connect(self.on_progress_changed)
        self.loadWorker.finished.connect(self.on_loading_finished)
        self.loadWorker.start()
        
        # 更新分页信息显示
        self.update_page_info()
    
    def show_preview_image(self, imagePath):
        """显示预览图片"""
        self.currentImagePath = imagePath
        fileExt = os.path.splitext(imagePath)[1].lower()
        workshopID = os.path.basename(os.path.dirname(imagePath))
        self.pathLabel.setText(f"ID: {workshopID}")

        if fileExt in ['.jpg', '.jpeg']:
            pixmap = QPixmap(imagePath)
            self.previewLabel.setPixmap(pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio,
                                                     Qt.TransformationMode.SmoothTransformation))
        elif fileExt == '.gif':
            movie = QMovie(imagePath)
            if movie.isValid():
                self.previewLabel.setMovie(movie)
                movie.start()
            else:
                self.previewLabel.setText("GIF加载失败")
        else:
            self.previewLabel.setText("不支持的格式")

        # 读取project.json
        pj = os.path.join(os.path.dirname(imagePath), "project.json")
        if os.path.exists(pj):
            try:
                with open(pj, 'r', encoding='utf-8') as f:
                    self.titleLabel.setText(json.load(f).get("title", "无标题"))
            except:
                self.titleLabel.setText("[读取壁纸信息失败]")
        else:
            self.titleLabel.setText("[无project.json文件]")
    
    # ------------------------- 分页控制 -------------------------
    
    def update_page_info(self):
        """更新分页信息显示"""
        if hasattr(self, 'pageLabel'):
            page_text = f"第 {self.current_page + 1} 页，共 {self.total_pages} 页 (共 {len(self.previewImages)} 个壁纸)"
            self.pageLabel.setText(page_text)
        
        # 更新按钮状态
        if hasattr(self, 'prevBtn'):
            self.prevBtn.setEnabled(self.current_page > 0)
        if hasattr(self, 'nextBtn'):
            self.nextBtn.setEnabled(self.current_page < self.total_pages - 1)

    def go_to_previous_page(self):
        """跳转到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.load_preview_images()

    def go_to_next_page(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_preview_images()
    
    # ------------------------- 图片加载回调 -------------------------
    
    def on_image_loaded(self, index, imagePath, display_object):
        """单个图片加载完成的回调"""
        if index < len(self.thumbnail_widgets):
            thumbnail = self.thumbnail_widgets[index]
            if display_object is not None:
                thumbnail.setPixmap(display_object)
            else:
                thumbnail.setText("加载失败")
            
            # 设置点击事件
            thumbnail.mousePressEvent = lambda e, path=imagePath: self.show_preview_image(path)

    def on_progress_changed(self, current, total):
        """进度更新回调"""
        self.progressBar.setValue(current)

    def on_loading_finished(self):
        """加载完成回调"""
        self.progressBar.setVisible(False)

    # ------------------------- 搜索索引 -------------------------

    def start_search_index_worker(self):
        """启动异步搜索索引构建"""
        if hasattr(self, 'searchWorker') and self.searchWorker.isRunning():
            self.searchWorker.terminate()
        self.searchWorker = SearchIndexWorker(self.originalPreviewImages)
        self.searchWorker.indexBuilt.connect(self.on_search_index_built)
        self.searchWorker.start()

    def on_search_index_built(self, index):
        """搜索索引构建完成回调"""
        self.search_index = index

    def search_wallpapers(self, text):
        """根据标题搜索壁纸"""
        query = text.strip().lower()
        if query:
            matched = [item["path"] for item in self.search_index if query in item["title"]]
            self.previewImages = matched
        else:
            self.previewImages = list(self.originalPreviewImages)
        self.current_page = 0
        self.load_preview_images()
    
    # ------------------------- 文件选择 -------------------------
    
    def browse_save_directory(self):
        """浏览保存目录"""
        init = self.savePathEdit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "选择保存壁纸的目录", init)
        if directory:
            self.savePathEdit.setText(directory)
            self.savePathEdit.setPlaceholderText(f"当前: {directory}")
            self.save_config()

    def browse_workshop_directory(self):
        """浏览创意工坊目录"""
        init = self.workshopPathEdit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "选择Steam创意工坊目录", init)
        if directory:
            self.workshopPathEdit.setText(directory)
            self.workshopDirectory = directory
            # 重新扫描新目录
            self.traverse_directory()
            # 保存到配置
            self.save_config()

    def browse_manual_file(self):
        """浏览手动文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要提取的文件", "",
            "所有支持的文件 (*.pkg *.mp4);;PKG文件 (*.pkg);;MP4文件 (*.mp4)"
        )
        if file_path:
            self.manualPathEdit.setText(file_path)

    def browse_manual_directory(self):
        """浏览手动目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择要提取的文件夹")
        if dir_path:
            self.batchPathEdit.setText(dir_path)

    def handle_manual_drop(self, e):
        """处理手动拖放"""
        urls = e.mimeData().urls()
        if urls:
            f = urls[0].toLocalFile()
            if f.lower().endswith(('.pkg', '.mp4')):
                self.manualPathEdit.setText(f)

    def handle_batch_drop(self, e):
        """处理批量拖放"""
        urls = e.mimeData().urls()
        if urls:
            f = urls[0].toLocalFile()
            if os.path.isdir(f):
                self.batchPathEdit.setText(f)
    
    # ------------------------- 提取功能 -------------------------
    
    def extract_and_organize_files(self):
        """提取并整理文件"""
        if not self.currentImagePath:
            print("未选择壁纸")
            return

        def after_extract():
            print("开始整理文件")
            self.file_ops.organize_extracted_files(self.savePathEdit.text())
            if btn:
                btn.setText("提取并整理完成")
                btn.setEnabled(True)

        btn = self.sender()
        if btn:
            btn.setEnabled(False)
            btn.setText("提取中...")

        # 用于提取的代码块
        parent_path = os.path.dirname(self.currentImagePath)
        title = self.file_ops.get_title_from_project_json(parent_path)
        target = self.file_ops.find_target_file(parent_path)

        if not target:
            print("未找到可提取文件")
            return

        save_dir = os.path.join(self.savePathEdit.text(), title)
        os.makedirs(save_dir, exist_ok=True)

        if target.lower().endswith('.mp4') or target.lower().endswith(('.jpg', '.jpeg', '.png')):
            if self.file_ops.copy_file_to_directory(target, save_dir):
                after_extract()
            else:
                if btn:
                    btn.setText("复制失败")
                    btn.setEnabled(True)
        else:
            # 使用 RePKG 异步提取，然后连接到整理逻辑
            self.worker = ExtractWorker([self.repkg_path, "extract", target, "-o", save_dir])
            self.worker.finished.connect(after_extract)
            self.worker.error.connect(lambda msg: self.on_extract_error(btn, msg))
            self.worker.start()
    
    def extract_action(self, imagePath):
        """提取操作"""
        if not imagePath:
            return
            
        parent_path = os.path.dirname(imagePath)
        title = self.file_ops.get_title_from_project_json(parent_path)
        target = self.file_ops.find_target_file(parent_path)
        
        if not target:
            print("未找到可提取文件")
            return

        btn = self.sender()
        save_dir = os.path.join(self.savePathEdit.text(), title)
        os.makedirs(save_dir, exist_ok=True)
        
        # 根据文件类型处理
        if target.lower().endswith('.mp4') or target.lower().endswith(('.png', '.jpg', '.jpeg')):
            if self.file_ops.copy_file_to_directory(target, save_dir):
                print("文件复制完成")
                if btn:
                    btn.setText("复制完成")
            else:
                if btn:
                    btn.setText("复制失败")
        else:
            # 使用RePKG提取PKG文件
            if not self.repkg_path:
                QMessageBox.warning(self, '错误', '未找到RePKG.exe，无法进行PKG提取！')
                if btn:
                    btn.setText("RePKG.exe未找到")
                return
            
            self.worker = ExtractWorker([self.repkg_path, "extract", target, "-o", save_dir])
            self.worker.finished.connect(lambda: self.on_extract_finished(btn))
            self.worker.error.connect(lambda msg: self.on_extract_error(btn, msg))
            self.worker.start()
            if btn:
                btn.setEnabled(False)
                btn.setText("提取中...")

    def extract_single_file(self, file_path):
        """提取单个文件"""
        if not file_path or not os.path.exists(file_path):
            print("文件不存在")
            return
        
        save_dir = self.savePathEdit.text()
        if file_path.lower().endswith('.pkg'):
            save_dir = os.path.join(save_dir, os.path.splitext(os.path.basename(file_path))[0])
        os.makedirs(save_dir, exist_ok=True)

        btn = self.sender()
        
        # 如果是mp4文件，直接复制
        if file_path.lower().endswith('.mp4'):
            if self.file_ops.copy_file_to_directory(file_path, save_dir):
                print("MP4文件复制完成")
                if btn:
                    btn.setText("复制完成")
            else:
                if btn:
                    btn.setText("复制失败")
        else:
            # 处理PKG文件
            cmd = self.file_ops.get_extract_command(file_path, save_dir, self.repkg_path)
            if cmd:
                self.worker = ExtractWorker(cmd)
                self.worker.finished.connect(lambda: self.on_extract_finished(btn))
                self.worker.error.connect(lambda msg: self.on_extract_error(btn, msg))
                self.worker.start()
                if btn:
                    btn.setEnabled(False)
                    btn.setText("提取中...")
            else:
                print("不支持的文件类型")
                if btn:
                    btn.setText("不支持")

    def batch_extract(self):
        """批量提取"""
        directory = self.batchPathEdit.text()
        if not directory or not os.path.isdir(directory):
            print("无效文件夹")
            return
        
        for root, _, files in os.walk(directory):
            target_file = None
            if "scene.pkg" in files:
                target_file = os.path.join(root, "scene.pkg")
            elif any(f.lower().endswith('.mp4') for f in files):
                mp4_files = [f for f in files if f.lower().endswith('.mp4')]
                target_file = os.path.join(root, mp4_files[0])
            
            if target_file:
                self.extract_single_file(target_file)
                break
    
    def open_current_directory(self):
        """打开当前文件所在目录"""
        if hasattr(self, 'currentImagePath') and self.currentImagePath:
            import platform
            import subprocess
            
            # 获取文件所在目录
            dir_path = os.path.dirname(self.currentImagePath)
            
            # 根据操作系统打开目录
            system = platform.system()
            try:
                if system == "Windows":
                    os.startfile(dir_path)
                elif system == "Darwin":  # macOS
                    subprocess.run(["open", dir_path])
                else:  # Linux
                    subprocess.run(["xdg-open", dir_path])
            except Exception as e:
                # 如果打开失败，可以显示错误信息
                print(f"无法打开目录: {e}")
        else:
            # 如果没有选择文件，可以显示提示信息
            print("请先选择一个壁纸文件")
    
    # ------------------------- 提取回调 -------------------------

    def on_extract_finished(self, button):
        """提取完成回调"""
        if button:
            button.setEnabled(True)
            button.setText("全部提取")
        print("提取完成")

    def on_extract_error(self, button, msg):
        """提取错误回调"""
        if button:
            button.setEnabled(True)
            button.setText("全部提取")
        print(f"提取出错: {msg}")
