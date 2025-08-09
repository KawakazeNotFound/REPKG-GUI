"""
配置管理模块
处理配置文件的读取、保存和管理
"""

import os
import json
try:
    import winreg  # type: ignore
except ImportError:  # pragma: no cover
    winreg = None  # type: ignore


class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_path = self.get_config_path()

    def get_config_path(self):
        """获取配置文件路径"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
        return {"save_path": os.path.dirname(os.path.abspath(__file__))}

    def save_config(self, config_data):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get_steam_install_path(self):
        """通过注册表获取Steam安装路径"""
        if winreg:
            try:
                # 打开Steam的注册表项
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
                    # 读取InstallPath值
                    install_path = winreg.QueryValueEx(key, "InstallPath")[0]
                    return install_path
            except OSError:
                # 注册表未找到或无法访问，继续尝试默认路径
                pass

        # 如果在注册表中找不到，尝试从默认路径查找
        default_paths = [
            r"C:\\Program Files (x86)\\Steam",
            r"C:\\Program Files\\Steam",
            r"D:\\Program Files (x86)\\Steam",
            r"D:\\Program Files\\Steam"
        ]
        for path in default_paths:
            if os.path.exists(os.path.join(path, "steam.exe")):
                return path
        return None

