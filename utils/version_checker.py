"""
版本检查模块
处理RePKG版本检查和比较
"""

import subprocess
import webbrowser


class VersionChecker:
    """版本检查器"""
    
    @staticmethod
    def check_repkg_version(repkg_path):
        """检查RePKG版本"""
        try:
            # 获取本地RePKG版本
            if not repkg_path:
                return "未安装"
                
            result = subprocess.run([repkg_path, "--version"], 
                                capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                local_version = result.stdout.strip()
                return local_version
        except Exception as e:
            print(f"检查RePKG版本失败: {e}")
        return "未安装"

    @staticmethod
    def get_latest_repkg_version():
        """获取最新RePKG版本"""
        try:
            import requests
            response = requests.get("https://api.github.com/repos/notscuffed/repkg/releases/latest", timeout=10)
            if response.status_code == 200:
                return response.json()["tag_name"]
        except Exception as e:
            print(f"获取最新RePKG版本失败: {e}")
        return None
    
    @staticmethod
    def compare_versions(local_version, latest_version):
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

    @staticmethod
    def open_github():
        """打开GitHub页面"""
        webbrowser.open('https://github.com/notscuffed/repkg/releases')

    @staticmethod
    def open_my_github():
        """打开我的GitHub页面"""
        webbrowser.open('https://github.com/KawakazeNotFound/REPKG-GUI')
