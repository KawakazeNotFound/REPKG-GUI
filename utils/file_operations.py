"""
文件操作模块
处理文件和目录的各种操作
"""

import os
import sys
import json
import glob
import shutil
import re
import subprocess


class FileOperations:
    """文件操作工具类"""
    
    @staticmethod
    def find_repkg_exe():
        """查找RePKG.exe的位置"""
        # 首先在程序所在目录查找
        if getattr(sys, 'frozen', False):
            # 如果是打包后的程序
            exe_dir = sys._MEIPASS
        else:
            exe_dir = os.path.dirname(os.path.abspath(__file__))
        
        repkg_path = os.path.join(exe_dir, '..', 'RePKG.exe')
        if os.path.exists(repkg_path):
            return repkg_path
        
        # 如果没找到，返回None
        return None
    
    @staticmethod
    def get_extract_command(file_path, save_directory, repkg_path):
        """获取提取命令"""
        if file_path.endswith('.pkg'):
            if not repkg_path:
                return None
            return [repkg_path, "extract", file_path, "-o", save_directory]
        elif file_path.endswith('.mp4') or file_path.endswith(('.jpg', '.jpeg', '.png')):
            return None
        return None
    
    @staticmethod
    def organize_extracted_files(save_dir):
        """整理提取后的文件"""
        if not save_dir:
            return
            
        # 遍历保存目录下的所有文件夹
        for item in os.listdir(save_dir):
            item_path = os.path.join(save_dir, item)
            if not os.path.isdir(item_path):
                continue
                
            materials_dir = os.path.join(item_path, "materials")
            if not os.path.exists(materials_dir):
                continue
                
            # 获取materials文件夹中的所有图片文件
            for root, _, files in os.walk(materials_dir):
                for file in files:
                    src_path = os.path.join(root, file)
                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        dst_path = os.path.join(item_path, file)
                        base_name, ext = os.path.splitext(dst_path)
                        counter = 1
                        while os.path.exists(dst_path):
                            dst_path = f"{base_name}_{counter}{ext}"
                            counter += 1
                        try:
                            shutil.copy2(src_path, dst_path)
                        except Exception as e:
                            print(f"复制文件失败: {e}")
            
            # 删除materials文件夹和非图片文件
            try:
                shutil.rmtree(materials_dir)
                for file in os.listdir(item_path):
                    file_path = os.path.join(item_path, file)
                    if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
            except Exception as e:
                print(f"清理文件失败: {e}")
    
    @staticmethod
    def get_title_from_project_json(parent_path):
        """从project.json获取标题"""
        pj = os.path.join(parent_path, "project.json")
        title = "Untitled"
        if os.path.exists(pj):
            try:
                with open(pj, 'r', encoding='utf-8') as f:
                    title = json.load(f).get("title", "Untitled")
                    title = re.sub(r'[<>:"/\\|?*]', '', title) or "Untitled"
            except:
                pass
        return title
    
    @staticmethod
    def find_target_file(parent_path):
        """按优先级查找目标文件：scene.pkg -> mp4 -> 图片文件"""
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
        
        return target
    
    @staticmethod
    def copy_file_to_directory(source_file, target_directory):
        """复制文件到目录"""
        try:
            filename = os.path.basename(source_file)
            target_path = os.path.join(target_directory, filename)
            shutil.copy2(source_file, target_path)
            return True
        except Exception as e:
            print(f"复制失败: {e}")
            return False
