"""
RePKG GUI 重构版 - 主程序入口
- 配置/工具函数 -> 事件处理 -> 提取逻辑 -> UI 构建 -> 主程序
- 缩略图预览、提取命令生成、配置管理
- 模块化重构，功能分离
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import RePKGGUI


def main():
    """主程序入口"""
    app = QApplication(sys.argv)
    gui = RePKGGUI()
    gui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
