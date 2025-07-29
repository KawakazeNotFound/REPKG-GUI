# RePKG GUI 重构版

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

一个用于提取和预览 Steam 创意工坊壁纸的图形界面工具，支持批量处理 PKG 文件。

## ✨ 功能特性

- **直观的 GUI 界面** - 采用 PyQt6 构建的用户友好界面
- **智能预览** - 自动加载壁纸缩略图（支持 JPG/GIF）
- **批量处理** - 支持单个文件和批量提取操作
- **版本检查** - 自动检测 RePKG 工具版本并提示更新
- **平台支持** - 兼容 Windows

## 📦 安装指南

### 前置要求
- Python 3.10+
- RePKG 工具（可选，用于 PKG 文件提取）

### 安装步骤
1. 克隆仓库：
   ```bash
   git clone https://github.com/KawakazeNotFound/REPKG-GUI.git
   cd REPKG-GUI
   ```

2. 创建虚拟环境（推荐）：
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # Windows
   ```

3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 使用说明

1. 运行程序：
   ```bash
   python main.py
   ```

2. 主界面功能区域：
   - **已安装**：浏览已下载的创意工坊壁纸
   - **手动提取**：处理单个文件或批量提取
   - **设置**：配置保存路径和版本检查

3. 基本操作：
   - 点击缩略图查看大图预览
   - 使用"提取"按钮导出壁纸资源
   - 通过"打开目录"快速访问文件位置


## 直接使用Release

1. 直接下载Release即可

## 🛠 构建发布

使用 Nuitka 构建独立可执行文件：

```bash
python -m nuitka \
  --standalone \
  --onefile \
  --enable-plugin=pyqt6 \
  --output-dir=dist \
  main.py
```

## 🤝 贡献指南

欢迎提交 Issue 或 Pull Request！请确保：
1. 代码符合 PEP 8 规范
2. 新功能附带测试用例
3. 更新相关文档

## 📄 许可证

？？？？

---

> 提示：首次运行时程序会自动检测 Steam 安装路径，如需手动指定，请在设置中修改创意工坊目录。

![界面截图](screenshot.png) <!-- 如果有截图可以放在这里 -->
