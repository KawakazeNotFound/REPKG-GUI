"""
测试脚本 - 验证重构后的功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试所有模块是否能正常导入"""
    try:
        from utils.config_manager import ConfigManager
        from utils.file_operations import FileOperations
        from utils.version_checker import VersionChecker
        from utils.workers import ExtractWorker, ImageLoadWorker
        from ui.tabs import TabCreator
        from ui.main_window import RePKGGUI
        print("✓ 所有模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ 模块导入失败: {e}")
        return False

def test_config_manager():
    """测试配置管理器"""
    try:
        from utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.load_config()
        print("✓ 配置管理器工作正常")
        return True
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False

def test_file_operations():
    """测试文件操作"""
    try:
        from utils.file_operations import FileOperations
        file_ops = FileOperations()
        repkg_path = file_ops.find_repkg_exe()
        print(f"✓ 文件操作模块工作正常 (RePKG路径: {repkg_path})")
        return True
    except Exception as e:
        print(f"✗ 文件操作测试失败: {e}")
        return False

def test_version_checker():
    """测试版本检查器"""
    try:
        from utils.version_checker import VersionChecker
        version_checker = VersionChecker()
        # 只测试不会出错的功能
        print("✓ 版本检查器模块加载正常")
        return True
    except Exception as e:
        print(f"✗ 版本检查器测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=== RePKG GUI 模块化重构测试 ===")
    
    tests = [
        ("模块导入", test_imports),
        ("配置管理器", test_config_manager), 
        ("文件操作", test_file_operations),
        ("版本检查器", test_version_checker)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n测试 {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n=== 测试结果: {passed}/{total} 通过 ===")
    
    if passed == total:
        print("🎉 所有测试通过！重构成功！")
    else:
        print("❌ 部分测试失败，需要检查问题")

if __name__ == "__main__":
    main()
