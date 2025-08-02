"""
UI标签页模块
创建和管理各个功能标签页
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QHBoxLayout, QGridLayout, QScrollArea, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt


class TabCreator:
    """标签页创建器"""
    
    def __init__(self, parent):
        self.parent = parent
    
    def create_pkg_tab(self):
        """创建PKG标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 保存路径选择
        saveLayout = QHBoxLayout()
        saveLayout.addWidget(QLabel("保存到"))
        self.parent.savePathEdit = QLineEdit()
        browseButton = QPushButton("浏览")
        browseButton.clicked.connect(self.parent.browse_save_directory)
        saveLayout.addWidget(self.parent.savePathEdit)
        saveLayout.addWidget(browseButton)
        layout.addLayout(saveLayout)

        # 创意工坊目录选择
        workshopLayout = QHBoxLayout()
        workshopLayout.addWidget(QLabel("创意工坊目录"))
        self.parent.workshopPathEdit = QLineEdit()
        self.parent.workshopPathEdit.setText(self.parent.workshopDirectory)
        self.parent.workshopPathEdit.setPlaceholderText("Steam创意工坊目录路径")
        workshopBrowseButton = QPushButton("浏览")
        workshopBrowseButton.clicked.connect(self.parent.browse_workshop_directory)
        workshopLayout.addWidget(self.parent.workshopPathEdit)
        workshopLayout.addWidget(workshopBrowseButton)
        layout.addLayout(workshopLayout)

        # 主内容区域
        mainContent = QHBoxLayout()

        # 缩略图区域
        thumbArea = QScrollArea()
        thumbArea.setWidgetResizable(True)
        thumbContainer = QWidget()
        self.parent.thumbnailLayout = QGridLayout(thumbContainer)
        thumbArea.setWidget(thumbContainer)

        # 右侧预览区
        rightPanel = QWidget()
        rightPanel.setFixedWidth(300)
        rightLayout = QVBoxLayout(rightPanel)
        
        # 添加预览窗口
        self.parent.previewLabel = QLabel("[就绪]")
        self.parent.previewLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parent.previewLabel.setFixedSize(280, 280)
        self.parent.previewLabel.setStyleSheet("border: 2px solid #555;")
        rightLayout.addWidget(self.parent.previewLabel)

        # 添加信息标签
        self.parent.titleLabel = QLabel("[选取一个壁纸来查看]")
        self.parent.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rightLayout.addWidget(self.parent.titleLabel)

        self.parent.pathLabel = QLabel("[选取一个壁纸来查看]")
        self.parent.pathLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rightLayout.addWidget(self.parent.pathLabel)

        # 添加分页控件
        pageLayout = QHBoxLayout()
        self.parent.prevBtn = QPushButton("上一页")
        self.parent.prevBtn.clicked.connect(self.parent.go_to_previous_page)
        self.parent.nextBtn = QPushButton("下一页")
        self.parent.nextBtn.clicked.connect(self.parent.go_to_next_page)
        
        pageLayout.addWidget(self.parent.prevBtn)
        pageLayout.addWidget(self.parent.nextBtn)
        rightLayout.addLayout(pageLayout)

        # 添加按钮组
        extractAndOrganizeBtn = QPushButton("提取并整理")
        extractAndOrganizeBtn.clicked.connect(self.parent.extract_and_organize_files)
        rightLayout.addWidget(extractAndOrganizeBtn)

        extractAllBtn = QPushButton("全部提取")
        extractAllBtn.clicked.connect(lambda: self.parent.extract_action(self.parent.currentImagePath))
        rightLayout.addWidget(extractAllBtn)

        openDirBtn = QPushButton("打开目录")
        openDirBtn.clicked.connect(self.parent.open_current_directory)
        rightLayout.addWidget(openDirBtn)

        rightLayout.addStretch(1)

        mainContent.addWidget(thumbArea, 7)
        mainContent.addWidget(rightPanel, 2)
        layout.addLayout(mainContent)
        return tab

    def create_manual_tab(self):
        """创建手动提取标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 单个提取卡片
        singleCard = QFrame()
        singleCard.setFrameStyle(QFrame.Shape.Box)
        singleLayout = QVBoxLayout(singleCard)
        singleLayout.addWidget(QLabel("单个提取"))
        self.parent.manualPathEdit = QLineEdit()
        self.parent.manualPathEdit.setPlaceholderText("拖拽文件或点击浏览")
        self.parent.manualPathEdit.setAcceptDrops(True)
        self.parent.manualPathEdit.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasUrls() else e.ignore()
        self.parent.manualPathEdit.dropEvent = self.parent.handle_manual_drop
        browseSingle = QPushButton("浏览")
        browseSingle.clicked.connect(self.parent.browse_manual_file)
        btnLayout = QHBoxLayout()
        btnLayout.addWidget(self.parent.manualPathEdit)
        btnLayout.addWidget(browseSingle)
        singleLayout.addLayout(btnLayout)
        extractSingle = QPushButton("提取")
        extractSingle.clicked.connect(lambda: self.parent.extract_single_file(self.parent.manualPathEdit.text()))
        singleLayout.addWidget(extractSingle)

        # 批量提取卡片
        batchCard = QFrame()
        batchCard.setFrameStyle(QFrame.Shape.Box)
        batchLayout = QVBoxLayout(batchCard)
        batchLayout.addWidget(QLabel("批量提取"))
        self.parent.batchPathEdit = QLineEdit()
        self.parent.batchPathEdit.setPlaceholderText("拖拽文件夹或点击浏览")
        self.parent.batchPathEdit.setAcceptDrops(True)
        self.parent.batchPathEdit.dragEnterEvent = lambda e: e.accept() if e.mimeData().hasUrls() else e.ignore()
        self.parent.batchPathEdit.dropEvent = self.parent.handle_batch_drop
        browseBatch = QPushButton("浏览")
        browseBatch.clicked.connect(self.parent.browse_manual_directory)
        bLayout = QHBoxLayout()
        bLayout.addWidget(self.parent.batchPathEdit)
        bLayout.addWidget(browseBatch)
        batchLayout.addLayout(bLayout)
        batchBtn = QPushButton("开始批量提取")
        batchBtn.clicked.connect(self.parent.batch_extract)
        batchLayout.addWidget(batchBtn)

        layout.addWidget(singleCard)
        layout.addWidget(batchCard)
        layout.addStretch()
        return tab

    def create_settings_tab(self):
        """创建设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加自定义设置组
        settingsGroup = QFrame()
        settingsGroup.setFrameStyle(QFrame.Shape.Box)
        settingsLayout = QVBoxLayout(settingsGroup)
        
        # 添加自定义标题
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(QLabel("自定义标题:"))
        self.parent.customTitleEdit = QLineEdit()
        self.parent.customTitleEdit.setPlaceholderText("输入自定义标题")
        titleLayout.addWidget(self.parent.customTitleEdit)
        applyTitleBtn = QPushButton("应用标题")
        applyTitleBtn.clicked.connect(self.parent.apply_custom_title)
        titleLayout.addWidget(applyTitleBtn)
        settingsLayout.addLayout(titleLayout)
        
        # 添加自定义背景颜色
        colorLayout = QHBoxLayout()
        colorLayout.addWidget(QLabel("背景颜色:"))
        self.parent.colorButton = QPushButton("选择颜色")
        self.parent.colorButton.clicked.connect(self.parent.choose_background_color)
        colorLayout.addWidget(self.parent.colorButton)
        settingsLayout.addLayout(colorLayout)
        
        # 添加版本检查组
        versionGroup = QFrame()
        versionGroup.setFrameStyle(QFrame.Shape.Box)
        versionLayout = QVBoxLayout(versionGroup)
        
        # 添加检查更新按钮
        update_check_layout = QHBoxLayout()
        update_check_layout.addWidget(QLabel("RePKG版本检查"))
        self.parent.versionLabel = QLabel("未检查")
        self.parent.versionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.parent.versionLabel.setStyleSheet("color: gray;")
        checkUpdateBtn = QPushButton("检查远端版本")
        checkUpdateBtn.clicked.connect(self.parent.check_update)
        update_check_layout.addWidget(self.parent.versionLabel)
        update_check_layout.addWidget(checkUpdateBtn)
        versionLayout.addLayout(update_check_layout)
        
        # 添加GitHub按钮
        github_layout = QHBoxLayout()
        github_btn = QPushButton("访问GitHub下载地址")
        github_btn.clicked.connect(self.parent.version_checker.open_github)
        github_layout.addWidget(github_btn)
        versionLayout.addLayout(github_layout)
        
        settingsLayout.addWidget(versionGroup)
        layout.addWidget(settingsGroup)
        layout.addStretch()
        return tab

    def create_about_tab(self):
        """创建关于标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 添加关于信息
        about_group = QFrame()
        about_group.setFrameStyle(QFrame.Shape.Box)
        about_layout = QVBoxLayout(about_group)
        
        # 添加版本信息
        version_label = QLabel("版本: 0.0.1")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(version_label)
        
        # 添加作者信息
        author_label = QLabel("作者: KawakazeNotFound/Ryosume")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(author_label)
        
        # 添加GitHub按钮
        github_btn = QPushButton("访问GitHub项目页面")
        github_btn.clicked.connect(self.parent.version_checker.open_my_github)
        about_layout.addWidget(github_btn)
        
        layout.addWidget(about_group)
        layout.addStretch()
        return tab
        layout.addWidget(about_group)
        layout.addStretch()
        return tab
