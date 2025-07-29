"""
RePKG GUI 重构版
- 配置/工具函数 -> 事件处理 -> 提取逻辑 -> UI 构建 -> 主程序
- 缩略图预览、提取命令生成、配置管理
- 更多功能还在学说是
"""

import sys, os, json, glob, subprocess, re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QTabWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QGridLayout, QScrollArea, QFrame, QFileDialog, QProgressBar
)

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QMovie

# ------------------------- 工具类 -------------------------

class ExtractWorker(QThread):
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


# ------------------------- 异步加载 --------------------------

class ImageLoadWorker(QThread):
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

# ------------------------- 主 GUI 类 -------------------------

class RePKG_GUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yet Another RePKG-GUI")
        self.currentImagePath = None
        self.previewImages = []
        self.thumbnail_widgets = []
        

        # 检查RePKG.exe是否存在
        self.repkg_path = self.findRePKGExe()
        if not self.repkg_path:
            from PyQt6.QtWidgets import QMessageBox, QPushButton
            msg = QMessageBox()
            msg.setWindowTitle('缺少RePKG.exe')
            msg.setText('未找到RePKG.exe，请确保RePKG.exe位于程序目录下。\n是否继续运行？（仅能提取未加密的图片和视频）')
            
            # 添加GitHub按钮
            github_btn = QPushButton("GitHub")
            github_btn.clicked.connect(self.openGithub)
            
            # 添加按钮到对话框
            msg.addButton(github_btn, QMessageBox.ButtonRole.ActionRole)
            msg.addButton(QMessageBox.StandardButton.Yes)
            msg.addButton(QMessageBox.StandardButton.No)
            
            reply = msg.exec()
            if reply == QMessageBox.StandardButton.No:
                sys.exit()
        else:
            # 检查版本
            local_version = self.checkRePKGVersion()
            latest_version = self.getLatestRePKGVersion()
            
            if local_version and latest_version:
                comparison = self.compareVersions(local_version, latest_version)
                if comparison == -1:
                    # 版本较旧，提示更新
                    from PyQt6.QtWidgets import QMessageBox, QPushButton
                    msg = QMessageBox()
                    msg.setWindowTitle('RePKG版本过旧')
                    msg.setText(f'当前RePKG版本为 {local_version}，最新版本为 {latest_version}\n建议更新到最新版本以获得更好的体验。')
                    
                    # 添加GitHub按钮
                    github_btn = QPushButton("GitHub")
                    github_btn.clicked.connect(self.openGithub)
                    
                    # 添加按钮到对话框
                    msg.addButton(github_btn, QMessageBox.ButtonRole.ActionRole)
                    msg.addButton(QMessageBox.StandardButton.Yes)
                    msg.exec()


        # 添加分页相关属性
        self.current_page = 0
        self.items_per_page = 30
        self.total_pages = 0        

        # 1. 加载配置
        config = self.loadConfig()

        # 2. 获取Steam安装路径
        steam_path = self.getSteamInstallPath()
        if steam_path:
            workshop_dir = os.path.join(steam_path, "steamapps", "workshop", "content", "431960")
            # 更新配置中的创意工坊目录
            if "workshop_dir" not in config or config["workshop_dir"] != workshop_dir:
                config["workshop_dir"] = workshop_dir
        else:
            workshop_dir = config.get("workshop_dir", r"C:\Program Files (x86)\Steam\steamapps\workshop\content\431960")

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

        # 6. 设置创意工坊目录
        self.workshopDirectory = workshop_dir

        # 7. 添加选项卡
        self.pkgTab = self.createPKGTab()
        self.manualTab = self.createManualTab()
        self.settingsTab = self.createSettingsTab()
        self.tabWidget.addTab(self.pkgTab, "已安装")
        self.tabWidget.addTab(self.manualTab, "手动提取")
        self.tabWidget.addTab(self.settingsTab, "设置")

        # 8. 设置保存路径
        defaultSavePath = config.get("save_path", os.path.dirname(os.path.abspath(__file__)))
        self.savePathEdit.setText(defaultSavePath)
        self.savePathEdit.setPlaceholderText(f"当前: {defaultSavePath}")

        # 9. 遍历目录加载预览
        self.traverseDirectory()

    # ------------------------- 环境检查 -------------------------

    def getSteamInstallPath(self):
        """通过注册表获取Steam安装路径"""
        import winreg
        
        try:
            # 打开Steam的注册表项
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                # 读取InstallPath值
                install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                return install_path
        except WindowsError:
            # 如果在注册表中找不到，尝试从默认路径查找
            default_paths = [
                r"C:\Program Files (x86)\Steam",
                r"C:\Program Files\Steam",
                r"D:\Program Files (x86)\Steam",
                r"D:\Program Files\Steam"
            ]
            for path in default_paths:
                if os.path.exists(os.path.join(path, "steam.exe")):
                    return path
            return None

    def findRePKGExe(self):
        """查找RePKG.exe的位置"""
        # 首先在程序所在目录查找
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            exe_dir = sys._MEIPASS
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        repkg_path = os.path.join(exe_dir, 'RePKG.exe')
        if os.path.exists(repkg_path):
            return repkg_path
        
        # 如果没找到，返回None
        return None


    # ------------------------- 配置管理 -------------------------

    def getConfigPath(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

    def loadConfig(self):
        path = self.getConfigPath()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        return {"save_path": os.path.dirname(os.path.abspath(__file__))}

    def saveConfig(self):
        path = self.getConfigPath()
        config_data = {
            "save_path": self.savePathEdit.text(),
            "workshop_dir": self.workshopDirectory
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")


    # ------------------------- UI/事件逻辑 -------------------------

    def createSettingsTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加检查更新按钮
        update_check_layout = QHBoxLayout()
        update_check_layout.addWidget(QLabel("RePKG版本检查"))
        self.versionLabel = QLabel("未检查")
        self.versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.versionLabel.setStyleSheet("color: gray;")
        checkUpdateBtn = QPushButton("检查远端版本")
        checkUpdateBtn.clicked.connect(self.checkUpdate)
        update_check_layout.addWidget(self.versionLabel)
        update_check_layout.addWidget(checkUpdateBtn)
        layout.addLayout(update_check_layout)

        # 添加GitHub按钮
        github_layout = QHBoxLayout()
        github_btn = QPushButton("访问GitHub")
        github_btn.clicked.connect(self.openGithub)
        github_layout.addWidget(github_btn)
        layout.addLayout(github_layout)
        
        layout.addStretch()
        return tab


    def checkUpdate(self):
        """检查更新并显示版本信息"""
        self.versionLabel.setText("检查中...")
        QApplication.processEvents()  # 确保界面更新
        
        try:
            # 获取远端版本信息
            latest_version = self.getLatestRePKGVersion()
            if latest_version:
                self.versionLabel.setText(f"远端版本: {latest_version}\n(检查更新功能维护中)")
            else:
                self.versionLabel.setText("获取远端版本失败\n(检查更新功能维护中)")
        except Exception as e:
            self.versionLabel.setText("检查更新失败\n(检查更新功能维护中)")
            print(f"检查更新出错: {e}")


    def checkRePKGVersion(self):
        """检查RePKG版本"""
        try:
            # 获取本地RePKG版本
            if not self.repkg_path:
                return "未安装"
                
            result = subprocess.run([self.repkg_path, "--version"], 
                                capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                local_version = result.stdout.strip()
                return local_version
        except Exception as e:
            print(f"检查RePKG版本失败: {e}")
        return "未安装"

    def getLatestRePKGVersion(self):
        """获取最新RePKG版本"""
        try:
            import requests
            response = requests.get("https://api.github.com/repos/notscuffed/repkg/releases/latest", timeout=10)
            if response.status_code == 200:
                return response.json()["tag_name"]
        except Exception as e:
            print(f"获取最新RePKG版本失败: {e}")
        return None
    
    def compareVersions(self, local_version, latest_version):
        """比较版本号"""
        try:
            # 如果任一版本号为空，返回-1表示需要更新
            if not local_version or not latest_version:
                return -1
                
            # 移除 'v' 前缀（如果存在）
            local = local_version.lstrip('v')
            latest = latest_version.lstrip('v')
            
            # 分割版本号和附加信息
            local_main = local.split('+')[0].split('-')[0]
            latest_main = latest.split('+')[0].split('-')[0]
            
            # 分割版本号
            local_parts = local_main.split('.')
            latest_parts = latest_main.split('.')
            
            # 比较每个部分
            for i in range(max(len(local_parts), len(latest_parts))):
                local_part = local_parts[i] if i < len(local_parts) else '0'
                latest_part = latest_parts[i] if i < len(latest_parts) else '0'
                
                # 尝试转换为整数进行比较
                try:
                    local_num = int(local_part)
                    latest_num = int(latest_part)
                except ValueError:
                    # 如果转换失败，按字符串比较
                    if local_part < latest_part:
                        return -1
                    elif local_part > latest_part:
                        return 1
                    continue
                    
                if local_num < latest_num:
                    return -1
                elif local_num > latest_num:
                    return 1
                
            return 0
        except Exception as e:
            print(f"版本比较失败: {e}")
            return -1  # 发生错误时默认返回需要更新

    def openGithub(self):
        """打开GitHub页面"""
        import webbrowser
        webbrowser.open('https://github.com/notscuffed/repkg/releases')

    def traverseDirectory(self):
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

        self.loadPreviewImages()

    def showPreviewImage(self, imagePath):
        """统一处理预览显示"""
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


    def onImageLoaded(self, index, imagePath, display_object):
        """单个图片加载完成的回调，异步加载函数"""
        if index < len(self.thumbnail_widgets):
            thumbnail = self.thumbnail_widgets[index]
            if display_object is not None:
                thumbnail.setPixmap(display_object)
            else:
                thumbnail.setText("加载失败")
            
            # 设置点击事件
            thumbnail.mousePressEvent = lambda e, path=imagePath: self.showPreviewImage(path)

    def onProgressChanged(self, current, total):
        """进度更新回调"""
        self.progressBar.setValue(current)

    def onLoadingFinished(self):
        """加载完成回调"""
        self.progressBar.setVisible(False)

    def loadPreviewImages(self):
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
            self.updatePageInfo()
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
        self.loadWorker.imageLoaded.connect(self.onImageLoaded)
        self.loadWorker.progressChanged.connect(self.onProgressChanged)
        self.loadWorker.finished.connect(self.onLoadingFinished)
        self.loadWorker.start()
        
        # 更新分页信息显示
        self.updatePageInfo()

    def updatePageInfo(self):
        """更新分页信息显示"""
        if hasattr(self, 'pageLabel'):
            page_text = f"第 {self.current_page + 1} 页，共 {self.total_pages} 页 (共 {len(self.previewImages)} 个壁纸)"
            self.pageLabel.setText(page_text)
        
        # 更新按钮状态
        if hasattr(self, 'prevBtn'):
            self.prevBtn.setEnabled(self.current_page > 0)
        if hasattr(self, 'nextBtn'):
            self.nextBtn.setEnabled(self.current_page < self.total_pages - 1)

    def goToPreviousPage(self):
        """跳转到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.loadPreviewImages()

    def goToNextPage(self):
        """跳转到下一页"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.loadPreviewImages()

    # ------------------------- 文件选择 -------------------------

    def browse_save_directory(self):
        init = self.savePathEdit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "选择保存壁纸的目录", init)
        if directory:
            self.savePathEdit.setText(directory)
            self.savePathEdit.setPlaceholderText(f"当前: {directory}")
            self.saveConfig()

    def browse_workshop_directory(self):
        init = self.workshopPathEdit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(self, "选择Steam创意工坊目录", init)
        if directory:
            self.workshopPathEdit.setText(directory)
            self.workshopDirectory = directory
            # 重新扫描新目录
            self.traverseDirectory()
            # 保存到配置
            self.saveConfig()


    def browse_manual_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要提取的文件", "",
            "所有支持的文件 (*.pkg *.mp4);;PKG文件 (*.pkg);;MP4文件 (*.mp4)"
        )
        if file_path:
            self.manualPathEdit.setText(file_path)

    def browse_manual_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择要提取的文件夹")
        if dir_path:
            self.batchPathEdit.setText(dir_path)

    def handleManualDrop(self, e):
        urls = e.mimeData().urls()
        if urls:
            f = urls[0].toLocalFile()
            if f.endswith(('.pkg', '.mp4')):
                self.manualPathEdit.setText(f)

    def handleBatchDrop(self, e):
        urls = e.mimeData().urls()
        if urls:
            f = urls[0].toLocalFile()
            if os.path.isdir(f):
                self.batchPathEdit.setText(f)

    # ------------------------- 提取逻辑 -------------------------

    def getExtractCommand(self, file_path, save_directory):
        if file_path.endswith('.pkg'):
            if not self.repkg_path:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, '错误', '未找到RePKG.exe，无法进行PKG提取！')
                return None
            return [self.repkg_path, "extract", file_path, "-o", save_directory]
        elif file_path.endswith('.mp4') or file_path.endswith(('.jpg', '.jpeg', '.png')):
            return None
        return None

    def extractAction(self, imagePath):
        if not imagePath:
            return
            
        parent_path = os.path.dirname(imagePath)
        pj = os.path.join(parent_path, "project.json")
        title = "Untitled"
        if os.path.exists(pj):
            try:
                title = json.load(open(pj, 'r', encoding='utf-8')).get("title", "Untitled")
                title = re.sub(r'[<>:"/\\|?*]', '', title) or "Untitled"
            except:
                pass

        # 按优先级查找文件：scene.pkg -> mp4 -> 图片文件
        scene_pkg = os.path.join(parent_path, "scene.pkg")
        mp4_files = glob.glob(os.path.join(parent_path, "*.mp4"))
        image_files = glob.glob(os.path.join(parent_path, "*.jpg")) + \
                    glob.glob(os.path.join(parent_path, "*.jpeg")) + \
                    glob.glob(os.path.join(parent_path, "*.png"))
        
        target = None
        if os.path.exists(scene_pkg):
            target = scene_pkg
        elif mp4_files:
            target = mp4_files[0]
        elif image_files:
            target = image_files[0]
        
        if not target:
            print("未找到可提取文件")
            return

        btn = self.sender()
        
        # 根据文件类型处理
        if target.endswith('.mp4'):
            # 只有在确定要进行复制时才创建文件夹
            save_dir = os.path.join(self.savePathEdit.text(), title)
            os.makedirs(save_dir, exist_ok=True)
            import shutil
            try:
                filename = os.path.basename(target)
                target_path = os.path.join(save_dir, filename)
                shutil.copy2(target, target_path)
                print("MP4文件复制完成")
                if btn:
                    btn.setText("复制完成")
            except Exception as e:
                print(f"复制失败: {e}")
                if btn:
                    btn.setText("复制失败")
        elif target.endswith(('.png', '.jpg', '.jpeg')):
            # 只有在确定要进行复制时才创建文件夹
            save_dir = os.path.join(self.savePathEdit.text(), title)
            os.makedirs(save_dir, exist_ok=True)
            import shutil
            try:
                filename = os.path.basename(target)
                target_path = os.path.join(save_dir, filename)
                shutil.copy2(target, target_path)
                print("图片文件复制完成")
                if btn:
                    btn.setText("复制完成")
            except Exception as e:
                print(f"复制失败: {e}")
                if btn:
                    btn.setText("复制失败")
        else:
            # 使用RePKG提取PKG文件
            if not self.repkg_path:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, '错误', '未找到RePKG.exe，无法进行PKG提取！')
                if btn:
                    btn.setText("RePKG.exe未找到")
                return
            
            # 只有在确认可以进行提取时才创建文件夹
            save_dir = os.path.join(self.savePathEdit.text(), title)
            os.makedirs(save_dir, exist_ok=True)
            
            self.worker = ExtractWorker([self.repkg_path, "extract", target, "-o", save_dir])
            self.worker.finished.connect(lambda: self.on_extract_finished(btn))
            self.worker.error.connect(lambda msg: self.on_extract_error(btn, msg))
            self.worker.start()
            if btn:
                btn.setEnabled(False)
                btn.setText("提取中...")

    def extract_single_file(self, file_path):
        if not file_path or not os.path.exists(file_path):
            print("文件不存在")
            return
        
        save_dir = self.savePathEdit.text()
        if file_path.endswith('.pkg'):
            save_dir = os.path.join(save_dir, os.path.splitext(os.path.basename(file_path))[0])
        os.makedirs(save_dir, exist_ok=True)

        btn = self.sender()
        
        # 如果是mp4文件，直接复制
        if file_path.endswith('.mp4'):
            import shutil
            try:
                filename = os.path.basename(file_path)
                target_path = os.path.join(save_dir, filename)
                shutil.copy2(file_path, target_path)
                print("MP4文件复制完成")
                if btn:
                    btn.setText("复制完成")
            except Exception as e:
                print(f"复制失败: {e}")
                if btn:
                    btn.setText("复制失败")
        else:
            # 处理PKG文件
            cmd = self.getExtractCommand(file_path, save_dir)
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
        directory = self.batchPathEdit.text()
        if not directory or not os.path.isdir(directory):
            print("无效文件夹")
            return
        
        for root, _, files in os.walk(directory):
            target_file = None
            if "scene.pkg" in files:
                target_file = os.path.join(root, "scene.pkg")
            elif any(f.endswith('.mp4') for f in files):
                mp4_files = [f for f in files if f.endswith('.mp4')]
                target_file = os.path.join(root, mp4_files[0])
            
            if target_file:
                self.extract_single_file(target_file)
                break

    # ------------------------- 按钮功能 -------------------------
    def openCurrentDirectory(self):
        """打开当前文件所在目录"""
        if hasattr(self, 'currentImagePath') and self.currentImagePath:
            import os
            import subprocess
            import platform
            
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
        if button:
            button.setEnabled(True)
            button.setText("全部提取")
        print("提取完成")

    def on_extract_error(self, button, msg):
        if button:
            button.setEnabled(True)
            button.setText("全部提取")
        print(f"提取出错: {msg}")

    # ------------------------- Tab 构建 -------------------------

    def createPKGTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 保存路径选择
        saveLayout = QHBoxLayout()
        saveLayout.addWidget(QLabel("保存到"))
        self.savePathEdit = QLineEdit()
        browseButton = QPushButton("浏览")
        browseButton.clicked.connect(self.browse_save_directory)
        saveLayout.addWidget(self.savePathEdit)
        saveLayout.addWidget(browseButton)
        layout.addLayout(saveLayout)

        # 创意工坊目录选择
        workshopLayout = QHBoxLayout()
        workshopLayout.addWidget(QLabel("创意工坊目录"))
        self.workshopPathEdit = QLineEdit()
        self.workshopPathEdit.setText(self.workshopDirectory)
        self.workshopPathEdit.setPlaceholderText("Steam创意工坊目录路径")
        workshopBrowseButton = QPushButton("浏览")
        workshopBrowseButton.clicked.connect(self.browse_workshop_directory)
        workshopLayout.addWidget(self.workshopPathEdit)
        workshopLayout.addWidget(workshopBrowseButton)
        layout.addLayout(workshopLayout)

        # 主内容区域
        mainContent = QHBoxLayout()

        # 缩略图区域
        thumbArea = QScrollArea()
        thumbArea.setWidgetResizable(True)
        thumbContainer = QWidget()
        self.thumbnailLayout = QGridLayout(thumbContainer)
        thumbArea.setWidget(thumbContainer)

        # 右侧预览区
        rightPanel = QWidget()
        rightPanel.setFixedWidth(300)
        rightLayout = QVBoxLayout(rightPanel)
        self.previewLabel = QLabel("[就绪]")
        self.previewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previewLabel.setFixedSize(280, 280)
        self.previewLabel.setStyleSheet("border: 2px solid #555;")

        self.titleLabel = QLabel("[选取一个壁纸来查看]")
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pathLabel = QLabel("[选取一个壁纸来查看]")
        self.pathLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        extractAllBtn = QPushButton("全部提取")
        extractAllBtn.clicked.connect(lambda: self.extractAction(self.currentImagePath))

        openDirBtn = QPushButton("打开目录")
        openDirBtn.clicked.connect(self.openCurrentDirectory)

        # 分页控件
        pageControlLayout = QHBoxLayout()
        self.prevBtn = QPushButton("上一页")
        self.prevBtn.clicked.connect(self.goToPreviousPage)
        self.nextBtn = QPushButton("下一页") 
        self.nextBtn.clicked.connect(self.goToNextPage)
        self.pageLabel = QLabel("第 1 页，共 1 页")
        self.pageLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pageControlLayout.addWidget(self.prevBtn)
        pageControlLayout.addWidget(self.pageLabel)
        pageControlLayout.addWidget(self.nextBtn)

        # 将分页控件添加到主布局中（在缩略图区域下方）
        layout.addLayout(pageControlLayout)

        rightLayout.addWidget(self.previewLabel)
        rightLayout.addWidget(self.titleLabel)
        rightLayout.addWidget(self.pathLabel)
        rightLayout.addWidget(extractAllBtn)
        rightLayout.addWidget(openDirBtn)
        rightLayout.addStretch(1)

        mainContent.addWidget(thumbArea, 7)
        mainContent.addWidget(rightPanel, 2)
        layout.addLayout(mainContent)
        return tab

    def createManualTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 单个提取卡片
        singleCard = QFrame(); singleCard.setFrameStyle(QFrame.Shape.Box)
        singleLayout = QVBoxLayout(singleCard)
        singleLayout.addWidget(QLabel("单个提取"))
        self.manualPathEdit = QLineEdit(); self.manualPathEdit.setPlaceholderText("拖拽文件或点击浏览")
        self.manualPathEdit.setAcceptDrops(True)
        self.manualPathEdit.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasUrls() else e.ignore()
        self.manualPathEdit.dropEvent = self.handleManualDrop
        browseSingle = QPushButton("浏览"); browseSingle.clicked.connect(self.browse_manual_file)
        btnLayout = QHBoxLayout(); btnLayout.addWidget(self.manualPathEdit); btnLayout.addWidget(browseSingle)
        singleLayout.addLayout(btnLayout)
        extractSingle = QPushButton("提取"); extractSingle.clicked.connect(lambda: self.extract_single_file(self.manualPathEdit.text()))
        singleLayout.addWidget(extractSingle)

        # 批量提取卡片
        batchCard = QFrame(); batchCard.setFrameStyle(QFrame.Shape.Box)
        batchLayout = QVBoxLayout(batchCard)
        batchLayout.addWidget(QLabel("批量提取"))
        self.batchPathEdit = QLineEdit(); self.batchPathEdit.setPlaceholderText("拖拽文件夹或点击浏览")
        self.batchPathEdit.setAcceptDrops(True)
        self.batchPathEdit.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasUrls() else e.ignore()
        self.batchPathEdit.dropEvent = self.handleBatchDrop
        browseBatch = QPushButton("浏览"); browseBatch.clicked.connect(self.browse_manual_directory)
        bLayout = QHBoxLayout(); bLayout.addWidget(self.batchPathEdit); bLayout.addWidget(browseBatch)
        batchLayout.addLayout(bLayout)
        batchBtn = QPushButton("开始批量提取"); batchBtn.clicked.connect(self.batch_extract)
        batchLayout.addWidget(batchBtn)

        layout.addWidget(singleCard)
        layout.addWidget(batchCard)
        layout.addStretch()
        return tab
    

# ------------------------- 主程序 -------------------------
def main():
    app = QApplication(sys.argv)
    gui = RePKG_GUI(); gui.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
